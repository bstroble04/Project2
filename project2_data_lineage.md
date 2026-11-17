# Project 2 Data Sources and Lineage

## Scope and reproducibility boundary

This record distinguishes (1) monthly adjusted ETF prices used to calculate
historical estimates, (2) sponsor documentation used to identify funds and
published expense ratios, and (3) ALFRED vintages used by the DGS10 committee
review gate. It does **not** represent current sponsor pages or later-viewed
holdings as information known on the September 30, 2026 Project 2 decision date.

Repository source-index retrieval date: **2026-11-17**.

## Historical return input

| Field | Value |
| --- | --- |
| File | `prices.csv` |
| Tickers | BIL, IEF, AGG, VTI, VXUS |
| Source | Yahoo Finance through `yfinance`; original run recorded in `lab15-data-sources.md` |
| Download date | 2026-10-22 |
| Observations | 61 month-end adjusted price rows, September 30, 2021 through September 30, 2026 |
| Definition | `auto_adjust=True` close prices; distributions and splits reflected in the adjusted series |
| Transformation | Consecutive monthly simple returns; arithmetic mean × 12 for annual expected return; sample monthly standard deviation × sqrt(12); covariance from monthly correlations and annualized volatility |
| Exclusions | No current price download, intramonth prices, taxes, fund flows, bid/ask costs, market-impact model, or forward return forecast |
| Revision / availability limitation | Yahoo historical data availability and adjustments are not a point-in-time backtest data source. The application does not claim that the price history was known without later corrections on every historical month-end. |
| Licensing limitation | Yahoo Finance and sponsor content are subject to their respective terms. This repository stores a course-use price snapshot and source links, not redistributed sponsor holdings files. |

## Fund-identification and expense evidence

Expense ratios below are sponsor-published figures, retained as separate evidence.
They are not deducted a second time from the historical adjusted-price returns,
which normally already reflect fund operating expenses. The app's 0/10-bps control
is a separate planning estimate for implementation/transaction costs.

| ETF | Sponsor / fund | Official source | Page source date | Published expense ratio | Holdings, liquidity, and derivative limitation |
| --- | --- | --- | --- | ---: | --- |
| BIL | State Street Global Advisors / State Street SPDR Bloomberg 1-3 Month T-Bill ETF | https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil | Fund information Nov. 1, 2026; holdings page observed Oct. 29, 2026 | 0.1352% | Later than Sept. 30 decision date; no source-backed five-day liquidation or complete point-in-time issuer calculation loaded. |
| IEF | BlackRock / iShares 7-10 Year Treasury Bond ETF | https://www.ishares.com/us/products/239456/ishares-7-10-year-treasury-bond-etf-ief | Product page reports Sept. 30, 2026 metrics; retrieved Nov. 17 | 0.15% | Displaying a historical metric after the fact does not establish decision-time availability; trading volume/spread is not a liquidation guarantee. |
| AGG | BlackRock / iShares Core U.S. Aggregate Bond ETF | https://www.ishares.com/us/products/239458/ishares-core-us-aggregate-bond-etf | Product page exposes Sept. 30, 2026 holdings selection; retrieved Nov. 17 | 0.03% | Sponsor holdings page labels a cash/derivatives position and discusses futures collateral; no no-derivatives pass is supportable without a dated full-file review. |
| VTI | Vanguard / Vanguard Total Stock Market ETF | https://advisors.vanguard.com/investments/products/vti/vanguard-total-stock-market-etf | Expense ratio Apr. 28, 2026; holdings page viewed after decision date | 0.03% | No project-ingested point-in-time full holdings file, issuer aggregation, five-day capacity evidence, or derivative analysis. |
| VXUS | Vanguard / Vanguard Total International Stock ETF | https://advisors.vanguard.com/investments/products/vxus/vanguard-total-international-stock-etf | Expense ratio Feb. 27, 2026; holdings page viewed after decision date | 0.05% | No project-ingested point-in-time full holdings file, issuer aggregation, five-day capacity evidence, or derivative analysis. |

### Fund-compliance treatment

- **Direct restriction:** the app can verify that modeled direct positions are
  long ETF-share weights rather than direct futures, options, swaps, borrowing, or
  short positions.
- **Underlying derivatives:** remains UNVERIFIED for every active ETF absent a
  date-matched prospectus/holdings review. The active default allocation does not
  contain AGG, but that does not prove the other active ETFs lack derivatives.
- **Five-day liquidity:** remains UNVERIFIED. Exchange listing, average volume,
  assets under management, and bid/ask spread are not proof that this endowment
  could liquidate at least 85% within five business days under its conditions.
- **Company issuer cap:** remains UNVERIFIED. An ETF's own ticker allocation is
  not a company issuer exposure. Passing requires dated constituent holdings,
  issuer normalization, aggregation across active funds, and a decision-time
  availability record.
- **Turnover:** when a user enters a prior approved allocation, the app calculates
  one-way turnover as `sum(abs(current weight - prior weight)) / 2` and compares it
  to 25%. The input itself is not independently authenticated by the app.

## Point-in-time rate signal

See `project2_point_in_time_signal.md`. The app calls the ALFRED graph endpoint
for DGS10 using the selected decision date as `vintage_date`:

`https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=DGS10&vintage_date=YYYY-MM-DD`

The signal uses the latest nonmissing observation dated on or before that
decision/vintage date. ALFRED establishes a date-level vintage but not an
intraday release timestamp in this graph export; therefore intraday use is
excluded. Current revised FRED values are excluded from the signal.

## Reproduction

```powershell
.\.venv-step6-cold\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run project2_app.py
```

For the existing historical allocation, select all 60 monthly returns, 0 bps
planning implementation cost, 6% target, 4% BIL reserve, no return adjustment,
and a 100% planning ETF cap. This produces 70% BIL, 15% VTI, and 15% VXUS.
Use 10 bps to reproduce the planning-cost allocation of 70% BIL, 20% VTI, and
10% VXUS.
