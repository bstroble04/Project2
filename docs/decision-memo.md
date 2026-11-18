# FIN 43900 Project 2 — Investment Committee Decision Memo

**AI-use disclosure:** ChatGPT and Codex assisted with code development,
debugging, organization, and documentation. The analysis and investment decision
are my own.

**Educational-use disclosure:** This is educational analysis, not investment
advice, an offer, or a recommendation to buy or sell securities.

**Client:** Fictional $50 million university scholarship endowment  
**Decision status:** Modeled candidate only; implementation is **not authorized**.

## 1. Executive recommendation

Retain the 60-month, 10-bps constrained allocation as a conditional modeled candidate for further review, but defer implementation. It clears the model's numerical return and reserve hurdles, while required mandate evidence remains unverified and the DGS10 governance gate requires committee review. This does not authorize a pilot or allocation.

Historical estimates are not forecasts or guarantees. See [README.md](../README.md).

## 2. Investment mandate and constraints

| Requirement | Standard |
| --- | --- |
| Assets and horizon | $50 million; 10 years; $2 million annual scholarship need |
| Annual return objective | 6% net of costs, over rolling five-year periods |
| Reserve | At least 4% in BIL |
| Liquidity | At least 85% redeemable within five business days |
| Issuer exposure | No more than 10% in a single company issuer |
| Restrictions | No borrowing, shorting, or derivatives |
| Rebalancing | Annual; 25% turnover threshold |

The original Project 2 scholarship-endowment mandate is documented in the Project 2 section of [lab13.md](../lab13.md); the historical baseline is documented in [lab15-notes.md](../lab15-notes.md). The mandate did not explicitly supply a benchmark or formal risk measure. Annualized volatility and minimum-volatility selection are transparent modeling choices, not mandate-specified requirements. The unrelated Meridian training mandate and its 60/40 benchmark are not used for this Project 2 decision. The engine returns `UNVERIFIED`, rather than a pass, when required evidence has not been supplied.

## 3. ETF universe and portfolio construction methodology

The model universe is BIL, IEF, AGG, VTI, and VXUS. The committed [prices.csv](../prices.csv) file contains 61 monthly adjusted price observations from September 2021 through September 2026, producing 60 monthly returns.

[project2_engine.py](../project2_engine.py) calculates annualized arithmetic return estimates, annualized volatility, correlations, reserve allocation, and worst monthly return. It searches a long-only 5% grid for the lowest modeled volatility portfolio that clears the selected return hurdle, BIL reserve, and planning ETF cap. It does not forecast returns or establish investability.

Planning implementation costs are separate from published fund expense ratios. Adjusted historical ETF prices generally already reflect fund operating expenses, so those ratios are not deducted again. See [project2_data_lineage.md](../project2_data_lineage.md) and [project2_fund_evidence.py](../project2_fund_evidence.py).

## 4. Comparison of equal-weight, inverse-volatility, and constrained portfolios

| Portfolio | Construction | Committee interpretation |
| --- | --- | --- |
| Equal weight | 20% in each ETF | Diversification baseline; it does not clear the modeled 6% net objective under the default 10-bps scenario. |
| Inverse volatility | Weights proportional to inverse historical volatility | Lower-risk historical baseline; it does not clear the modeled 6% net objective under the default 10-bps scenario. |
| Constrained 5% grid | Lowest modeled volatility subject to long-only, return, reserve, and planning-cap constraints | Selected modeled allocation because it clears the numerical net-return hurdle and reserve requirement. |

All three are calculated from the same data source and shown with the same mandate-evidence gates in [project2_app.py](../project2_app.py). Selection by the model is not proof of liquidity, issuer diversification, suitability, or implementation approval.

## 5. Recommended modeled allocation and expected return/risk

The base scenario uses all 60 monthly returns, a 6% net target, a 4% BIL reserve, no return-estimate adjustment, and a 10-bps planning implementation cost.

| ETF | Modeled weight |
| --- | ---: |
| BIL | 70% |
| IEF | 0% |
| AGG | 0% |
| VTI | 20% |
| VXUS | 10% |
| **Total** | **100%** |

