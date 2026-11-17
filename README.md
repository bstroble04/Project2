# FIN 43900 Labs 18 & 19 — Investor Skills and Legend Panel

This project combines my Lab 18 Warren Buffett investor skill with my Lab 19 Legend Panel. It uses SEC EDGAR 10-K facts only: Python retrieves and calculates the financial values, while the Buffett, Benjamin Graham, and Michael Burry frameworks interpret the same printed results. It is a learning demonstration, not investment advice, and does not use FAskills software, paid data, stock prices, or price targets.

## Project 2 — Scholarship Endowment Application

`project2_app.py` is a separate Streamlit dashboard for the FIN 43900 Project 2
$50 million scholarship-endowment mandate. It reads the committed `prices.csv`
file for BIL, IEF, AGG, VTI, and VXUS; calculates equal-weight and
inverse-volatility baselines; and searches long-only 5% allocations that meet the
4% BIL reserve and the 6% net target under an explicitly displayed planning-cost
assumption.

With all 60 returns and a 0-bps planning-cost input, the constrained calculation
reproduces the allocation reported in `lab15-notes.md`: 70% BIL, 0% IEF, 0% AGG,
15% VTI, and 15% VXUS. A nonzero planning-cost input can change that allocation,
because the historical gross return must then exceed 6% by the modeled cost.

It never treats missing evidence as a pass: five-day liquidity, ETF look-through
issuer exposure, ETF derivative exposure, turnover, and verified cost evidence
remain **UNVERIFIED** until supporting evidence is added. The dashboard includes
interactive estimation-window, cost, return-estimate, return-target, reserve, and
planning ETF-cap stresses. It also uses a DGS10 ALFRED-vintage committee-review
gate documented in `project2_point_in_time_signal.md`; it is a prospective
date-level rule, not a backtest or automatic-trading rule.

Fund sponsor sources, expense-ratio treatment, point-in-time boundaries, and
reproduction steps are documented in `project2_data_lineage.md`. The app keeps
five-day liquidity, ETF look-through issuer exposure, and underlying derivatives
as **UNVERIFIED** until dated, source-matched evidence is loaded.

Run it from a clean environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run project2_app.py
```

Run all offline tests:

```powershell
python -m unittest discover -s tests -v
```

The existing `app.py` below remains the independent Lab 18/19 SEC Legend Panel.

## Project files

- [Lab 19 report](lab19.md)
- [Streamlit Legend Panel](app.py)
- [SEC EDGAR Python engine](.agents/skills/buffett-investor/scripts/edgar_buffett.py)
- [Warren Buffett skill](.agents/skills/buffett-investor/SKILL.md)
- [Benjamin Graham skill](.agents/skills/benjamin-graham-investor/SKILL.md)
- [Michael Burry skill](.agents/skills/michael-burry-investor/SKILL.md)

## Run in VS Code on Windows

Open this workspace in VS Code, then use its integrated PowerShell terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SEC_USER_AGENT = "Your Name your.email@example.com"
python .\.agents\skills\buffett-investor\scripts\edgar_buffett.py COST
python .\.agents\skills\buffett-investor\scripts\edgar_buffett.py NVDA
streamlit run app.py
```

If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate the environment again.

## SEC EDGAR data rules

- Uses the keyless SEC ticker directory and company-facts endpoints. Every SEC request requires `SEC_USER_AGENT` with a name and email.
- Uses only `10-K` / `FY` facts. Flow measures must cover about 300–380 days; the script keeps the newest five actual fiscal-year-end dates and uses the latest filed fact when a fiscal end is duplicated.
- Values are never estimated. Missing source facts remain `not found`; missing or undefined check inputs produce `not known`.
- The script prints each selected XBRL tag and formula. The reported tags include revenue `RevenueFromContractWithCustomerExcludingAssessedTax`, then `Revenues`; net income `NetIncomeLoss`; operating cash flow `NetCashProvidedByUsedInOperatingActivities`; capital spending `PaymentsToAcquirePropertyPlantAndEquipment`, then `PaymentsToAcquireProductiveAssets`; and equity `StockholdersEquity`.

## Lab 18 — Warren Buffett

Lab 18 created the Buffett skill and the SEC EDGAR financial engine. It calculates ROE as net income divided by year-end equity and owner earnings as operating cash flow minus capital spending.

The three Buffett checks are:

1. ROE >= 15% every year.
2. Owner earnings > 0 every year.
3. Owner earnings grew from the first year to the last year.

## Lab 19 — Legend Panel

Lab 19 added Benjamin Graham and Michael Burry skills and extended the Streamlit app into a Legend Panel. The panel shows eight checks, three deterministic investor verdicts, and three editable memos side by side; each memo is validated so a numerical claim must match a value printed by the current Python report at its displayed precision.

The script also retrieves three additional SEC XBRL facts: total liabilities `Liabilities`, current assets `AssetsCurrent`, and current liabilities `LiabilitiesCurrent`. These support the following screens:

| Investor | Checks |
| --- | --- |
| Buffett | ROE >= 15%; positive owner earnings; owner-earnings growth |
| Graham | Current ratio >= 2.0; positive net income every year; net-income growth |
| Burry | Operating cash flow >= net income every year; latest liabilities <= 2 times equity |

## Validation and examples

- A live SEC EDGAR Costco (COST) run produced the expected checks: Buffett passed 3 of 3, Graham passed 2 of 3 because the latest current ratio was 1.06x, and Burry passed 2 of 2 with liabilities-to-equity of 1.49x. These results are calculated from SEC data rather than hardcoded.
- I temporarily changed Graham's current-ratio cutoff from 2.0 to 1.0. Costco then passed all three Graham checks; after restoring the original 2.0 rule, it returned to 2 of 3 passes.
- I ran NVIDIA (NVDA) for Project 2. Buffett and Graham each passed all of their checks; Burry passed the liabilities-to-equity screen at 0.31x but failed the operating-cash-flow-versus-net-income screen.
- The unsupported-number validator successfully flagged `999.9` as an unsupported memo claim.

## Tests

Run the offline test suite without SEC requests:

```powershell
python -m unittest discover -s tests -v
```

The test suite covers check logic, missing values, latest-filing selection, investor verdicts, and unsupported numeric claims.

## SEC disclaimer

Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice. The SEC does not endorse this application or its analysis. Data may be incomplete, amended, or incorrectly tagged by filers; verify material conclusions against the original filings.
