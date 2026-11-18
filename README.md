# FIN 43900 Project 2 — Investment Management Application

This repository contains my FIN 43900 Project 2 application for a fictional
**$50 million university scholarship endowment**. The application evaluates
historical ETF-based portfolio allocations against the documented mandate and
clearly separates calculated results from evidence that has not yet been
verified.

**AI-use and educational disclosure:** AI assisted with code development,
debugging, organization, and documentation. I remain responsible for reviewing
the calculations, evidence, policy assumptions, and final investment judgment.
This is a course project for educational purposes, not investment advice, an
offer, or a recommendation to buy or sell securities. Historical estimates are
not forecasts or guarantees.

## Mandate and current committee position

The Project 2 scholarship-endowment mandate and historical baseline are
documented in [lab15-notes.md](lab15-notes.md):

- $50 million endowment; 10-year horizon; $2 million annual scholarship need.
- 6% annual return objective, **net of costs**.
- Minimum 4% reserve allocation in BIL.
- Minimum 85% five-business-day liquidity.
- Maximum 10% exposure to any single company issuer.
- No borrowing, shorting, or derivatives.
- Annual rebalancing and a 25% turnover threshold.

The app models long-only portfolios from BIL, IEF, AGG, VTI, and VXUS. It can
verify weights, direct long-only positions, reserve allocation, modeled net
return, planning ETF cap, and turnover when a prior approved allocation is
entered. It does **not** pass liquidity, ETF look-through company exposure, or
underlying-fund derivative exposure without dated, source-matched evidence.

The current default constrained scenario uses 10 bps of separate planning
implementation costs and produces:

| ETF | Weight |
| --- | ---: |
| BIL | 70% |
| IEF | 0% |
| AGG | 0% |
| VTI | 20% |
| VXUS | 10% |

| Metric | Modeled result |
| --- | ---: |
| Gross expected return | 6.1547% |
| Net expected return | 6.0547% |
| Annualized volatility | 4.5804% |
| BIL reserve | 70.00% |

This is not an adoption recommendation. Required liquidity, issuer,
underlying-derivative, turnover, and verified implementation-cost evidence still
limits the strategy to further review. The default DGS10 point-in-time gate also
requires committee review before authorizing a rebalance.

## Portfolio calculations

[project2_engine.py](project2_engine.py) reads the committed
[prices.csv](prices.csv) file of monthly adjusted ETF prices. It calculates:

- equal-weight and inverse-volatility baselines;
- historical annualized arithmetic return estimates, volatility, correlations,
  reserve allocation, largest ETF allocation, and worst monthly return;
- a long-only 5% grid constrained portfolio;
- net expected return after a separately displayed 0-, 10-, or 20-bps planning
  implementation-cost scenario (10 bps is the default);
- portfolio turnover when a prior allocation is supplied.

The 60-month, 0-bps historical calculation reproduces the allocation reported
in [lab15-notes.md](lab15-notes.md): 70% BIL, 15% VTI, and 15% VXUS. The 10-bps
scenario changes the constrained allocation because gross expected return must
clear the 6% objective after the modeled cost.

Published fund expense ratios are documented separately in
[project2_data_lineage.md](project2_data_lineage.md). They are not subtracted a
second time from adjusted-price returns, which generally already reflect fund
operating expenses. The app's implementation-cost input is therefore separate
from fund expenses and from turnover-related trading costs.

## Point-in-time governance signal

[project2_signal.py](project2_signal.py) uses the ALFRED vintage of DGS10 for a
selected annual rebalance decision date. It selects the latest nonmissing
observation dated on or before that vintage date, never substitutes current
revised FRED data, and quarantines unavailable data as `UNVERIFIED`.

The proposed governance rule is a committee-review gate, not a backtest or an
automatic trade rule:

- DGS10 at or above the user-selected threshold requires committee review before
  a rebalance may be authorized.
- A missing ALFRED vintage results in `DO NOT AUTHORIZE REBALANCE`.
- The ALFRED graph export verifies availability at the date level; it does not
  establish an intraday release timestamp.

The full rule, data card, and limitations are in
[project2_point_in_time_signal.md](project2_point_in_time_signal.md).

## Evidence gates and source lineage

[project2_fund_evidence.py](project2_fund_evidence.py) indexes official sponsor
sources for BIL, IEF, AGG, VTI, and VXUS. The app displays sponsor identity,
official URL, source-date note, published expense ratio, and evidence status.

Current or later-viewed holdings are not treated as information known on
September 30, 2026. Five-day liquidity and company issuer-cap checks remain
`UNVERIFIED` until the project includes dated, availability-verified full
holdings and a portfolio-size liquidity analysis. Direct ETF-share positions are
distinguished from possible underlying-fund derivative exposure.

For sources, definitions, transformations, exclusions, revision/availability
limits, licensing considerations, and reproduction details, see
[project2_data_lineage.md](project2_data_lineage.md).

## Interactive stress testing

[project2_app.py](project2_app.py) provides Streamlit controls for:

- 60-month or 36-month historical estimation windows;
- 0-, 10-, or 20-bps planning implementation costs (10 bps default);
- parallel expected-return estimate changes;
- return target, BIL reserve, and planning ETF-cap scenarios;
- a prior approved allocation for turnover calculation;
- DGS10 decision date and review threshold.

Each scenario recalculates portfolio weights, gross/net return, volatility,
mandate statuses, change versus the 60-month/0-bps base, and committee stop
conditions. It also reproduces the documented 36-month stability and 7% target
scenarios from [lab15-notes.md](lab15-notes.md).

## Windows setup

Open PowerShell in the repository root.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## Launch the Project 2 app

```powershell
streamlit run project2_app.py
```

## Run offline tests

```powershell
python -m unittest discover -s tests -v
```

The suite covers 60-month and 10-bps baseline reproduction, 36-month and 7%
stress cases, infeasible optimization, point-in-time leakage and missing-data
handling, mandate evidence gates, turnover, and issuer-cap logic with controlled
test fixtures. The repository's Project 2 suite contains 12 automated tests.

## Validation and Locked Changed-Input Record

[docs/validation-and-ai-use.md](docs/validation-and-ai-use.md) records executed
validation evidence and contains the required blank Locked Changed-Input Record
template. The student must personally write an AI-off prediction, commit it to
GitHub, record its pre-run hash, and only then run the selected changed-input
test. This repository does not provide that personal prediction or fabricated
Git evidence.