| Metric | Modeled result |
| --- | ---: |
| Gross expected return | Approximately 6.15% |
| Planning implementation cost | 10 bps |
| Net expected return | Approximately 6.05% |
| Annualized volatility | Approximately 4.58% |
| BIL reserve allocation | 70% |

The numerical model passes the 6% net objective and 4% reserve under these inputs. It does not resolve the evidence gates in Section 8.

## 6. Stress tests and completed 10-to-20-bps implementation-cost sensitivity test

[validation-and-ai-use.md](validation-and-ai-use.md) documents reproduction of the 60-month/0-bps and 60-month/10-bps cases, the 36-month stability case, the 7% target case, an infeasible 50% target, and the completed locked 10-to-20-bps implementation-cost sensitivity test.

| Scenario | BIL | IEF | AGG | VTI | VXUS | Gross return | Net return | Volatility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base: 10-bps planning cost | 70% | 0% | 0% | 20% | 10% | ~6.15% | ~6.05% | ~4.58% |
| Completed sensitivity: 20-bps planning cost | 70% | 0% | 0% | 25% | 5% | ~6.31% | ~6.11% | ~4.70% |

The completed test changed the planning implementation-cost input. The engine selected a higher modeled-return mix that offset the additional cost, raising modeled gross and net return while modestly increasing volatility. This is a historical-model result, not evidence that higher implementation costs improve real-world performance. The 20-bps portfolio retained the same stop conditions.

## 7. Point-in-time DGS10 signal and committee review requirement

[project2_signal.py](../project2_signal.py) requests an ALFRED vintage of DGS10 for the selected decision date and selects the latest nonmissing observation on or before that date. It does not substitute revised current FRED data. The rule is a prospective governance gate, not a backtest or automatic trading rule.

For the documented September 30, 2026 decision/vintage date, the latest known DGS10 observation was September 29, 2026 at 5.26%. At the 5.00% review threshold, the signal is **COMMITTEE REVIEW REQUIRED**. The ALFRED graph export supports date-level availability, not an intraday release timestamp. See [project2_point_in_time_signal.md](../project2_point_in_time_signal.md).

## 8. Mandate verification, missing evidence, and stop conditions

| Item | Status | Basis |
| --- | --- | --- |
| Weights total 100% | PASS | Direct calculation |
| No borrowing or short selling | PASS | Long-only direct ETF weights |
| 4% BIL reserve | PASS | 70% BIL allocation |
| 6% net objective | PASS | ~6.05% modeled net return after 10 bps |
| No direct derivatives | PASS for direct ETF positions only | Direct positions are ETF shares; this does not establish that the underlying ETFs satisfy the mandate's derivatives restriction |
| Fund expense-ratio evidence | PASS as evidence | Ratios are indexed separately and not double-counted |
| Five-day liquidity | UNVERIFIED | No source-backed, portfolio-size five-day liquidation evidence for every active ETF |
| Company issuer cap | UNVERIFIED | No date-available full holdings files and issuer aggregation across active funds |
| Underlying-fund derivatives | UNVERIFIED | No complete dated holdings/prospectus review for every active ETF |
| 25% turnover threshold | UNVERIFIED | No prior approved allocation supplied for the recommended allocation |
| Verified implementation costs | UNVERIFIED | The 10-bps planning assumption has not been independently validated using actual execution-cost, spread, and market-impact evidence |

The app displays **STOP CONDITION TRIGGERED** when required evidence remains unverified. The 20-bps test did not remove those conditions; the DGS10 review requirement also remains active.

## 9. Risks, limitations, and assumptions

- Expected returns, volatility, and correlations are historical estimates, not predictions.
- The long-only 5% grid can omit allocations available under continuous optimization.
- Implementation costs are planning assumptions, distinct from fund expenses, actual spreads, and market impact.
- Exchange volume and bid/ask spread are not treated as proof of five-day liquidity for this endowment.
- Current or later-viewed sponsor holdings are not treated as known on the September 30, 2026 decision date.
- The DGS10 gate is not an interest-rate forecast, duration model, causal claim, or performance backtest.

