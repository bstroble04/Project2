"""Reproducible calculations for the FIN 43900 Project 2 endowment.

This module deliberately separates calculations supported by ``prices.csv`` from
mandate items that need separate liquidity, ETF-holdings, cost, or prior-portfolio
evidence. It does not turn missing evidence into a pass.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from project2_fund_evidence import FUND_EVIDENCE, weighted_expense_ratio

from portfolio import (
    build_covariance_matrix,
    equal_weight_weights,
    estimate_historical_inputs,
    inverse_volatility_weights,
    portfolio_return,
    portfolio_volatility,
    reserve_eligible_weight,
)


PROJECT2_TICKERS = ("BIL", "IEF", "AGG", "VTI", "VXUS")
RESERVE_ELIGIBLE = (0,)  # BIL only, per the documented Project 2 policy.
RETURN_OBJECTIVE = 0.06
MINIMUM_RESERVE = 0.04
LIQUIDITY_REQUIREMENT = 0.85
ISSUER_LIMIT = 0.10
GRID_INCREMENT = 0.05


def _monthly_returns(csv_filename: str | Path, use_last_36: bool) -> list[list[float]]:
    """Read monthly returns from the committed adjusted-price file."""
    with open(csv_filename, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    prices = [[float(value) for value in row[1:]] for row in rows[1:]]
    returns = [
        [(current / previous) - 1.0 for current, previous in zip(current_row, previous_row)]
        for previous_row, current_row in zip(prices, prices[1:])
    ]
    return returns[-36:] if use_last_36 else returns


def load_historical_inputs(csv_filename: str | Path, use_last_36: bool = False) -> dict[str, Any]:
    """Load the documented ETF universe and derive historical estimates."""
    tickers, expected_returns, volatilities, correlations = estimate_historical_inputs(
        str(csv_filename), use_last_36=use_last_36
    )
    if tuple(tickers) != PROJECT2_TICKERS:
        raise ValueError(
            "Project 2 requires prices.csv columns BIL, IEF, AGG, VTI, VXUS in that order."
        )
    monthly_returns = _monthly_returns(csv_filename, use_last_36)
    return {
        "tickers": tickers,
        "expected_returns": expected_returns,
        "volatilities": volatilities,
        "correlations": correlations,
        "monthly_returns": monthly_returns,
        "months": len(monthly_returns),
    }


def _find_constrained_weights(
    inputs: dict[str, Any],
    target_return: float,
    minimum_reserve: float,
    maximum_etf_weight: float,
) -> list[float] | None:
    """Find the lowest-volatility feasible allocation on the documented 5% grid."""
    increments = round(1 / GRID_INCREMENT)
    maximum_units = math.floor(maximum_etf_weight * increments + 1e-9)
    covariance = build_covariance_matrix(inputs["volatilities"], inputs["correlations"])
    best_weights: list[float] | None = None
    best_volatility: float | None = None

    def evaluate(prefix: list[int], remaining: int, positions_left: int) -> None:
        nonlocal best_weights, best_volatility
        if positions_left == 1:
            if remaining > maximum_units:
                return
            weights = [unit / increments for unit in prefix + [remaining]]
            if reserve_eligible_weight(weights, RESERVE_ELIGIBLE) + 1e-12 < minimum_reserve:
                return
            if portfolio_return(weights, inputs["expected_returns"]) + 1e-12 < target_return:
                return
            volatility = portfolio_volatility(weights, covariance)
            if best_volatility is None or volatility < best_volatility:
                best_weights, best_volatility = weights, volatility
            return
        for unit in range(min(remaining, maximum_units) + 1):
            evaluate(prefix + [unit], remaining - unit, positions_left - 1)

    evaluate([], increments, len(inputs["tickers"]))
    return best_weights


def fund_compliance_checks(
    weights: list[float],
    prior_weights: list[float] | None = None,
) -> list[dict[str, str]]:
    """Check sourced fund evidence without inferring unsupported compliance."""
    active = [(ticker, weight) for ticker, weight in zip(PROJECT2_TICKERS, weights) if weight > 1e-12]
    records = [FUND_EVIDENCE[ticker] for ticker, _ in active]

    liquidity_data_available = all(
        record.get("liquidity_status") == "VERIFIED" and record.get("five_day_liquid_share") is not None
        for record in records
    )
    if liquidity_data_available:
        liquid_share = sum(weight * FUND_EVIDENCE[ticker]["five_day_liquid_share"] for ticker, weight in active)
        liquidity_check = {
            "Rule": "At least 85% redeemable within five business days",
            "Status": "PASS" if liquid_share + 1e-12 >= LIQUIDITY_REQUIREMENT else "FAIL",
            "Reason": f"Source-backed five-day liquid share: {liquid_share:.2%}.",
        }
    else:
        liquidity_check = {
            "Rule": "At least 85% redeemable within five business days",
            "Status": "UNVERIFIED",
            "Reason": "No source-backed, portfolio-size five-day liquidation evidence is loaded for every active ETF.",
        }

    issuer_data_available = all(
        record.get("issuer_status") == "VERIFIED" and record.get("issuer_weights") is not None
        for record in records
    )
    if issuer_data_available:
        issuer_exposure: dict[str, float] = {}
        for ticker, fund_weight in active:
            for issuer, issuer_weight in FUND_EVIDENCE[ticker]["issuer_weights"].items():
                issuer_exposure[issuer] = issuer_exposure.get(issuer, 0.0) + fund_weight * issuer_weight
        largest_issuer = max(issuer_exposure.values(), default=0.0)
        issuer_check = {
            "Rule": "No more than 10% in a single company issuer",
            "Status": "PASS" if largest_issuer <= ISSUER_LIMIT + 1e-12 else "FAIL",
            "Reason": f"Largest aggregated company issuer exposure: {largest_issuer:.2%}.",
        }
    else:
        issuer_check = {
            "Rule": "No more than 10% in a single company issuer",
            "Status": "UNVERIFIED",
            "Reason": "No date-available full ETF holdings files and issuer aggregation are loaded for every active ETF.",
        }

    derivative_statuses = [record.get("underlying_derivatives_status") for record in records]
    if any(status == "HELD" for status in derivative_statuses):
        derivative_check = {
            "Rule": "No derivatives",
            "Status": "FAIL",
            "Reason": "Source-backed evidence identifies underlying derivatives in an active ETF.",
        }
    elif records and all(status == "NONE_VERIFIED" for status in derivative_statuses):
        derivative_check = {
            "Rule": "No derivatives",
            "Status": "PASS",
            "Reason": "Source-backed evidence verifies no underlying derivatives in every active ETF.",
        }
    else:
        derivative_check = {
            "Rule": "No derivatives",
            "Status": "UNVERIFIED",
            "Reason": "Direct ETF-share positions are not derivatives, but underlying-fund derivative exposure is not fully source-verified.",
        }

    expense_ratio = weighted_expense_ratio(weights, PROJECT2_TICKERS)
    expense_check = {
        "Rule": "Fund expense-ratio evidence",
        "Status": "PASS" if expense_ratio is not None else "UNVERIFIED",
        "Reason": (
            f"Weighted published fund expense ratio: {expense_ratio:.3%}. Historical adjusted-price returns already reflect fund expenses; "
            "this rate is disclosed separately and is not subtracted again from those returns."
            if expense_ratio is not None else "At least one active ETF has no indexed sponsor expense ratio."
        ),
    }

    if prior_weights is None:
        turnover_check = {
            "Rule": "Annual rebalancing / 25% turnover threshold",
            "Status": "UNVERIFIED",
            "Reason": "No prior approved allocation was provided, so one-way turnover cannot be calculated.",
        }
    elif len(prior_weights) != len(weights) or any(weight < 0 for weight in prior_weights) or not math.isclose(sum(prior_weights), 1.0, abs_tol=1e-9):
        turnover_check = {
            "Rule": "Annual rebalancing / 25% turnover threshold",
            "Status": "FAIL",
            "Reason": "The supplied prior allocation must have five nonnegative weights totaling 100%.",
        }
    else:
        turnover = sum(abs(current - prior) for current, prior in zip(weights, prior_weights)) / 2
        turnover_check = {
            "Rule": "Annual rebalancing / 25% turnover threshold",
            "Status": "PASS" if turnover <= 0.25 + 1e-12 else "FAIL",
            "Reason": f"One-way turnover from the supplied prior allocation: {turnover:.2%}.",
        }

    return [
        {"Rule": "No direct derivatives", "Status": "PASS", "Reason": "The modeled positions are direct long ETF-share weights, not futures, options, swaps, or short positions."},
        liquidity_check,
        issuer_check,
        derivative_check,
        expense_check,
        turnover_check,
    ]


def mandate_checks(
    weights: list[float],
    expected_return: float,
    annual_cost_bps: float | None,
    target_return: float = RETURN_OBJECTIVE,
    minimum_reserve: float = MINIMUM_RESERVE,
    maximum_etf_weight: float = 1.0,
    prior_weights: list[float] | None = None,
) -> list[dict[str, str]]:
    """Evaluate only what supplied data can substantiate; disclose the rest."""
    total = sum(weights)
    reserve = reserve_eligible_weight(weights, RESERVE_ELIGIBLE)
    lowest_weight = min(weights)
    checks: list[dict[str, str]] = [
        {"Rule": "Weights total 100%", "Status": "PASS" if math.isclose(total, 1.0, abs_tol=1e-9) else "FAIL", "Reason": f"Calculated total: {total:.2%}."},
        {"Rule": "No borrowing or short selling", "Status": "PASS" if lowest_weight >= -1e-9 else "FAIL", "Reason": f"Lowest direct ETF weight: {lowest_weight:.2%}."},
        {"Rule": f"Minimum {minimum_reserve:.0%} reserve (BIL)", "Status": "PASS" if reserve + 1e-9 >= minimum_reserve else "FAIL", "Reason": f"Reserve-eligible allocation: {reserve:.2%}."},
        {"Rule": "Long-only planning ETF cap", "Status": "PASS" if max(weights) <= maximum_etf_weight + 1e-9 else "FAIL", "Reason": f"Largest ETF allocation: {max(weights):.2%}; planning cap: {maximum_etf_weight:.2%}."},
    ]
    if annual_cost_bps is None:
        checks.append({"Rule": f"{target_return:.0%} annual return objective, net of costs", "Status": "UNVERIFIED", "Reason": "No annual cost assumption was supplied, so a net return cannot be calculated."})
    else:
        net_return = expected_return - annual_cost_bps / 10_000
        checks.append({"Rule": f"{target_return:.0%} annual return objective, net of costs", "Status": "PASS" if net_return + 1e-12 >= target_return else "FAIL", "Reason": f"Historical expected return {expected_return:.2%} less {annual_cost_bps:.1f} bps costs = {net_return:.2%}."})
    checks.extend(fund_compliance_checks(weights, prior_weights))
    return checks


def portfolio_summary(
    name: str,
    weights: list[float],
    inputs: dict[str, Any],
    annual_cost_bps: float | None,
    target_return: float = RETURN_OBJECTIVE,
    minimum_reserve: float = MINIMUM_RESERVE,
    maximum_etf_weight: float = 1.0,
    prior_weights: list[float] | None = None,
) -> dict[str, Any]:
    """Calculate portfolio metrics from historical monthly adjusted-price returns."""
    covariance = build_covariance_matrix(inputs["volatilities"], inputs["correlations"])
    expected_return = portfolio_return(weights, inputs["expected_returns"])
    volatility = portfolio_volatility(weights, covariance)
    portfolio_monthly_returns = [sum(weight * asset_return for weight, asset_return in zip(weights, return_row)) for return_row in inputs["monthly_returns"]]
    net_return = None if annual_cost_bps is None else expected_return - annual_cost_bps / 10_000
    return {
        "name": name, "weights": weights, "expected_return": expected_return,
        "net_expected_return": net_return, "volatility": volatility,
        "reserve_weight": reserve_eligible_weight(weights, RESERVE_ELIGIBLE),
        "maximum_weight": max(weights), "worst_month": min(portfolio_monthly_returns),
        "checks": mandate_checks(weights, expected_return, annual_cost_bps, target_return, minimum_reserve, maximum_etf_weight, prior_weights),
    }


def run_project2_analysis(
    csv_filename: str | Path,
    annual_cost_bps: float | None = 10.0,
    use_last_36: bool = False,
    target_return: float = RETURN_OBJECTIVE,
    minimum_reserve: float = MINIMUM_RESERVE,
    expected_return_adjustment_bps: float = 0.0,
    maximum_etf_weight: float = 1.0,
    prior_weights: list[float] | None = None,
) -> dict[str, Any]:
    """Return two baselines and a feasible long-only 5%-grid portfolio.

    ``annual_cost_bps`` is a scenario input, not an asserted fund expense. Passing
    ``None`` intentionally leaves the net-return mandate unverified and prevents a
    constrained net-of-cost recommendation.
    """
    if annual_cost_bps is not None and annual_cost_bps < 0:
        raise ValueError("Annual costs cannot be negative.")
    if not 0 <= target_return <= 1:
        raise ValueError("The return target must be between 0% and 100%.")
    if not 0 <= minimum_reserve <= 1:
        raise ValueError("The reserve minimum must be between 0% and 100%.")
    if not GRID_INCREMENT <= maximum_etf_weight <= 1:
        raise ValueError("The planning ETF cap must be between 5% and 100%.")
    inputs = load_historical_inputs(csv_filename, use_last_36)
    inputs = dict(inputs)
    inputs["expected_returns"] = [
        value + expected_return_adjustment_bps / 10_000 for value in inputs["expected_returns"]
    ]
    equal = equal_weight_weights(len(inputs["tickers"]))
    inverse = inverse_volatility_weights(inputs["volatilities"])
    portfolios = [
        portfolio_summary("Equal weight", equal, inputs, annual_cost_bps, target_return, minimum_reserve, maximum_etf_weight, prior_weights),
        portfolio_summary("Inverse volatility", inverse, inputs, annual_cost_bps, target_return, minimum_reserve, maximum_etf_weight, prior_weights),
    ]
    constrained: dict[str, Any] | None = None
    infeasible_reason: str | None = None
    if annual_cost_bps is None:
        infeasible_reason = "A net-of-cost target cannot be optimized until an annual cost input is supplied."
    else:
        result = _find_constrained_weights(
            inputs,
            target_return + annual_cost_bps / 10_000,
            minimum_reserve,
            maximum_etf_weight,
        )
        if result is None:
            infeasible_reason = f"No long-only 5% grid allocation met the {target_return:.0%} net target after {annual_cost_bps:.1f} bps costs, the {minimum_reserve:.0%} BIL reserve, and the {maximum_etf_weight:.0%} planning ETF cap."
        else:
            constrained = portfolio_summary("Constrained 5% grid", result, inputs, annual_cost_bps, target_return, minimum_reserve, maximum_etf_weight, prior_weights)
            portfolios.append(constrained)
    return {
        "inputs": inputs, "annual_cost_bps": annual_cost_bps, "portfolios": portfolios,
        "constrained": constrained, "infeasible_reason": infeasible_reason,
        "scenario": {
            "target_return": target_return, "minimum_reserve": minimum_reserve,
            "expected_return_adjustment_bps": expected_return_adjustment_bps,
            "maximum_etf_weight": maximum_etf_weight,
        },
    }
