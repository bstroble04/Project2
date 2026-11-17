# Project 2 Point-in-Time Signal — DGS10 Review Gate

## Purpose and rule

This is a **proposed prospective governance rule**, not a historical trading rule
and not a backtest. On an annual rebalance decision date, the application requests
the ALFRED vintage of DGS10 available on that same date. It takes the latest
nonmissing observation dated on or before the decision date.

- If that rate is at or above the user-selected review threshold (the dashboard
  default is 5.00%), the output is **COMMITTEE REVIEW REQUIRED**. The proposed
  effect is to withhold rebalance authorization until the committee documents why
  the allocation remains appropriate in the higher-rate environment.
- If it is below the threshold, the output is **ELIGIBLE FOR COMMITTEE REVIEW**.
  This is not an automatic trade authorization and does not override any mandate
  check.
- If an ALFRED vintage or usable observation cannot be verified, the output is
  **UNVERIFIED — DO NOT AUTHORIZE REBALANCE**. The app never substitutes current
  revised FRED data.

The rule does not change historical return estimates or assert that a 5.00% rate
threshold would have improved performance. The threshold is a transparent planning
input that requires committee approval before use.

## Data card

| Field | Value |
| --- | --- |
| Series | DGS10 — Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity |
| Source / provider | Board of Governors of the Federal Reserve System; ALFRED / Federal Reserve Bank of St. Louis |
| Units and frequency | Percent; daily; not seasonally adjusted |
| Observation date | The calendar date the reported yield measures |
| Decision / vintage date | The selected annual rebalance date. The app requests the ALFRED vintage available on this date. |
| Availability | Date-level: ALFRED confirms the selected observation appears in that vintage. It does not supply an intraday release timestamp in the graph CSV. |
| Transformation | Select latest nonmissing observation with observation date on or before decision date; compare yield in percent to the user-supplied threshold. No return forecasting transformation. |
| Revisions | ALFRED vintage is used to avoid silently applying today's revised FRED values. Current FRED data is excluded from this signal. |
| Exclusions | No intraday decisions; no rate-duration model; no causal or performance claim; no backtest. |
| Limitations | A DGS10 level alone does not measure ETF liquidity, company issuer exposure, derivatives, turnover, expected returns, or suitability. Exact historical release time remains unverified. |

## Existing evidence

`lab17.md` records that at the September 30, 2026 date-level cutoff, the latest
known DGS10 observation was September 29, 2026 at 5.26%. With the dashboard's
default 5.00% review threshold, that documented vintage triggers **COMMITTEE
REVIEW REQUIRED**. This is an application of the proposed gate to one documented
vintage, not evidence of historical investment performance.
