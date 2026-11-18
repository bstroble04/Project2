# FIN 43900 Project 2 — Validation and AI-Use Record

## 1. Validation objective

The objective is to show that the Project 2 application calculates reproducible
portfolio results from `prices.csv`, responds to changed supported inputs,
quarantines unavailable evidence rather than passing it, and prevents a known
point-in-time data-leakage case. Validation of calculation integrity is not a
claim that the portfolio is suitable or committee-ready.

The code being validated is primarily `project2_engine.py`,
`project2_signal.py`, `project2_fund_evidence.py`, and `project2_app.py`. The
separate Lab 18/19 SEC Legend Panel (`app.py`) remains independent.

## 2. Known-answer portfolio calculations

### Executed evidence

The following offline command was executed in the project environment on
2026-11-17 and completed successfully with **27 tests passed**:

```powershell
python -m unittest discover -s tests -v
```

The Project 2 known-answer tests are in `tests/test_project2_engine.py`.

| Test | Known result verified | Status |
| --- | --- | --- |
| `test_preserves_documented_zero_and_ten_bps_allocations` | 60-month, 0-bps result = 70% BIL / 0% IEF / 0% AGG / 15% VTI / 15% VXUS; 10-bps result = 70% BIL / 0% IEF / 0% AGG / 20% VTI / 10% VXUS | Executed — PASS |
| `test_constrained_output_meets_calculable_constraints` | Constrained portfolio weights total 100%, are long-only, meet the reserve minimum, and meet the modeled net target in the 10-bps scenario | Executed — PASS |
| `test_loads_documented_universe_and_full_period` | `prices.csv` loads BIL, IEF, AGG, VTI, VXUS in order and contains 60 monthly returns | Executed — PASS |

These tests validate model calculations from the committed price snapshot. They
do not validate future investment performance.

## 3. Baseline comparison tests

### Executed evidence

`test_preserves_documented_zero_and_ten_bps_allocations` compares the engine
with the historical allocation reported in `lab15-notes.md`.

| Scenario | Expected constrained allocation | Result |
| --- | --- | --- |
| All 60 monthly returns; 0 bps implementation-cost scenario | 70% BIL / 15% VTI / 15% VXUS | Executed — reproduced |
| All 60 monthly returns; 10 bps implementation-cost scenario | 70% BIL / 20% VTI / 10% VXUS | Executed — reproduced |

The 10-bps amount is a planning implementation-cost scenario. It is separate
from published ETF expense ratios, which are generally already reflected in the
adjusted historical ETF prices. See `project2_data_lineage.md`.

## 4. Stress and sensitivity tests

### Executed evidence

| Test | Change | Expected constrained allocation | Status |
| --- | --- | --- | --- |
| `test_reproduces_36_month_and_partner_target_scenarios` | Estimate from last 36 monthly returns, 0 bps | 90% BIL / 10% VTI | Executed — PASS |
| `test_reproduces_36_month_and_partner_target_scenarios` | Raise target from 6% to 7%, 0 bps | 60% BIL / 30% VTI / 10% VXUS | Executed — PASS |
| `test_return_adjustment_and_planning_cap_change_the_engine_inputs` | Apply -100 bps return-estimate adjustment and 65% planning ETF cap | The engine changes expected-return inputs; any feasible result respects the cap | Executed — PASS |
| `test_infeasible_target_is_disclosed` | Raise net target to 50%, 0 bps | No feasible long-only 5% grid allocation; clear infeasibility reason | Executed — PASS |

The Streamlit controls in `project2_app.py` expose the estimation window, 0/10
bps implementation-cost scenarios, return-estimate adjustment, return target,
reserve, and planning ETF cap. These are sensitivity scenarios, not forecasts.

### Still to perform

The application does not yet include a source-backed market drawdown, spread,
market-impact, or liquidity stress for the $50 million endowment. Such tests
need documented inputs before they can be claimed as performed.

The current `project2_app.py` implementation-cost control offers only **0 bps**
and **10 bps**. A 20-bps changed-input test requires an input-control update
before it can be run through the Streamlit app; no such update is made in this
validation record.

## 5. Point-in-time signal validation

### Executed evidence

| Test | Control | Status |
| --- | --- | --- |
| `test_signal_excludes_future_observations` | A September 30, 2026 decision cannot select an October 1, 2026 observation | Executed — PASS |
| `test_signal_missing_data_is_unverified` | Missing eligible vintage data returns `UNVERIFIED` and `DO NOT AUTHORIZE REBALANCE` | Executed — PASS |

