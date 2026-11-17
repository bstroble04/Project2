import math
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import project2_engine as engine
from project2_signal import evaluate_dgs10_signal


PRICE_FILE = Path(__file__).parents[1] / "prices.csv"


class Project2EngineTests(unittest.TestCase):
    def test_loads_documented_universe_and_full_period(self):
        inputs = engine.load_historical_inputs(PRICE_FILE)
        self.assertEqual(tuple(inputs["tickers"]), engine.PROJECT2_TICKERS)
        self.assertEqual(inputs["months"], 60)

    def test_constrained_output_meets_calculable_constraints(self):
        analysis = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=10.0)
        result = analysis["constrained"]
        self.assertIsNotNone(result)
        self.assertTrue(math.isclose(sum(result["weights"]), 1.0, abs_tol=1e-9))
        self.assertGreaterEqual(result["reserve_weight"], engine.MINIMUM_RESERVE)
        self.assertGreaterEqual(result["net_expected_return"], engine.RETURN_OBJECTIVE)
        self.assertTrue(all(weight >= 0 for weight in result["weights"]))

    def test_unverified_evidence_is_not_marked_pass(self):
        analysis = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=10.0)
        statuses = {item["Rule"]: item["Status"] for item in analysis["portfolios"][0]["checks"]}
        self.assertEqual(statuses["At least 85% redeemable within five business days"], "UNVERIFIED")
        self.assertEqual(statuses["No more than 10% in a single company issuer"], "UNVERIFIED")
        self.assertEqual(statuses["Annual rebalancing / 25% turnover threshold"], "UNVERIFIED")

    def test_missing_cost_evidence_makes_net_target_unverified(self):
        analysis = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=None)
        self.assertIsNone(analysis["constrained"])
        statuses = {item["Rule"]: item["Status"] for item in analysis["portfolios"][0]["checks"]}
        self.assertEqual(statuses["6% annual return objective, net of costs"], "UNVERIFIED")

    def test_preserves_documented_zero_and_ten_bps_allocations(self):
        zero_bps = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=0.0)["constrained"]
        ten_bps = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=10.0)["constrained"]
        self.assertEqual(zero_bps["weights"], [0.70, 0.0, 0.0, 0.15, 0.15])
        self.assertEqual(ten_bps["weights"], [0.70, 0.0, 0.0, 0.20, 0.10])

    def test_reproduces_36_month_and_partner_target_scenarios(self):
        stability = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=0.0, use_last_36=True)["constrained"]
        partner = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=0.0, target_return=0.07)["constrained"]
        self.assertEqual(stability["weights"], [0.90, 0.0, 0.0, 0.10, 0.0])
        self.assertEqual(partner["weights"], [0.60, 0.0, 0.0, 0.30, 0.10])

    def test_infeasible_target_is_disclosed(self):
        result = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=0.0, target_return=0.50)
        self.assertIsNone(result["constrained"])
        self.assertIn("No long-only 5% grid allocation", result["infeasible_reason"])

    def test_return_adjustment_and_planning_cap_change_the_engine_inputs(self):
        base = engine.run_project2_analysis(PRICE_FILE, annual_cost_bps=0.0)
        adjusted = engine.run_project2_analysis(
            PRICE_FILE, annual_cost_bps=0.0, expected_return_adjustment_bps=-100.0,
            maximum_etf_weight=0.65,
        )
        self.assertAlmostEqual(
            adjusted["inputs"]["expected_returns"][0],
            base["inputs"]["expected_returns"][0] - 0.01,
        )
        if adjusted["constrained"] is not None:
            self.assertLessEqual(max(adjusted["constrained"]["weights"]), 0.65)

    def test_signal_excludes_future_observations(self):
        vintage = pd.DataFrame({
            "observation_date": ["2026-09-29", "2026-10-01"],
            "value": [5.26, 4.00],
        })
        signal = evaluate_dgs10_signal(vintage, pd.Timestamp("2026-09-30").date(), 5.00)
        self.assertEqual(signal["observation_date"].isoformat(), "2026-09-29")
        self.assertEqual(signal["value"], 5.26)
        self.assertEqual(signal["decision"], "COMMITTEE REVIEW REQUIRED")

    def test_signal_missing_data_is_unverified(self):
        vintage = pd.DataFrame({"observation_date": ["2026-10-01"], "value": [4.00]})
        signal = evaluate_dgs10_signal(vintage, pd.Timestamp("2026-09-30").date(), 5.00)
        self.assertEqual(signal["status"], "UNVERIFIED")
        self.assertEqual(signal["decision"], "DO NOT AUTHORIZE REBALANCE")

    def test_fund_evidence_keeps_unsupported_rules_unverified_and_calculates_turnover(self):
        checks = engine.fund_compliance_checks(
            [0.70, 0.0, 0.0, 0.20, 0.10],
            prior_weights=[0.70, 0.0, 0.0, 0.15, 0.15],
        )
        statuses = {check["Rule"]: check for check in checks}
        self.assertEqual(statuses["At least 85% redeemable within five business days"]["Status"], "UNVERIFIED")
        self.assertEqual(statuses["No more than 10% in a single company issuer"]["Status"], "UNVERIFIED")
        self.assertEqual(statuses["No direct derivatives"]["Status"], "PASS")
        self.assertEqual(statuses["No derivatives"]["Status"], "UNVERIFIED")
        self.assertEqual(statuses["Fund expense-ratio evidence"]["Status"], "PASS")
        self.assertEqual(statuses["Annual rebalancing / 25% turnover threshold"]["Status"], "PASS")
        self.assertIn("5.00%", statuses["Annual rebalancing / 25% turnover threshold"]["Reason"])

    def test_verified_mock_holdings_can_drive_liquidity_and_issuer_failures(self):
        evidence = deepcopy(engine.FUND_EVIDENCE)
        evidence["BIL"].update({
            "liquidity_status": "VERIFIED",
            "five_day_liquid_share": 0.90,
            "issuer_status": "VERIFIED",
            "issuer_weights": {"Example Company": 0.11},
            "underlying_derivatives_status": "NONE_VERIFIED",
        })
        with patch.dict(engine.FUND_EVIDENCE, evidence, clear=True):
            checks = engine.fund_compliance_checks([1.0, 0.0, 0.0, 0.0, 0.0])
        statuses = {check["Rule"]: check["Status"] for check in checks}
        self.assertEqual(statuses["At least 85% redeemable within five business days"], "PASS")
        self.assertEqual(statuses["No more than 10% in a single company issuer"], "FAIL")
        self.assertEqual(statuses["No derivatives"], "PASS")


if __name__ == "__main__":
    unittest.main()
