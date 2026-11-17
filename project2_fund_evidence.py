"""Source-indexed ETF evidence used by the Project 2 compliance display.

This is deliberately a documentation index, not a substitute for archived fund
files. ``as_of_date`` identifies what a sponsor page says about data; it does not
prove that the information was available on the Project 2 historical decision
date. The compliance engine therefore never uses these records to pass liquidity
or look-through issuer checks without separately supplied dated data.
"""

from __future__ import annotations

from typing import Any


RETRIEVAL_DATE = "2026-11-17"

FUND_EVIDENCE: dict[str, dict[str, Any]] = {
    "BIL": {
        "sponsor": "State Street Global Advisors / SPDR",
        "fund_name": "State Street SPDR Bloomberg 1-3 Month T-Bill ETF",
        "official_url": "https://www.ssga.com/us/en/individual/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil",
        "source_date": "2026-11-01 fund information; top holdings page observed 2026-10-29",
        "expense_ratio": 0.001352,
        "expense_date": "2026-11-01",
        "liquidity_status": "UNVERIFIED",
        "liquidity_reason": "Exchange listing and Treasury-bill strategy do not establish the endowment's five-business-day liquidation capacity.",
        "issuer_status": "UNVERIFIED",
        "issuer_reason": "No archived, source-matched holdings file and issuer aggregation were loaded for the September 30 decision date.",
        "underlying_derivatives_status": "UNVERIFIED",
        "underlying_derivatives_reason": "The reviewed product page is not sufficient evidence that the fund held no derivatives on the decision date.",
        "limitations": "The reported expense ratio and holdings page are after September 30, 2026 and are not used as point-in-time holdings evidence.",
    },
    "IEF": {
        "sponsor": "BlackRock / iShares",
        "fund_name": "iShares 7-10 Year Treasury Bond ETF",
        "official_url": "https://www.ishares.com/us/products/239456/ishares-7-10-year-treasury-bond-etf-ief",
        "source_date": "Product page reports September 30, 2026 fund metrics; web retrieval 2026-11-17",
        "expense_ratio": 0.0015,
        "expense_date": "Current prospectus shown on product page",
        "liquidity_status": "UNVERIFIED",
        "liquidity_reason": "Reported exchange volume and bid/ask spread are not a five-day liquidation guarantee.",
        "issuer_status": "UNVERIFIED",
        "issuer_reason": "Treasury holdings information was not captured in an archived, availability-verified September 30 file for this project.",
        "underlying_derivatives_status": "UNVERIFIED",
        "underlying_derivatives_reason": "No dated holdings/prospectus analysis proving the absence of underlying derivatives was loaded.",
        "limitations": "A page can display a September 30 metric after that date; availability at the historical decision time is not established.",
    },
    "AGG": {
        "sponsor": "BlackRock / iShares",
        "fund_name": "iShares Core U.S. Aggregate Bond ETF",
        "official_url": "https://www.ishares.com/us/products/239458/ishares-core-us-aggregate-bond-etf",
        "source_date": "Product page exposes a September 30, 2026 holdings selection; web retrieval 2026-11-17",
        "expense_ratio": 0.0003,
        "expense_date": "Current prospectus shown on product page",
        "liquidity_status": "UNVERIFIED",
        "liquidity_reason": "ETF trading statistics do not document five-day liquidation capacity for a $50m endowment.",
        "issuer_status": "UNVERIFIED",
        "issuer_reason": "The project has not ingested a dated full holdings file and aggregated issuer exposures.",
        "underlying_derivatives_status": "UNVERIFIED",
        "underlying_derivatives_reason": "The sponsor holdings page labels a cash/derivatives position and discusses futures collateral; this prevents a no-derivatives pass without a dated full-file review.",
        "limitations": "The product-page history alone does not establish a September 30 availability timestamp or complete issuer aggregation.",
    },
    "VTI": {
        "sponsor": "The Vanguard Group",
        "fund_name": "Vanguard Total Stock Market ETF",
        "official_url": "https://advisors.vanguard.com/investments/products/vti/vanguard-total-stock-market-etf",
        "source_date": "Expense ratio as of 2026-04-28; holdings page observed after the Project 2 decision date",
        "expense_ratio": 0.0003,
        "expense_date": "2026-04-28",
        "liquidity_status": "UNVERIFIED",
        "liquidity_reason": "Reported bid/ask spread or exchange trading is not evidence of five-day liquidation capacity.",
        "issuer_status": "UNVERIFIED",
        "issuer_reason": "No point-in-time, project-ingested full holdings file with issuer aggregation is available.",
        "underlying_derivatives_status": "UNVERIFIED",
        "underlying_derivatives_reason": "No dated prospectus and holdings analysis establishing underlying derivative exposure was loaded.",
        "limitations": "Current or later-viewed holdings cannot be treated as known on September 30, 2026.",
    },
    "VXUS": {
        "sponsor": "The Vanguard Group",
        "fund_name": "Vanguard Total International Stock ETF",
        "official_url": "https://advisors.vanguard.com/investments/products/vxus/vanguard-total-international-stock-etf",
        "source_date": "Expense ratio as of 2026-02-27; holdings page observed after the Project 2 decision date",
        "expense_ratio": 0.0005,
        "expense_date": "2026-02-27",
        "liquidity_status": "UNVERIFIED",
        "liquidity_reason": "International-market and ETF trading conditions require separate evidence; no five-day liquidation analysis is included.",
        "issuer_status": "UNVERIFIED",
        "issuer_reason": "No point-in-time, project-ingested full holdings file with issuer aggregation is available.",
        "underlying_derivatives_status": "UNVERIFIED",
        "underlying_derivatives_reason": "No dated prospectus and holdings analysis establishing underlying derivative exposure was loaded.",
        "limitations": "Current or later-viewed holdings cannot be treated as known on September 30, 2026.",
    },
}


def weighted_expense_ratio(weights: list[float], tickers: tuple[str, ...]) -> float | None:
    """Return the weighted published expense ratio when all active funds are sourced."""
    active = [(ticker, weight) for ticker, weight in zip(tickers, weights) if weight > 1e-12]
    if any(FUND_EVIDENCE[ticker].get("expense_ratio") is None for ticker, _ in active):
        return None
    return sum(weight * FUND_EVIDENCE[ticker]["expense_ratio"] for ticker, weight in active)