The separately documented live ALFRED check in `project2_point_in_time_signal.md`
uses the September 30, 2026 vintage date and the September 29, 2026 DGS10
observation at 5.26%. At the displayed 5.00% threshold, the proposed governance
rule requires committee review. This is a date-level vintage check, not a
backtest and not an intraday availability claim.

## 6. Data and mandate failure tests

### Executed evidence

| Test | Condition | Status |
| --- | --- | --- |
| `test_missing_cost_evidence_makes_net_target_unverified` | No implementation-cost input | Executed — net objective and constrained optimization are UNVERIFIED / unavailable |
| `test_unverified_evidence_is_not_marked_pass` | Missing liquidity, issuer, and turnover evidence | Executed — all remain UNVERIFIED |
| `test_fund_evidence_keeps_unsupported_rules_unverified_and_calculates_turnover` | Default fund evidence plus supplied prior weights | Executed — liquidity, issuer, and underlying derivatives remain UNVERIFIED; direct ETF-share restriction and expense evidence pass; 5% one-way turnover passes |
| `test_verified_mock_holdings_can_drive_liquidity_and_issuer_failures` | Controlled test fixture: 90% source-backed liquidity, 11% company issuer exposure | Executed — liquidity PASS, issuer cap FAIL, underlying-derivatives check PASS |

The mock-data test proves that the check logic can produce PASS or FAIL when
properly structured evidence is supplied. It does **not** claim that the actual
fund evidence currently meets the liquidity or issuer rules.

## 7. AI-output verification

The application and documentation were developed with AI assistance. The
student remains responsible for reviewing every calculation, source claim,
recommendation, and final submission statement.

### Executed evidence

- Unit tests exercise deterministic portfolio, fund-evidence, turnover,
  infeasibility, and point-in-time logic.
- The 60-month historical result is reproduced from the committed price file.
- The application labels missing fund evidence `UNVERIFIED` rather than treating
  it as a pass.

### Still required from the student

- Review the final application, source documentation, and recommendation without
  relying on an AI statement as evidence of correctness.
- The Locked Changed-Input prediction below has been committed. The changed-input
  test, actual-result record, post-run comparison, and post-run Git commit remain
  pending.
- Preserve the GitHub commit URL/hash and any instructor-required screenshots or
  submission receipt. None are fabricated or recorded here.

## 8. Cold-run reproducibility

### Executed evidence

Python compilation and the offline tests were executed successfully:

```powershell
python -m py_compile project2_engine.py project2_signal.py project2_fund_evidence.py project2_app.py app.py
python -m unittest discover -s tests -v
```

The most recently documented result was compilation exit code 0 and 27 passing
tests.

### Still to perform

A clean-machine or clean-virtual-environment cold run has not been represented
as completed in this record. Complete it without modifying model inputs:

```powershell
py -m venv .venv-project2-cold
.\.venv-project2-cold\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run project2_app.py
```

Record the Python version, package-install result, test output, application
startup result, and any errors before making repairs. Do not call a cold run a
validation pass until these facts have been captured by the student.

## 9. Locked Changed-Input Record

Changed Input: Planning implementation cost

Current Setting: 10 bps

New Setting: 20 bps

### Locked Changed-Input Test Record

| Field | Student entry |
| --- | --- |
| Decision being tested | Whether the portfolio still meets the 6% net return objective after increasing implementation costs |
| Exact input to change | Planning implementation cost |
| Original input | 10 bps |
| Changed input | 20 bps |
| Human-authored AI-off prediction | I predict that increasing the implementation cost from 10 bps to 20 bps will lower the portfolio's net return because more money is being taken out for costs. I think this will make it harder for the portfolio to reach our 6% return goal. The app might also change the portfolio weights to try to make up for the higher cost. Overall, I expect the portfolio to perform a little worse with the higher cost, but I don't think the change will be huge. |
| Predicted numerical effect | Increasing implementation costs from 10 bps to 20 bps adds 0.10 percentage points in annual costs. If the portfolio weights stay the same, its net expected return would decrease from around 6.05% to 5.95%, which is below the 6% objective. However, the app might adjust to make up for the additional costs. |
| Predicted committee decision effect | Since it costs more to set up, the committee might not like this plan as much. If the money we make after costs is less than 6%, they might say no for now and ask us to change things or look at it again. Even if the app finds a new mix that hits our goal, it won't be a done deal until we double-check that it follows all the other rules. |
| Pre-run Git commit hash | f0bebeb2fab7be390b3998422e1c0c0a6920fbd9 |
| Post-run Git commit hash | |
| Actual numerical result | |
| Actual decision effect | |
| Explanation of differences | |