## 10. Conditions required before authorizing implementation

1. Source-backed evidence that at least 85% of the intended portfolio can be liquidated within five business days at the endowment's dollar size.
2. Date-available full constituent holdings, issuer normalization, aggregation across active funds, and a documented 10% issuer-cap test.
3. A dated prospectus and holdings review of underlying derivatives for active ETFs, followed by a policy decision on permissibility.
4. A prior approved allocation and proposed trade list to measure turnover against the 25% threshold.
5. Verified implementation-cost, spread, and market-impact assumptions.
6. Committee review and written disposition of the DGS10 signal.

## 11. CONDITIONAL ALLOCATION RANGE

The following range is restricted to the four tested 5%-grid combinations below.
IEF and AGG are 0% in every combination, and total weights must equal 100%.
These are not independently selectable ticker bands; no arbitrary combination
within the individual BIL, VTI, and VXUS ranges qualifies.

| BIL | IEF | AGG | VTI | VXUS | Net estimate at 10 bps |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 65% | 0% | 0% | 20% | 15% | 6.38% |
| 65% | 0% | 0% | 25% | 10% | 6.53% |
| 70% | 0% | 0% | 20% | 10% | 6.05% — primary modeled candidate |
| 70% | 0% | 0% | 25% | 5% | 6.21% |

Using the default 60-month historical window and 10-bps planning implementation
cost, each listed combination passed the currently calculable checks. None is
authorized for implementation, pilot, or allocation while required implementation
evidence remains unverified. A 60-month historical return estimate above 6% does
not demonstrate achievement of the 6% net objective over rolling five-year periods.

## 12. MONITORING AND REVERSAL TRIGGERS

- Keep **STOP CONDITION TRIGGERED** until at least 85% five-business-day liquidity, no more than 10% aggregated single-company issuer exposure, underlying-fund derivatives compliance, turnover based on a prior approved allocation, and independently verified implementation costs are documented.
- Proposed one-way turnover greater than 25% requires documented committee approval before rebalancing.
- DGS10 at or above 5.00% requires committee review before rebalance authorization. A missing eligible ALFRED vintage means no rebalance authorization.
- If verified implementation costs exceed the 10-bps planning assumption, rerun the model. Do not proceed if the recalculated net estimate falls below 6%.
- If verified liquidity falls below 85%, issuer exposure exceeds 10%, or underlying derivatives violate policy, stop or reverse implementation pending a compliant replacement.
- At each annual review, compare available realized rolling-five-year net performance with the 6% objective. A shortfall triggers reassessment and committee review.

## 13. Final investment committee decision

**Committee ask: DEFER IMPLEMENTATION. Preserve the 70% BIL / 20% VTI / 10% VXUS allocation as the primary modeled candidate for further review; require the missing evidence and committee approval before any pilot or allocation.**

The primary modeled candidate clears the model's numerical 6% net-return and reserve hurdles at the stated 10-bps planning cost. The completed 20-bps sensitivity test also clears the modeled return hurdle. Neither result is sufficient for implementation approval: liquidity, issuer, underlying-derivative, turnover, and verified-cost evidence remain unresolved, and the DGS10 gate requires committee review. No committee authorization is represented by this memo.

## Project submission readiness

The following items support course-project submission readiness rather than an investment implementation authorization:

- Post-run GitHub verification.
- Cold-run reproducibility evidence.
- Any instructor-required submission artifacts.

## Project evidence reviewed

- [project2_app.py](../project2_app.py)
- [project2_engine.py](../project2_engine.py)
- [project2_signal.py](../project2_signal.py)
- [project2_fund_evidence.py](../project2_fund_evidence.py)
- [project2_data_lineage.md](../project2_data_lineage.md)
- [project2_point_in_time_signal.md](../project2_point_in_time_signal.md)
- [validation-and-ai-use.md](validation-and-ai-use.md)
- [README.md](../README.md)
