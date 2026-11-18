"""FIN 43900 Project 2 — scholarship endowment portfolio dashboard."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from project2_engine import GRID_INCREMENT, ISSUER_LIMIT, PROJECT2_TICKERS, run_project2_analysis
from project2_fund_evidence import FUND_EVIDENCE, RETRIEVAL_DATE, weighted_expense_ratio
from project2_signal import live_dgs10_signal


PRICE_FILE = Path(__file__).parent / "prices.csv"


@st.cache_data(ttl=3600, show_spinner=False)
def cached_dgs10_signal(decision_date_text: str, threshold: float) -> dict:
    """Avoid repeated network calls while retaining an explicit ALFRED vintage."""
    return live_dgs10_signal(date.fromisoformat(decision_date_text), threshold)


def check_statuses(portfolio: dict | None) -> dict[str, str]:
    return {} if portfolio is None else {check["Rule"]: check["Status"] for check in portfolio["checks"]}


def stop_conditions(analysis: dict, signal: dict) -> list[str]:
    """State why an allocation cannot proceed to implementation."""
    conditions: list[str] = []
    if analysis["constrained"] is None:
        conditions.append(analysis["infeasible_reason"] or "No feasible constrained allocation exists.")
        return conditions
    statuses = check_statuses(analysis["constrained"])
    failed = [rule for rule, status in statuses.items() if status == "FAIL"]
    unverified = [rule for rule, status in statuses.items() if status == "UNVERIFIED"]
    if failed:
        conditions.append("Deterministic mandate failure: " + "; ".join(failed))
    if unverified:
        conditions.append("Committee-readiness stop — evidence remains unverified: " + "; ".join(unverified))
    if signal["decision"] != "ELIGIBLE FOR COMMITTEE REVIEW":
        conditions.append("Point-in-time gate: " + signal["decision"])
    return conditions


def comparison_rows(analysis: dict) -> list[dict]:
    return [
        {
            "Portfolio": portfolio["name"],
            "Expected return (gross)": portfolio["expected_return"] * 100,
            "Expected return (net)": None if portfolio["net_expected_return"] is None else portfolio["net_expected_return"] * 100,
            "Annualized volatility": portfolio["volatility"] * 100,
            "Reserve allocation": portfolio["reserve_weight"] * 100,
            "Largest ETF weight": portfolio["maximum_weight"] * 100,
            "Worst historical month": portfolio["worst_month"] * 100,
        }
        for portfolio in analysis["portfolios"]
    ]


st.set_page_config(page_title="FIN 43900 Project 2", page_icon="📊", layout="wide")
st.title("FIN 43900 Project 2 — Scholarship Endowment")
st.caption("Historical estimates from committed ETF prices. Learning demonstration, not investment advice.")

with st.sidebar:
    st.header("Interactive stress controls")
    period = st.radio("Historical estimation window", ["All 60 monthly returns", "Last 36 monthly returns"])
    annual_cost_bps = st.select_slider("Planning transaction / implementation costs (bps)", options=[0.0, 10.0, 20.0], value=10.0)
    return_adjustment_bps = st.slider("Parallel expected-return estimate change (bps)", -300, 300, 0, 25)
    target_return = st.slider("Net annual return target (%)", 0.0, 15.0, 6.0, 0.5, format="%.1f%%") / 100
    reserve_minimum = st.slider("Minimum BIL reserve (%)", 0.0, 30.0, 4.0, 1.0, format="%.0f%%") / 100
    maximum_etf_weight = st.slider("Planning maximum ETF weight (%)", 5.0, 100.0, 100.0, 5.0, format="%.0f%%") / 100
    st.caption("The ETF cap and return adjustment are scenario inputs, not additional stated mandate rules.")
    use_prior_allocation = st.checkbox("Enter prior approved allocation for turnover", value=False)
    prior_weights = None
    if use_prior_allocation:
        st.caption("Enter actual prior approved weights; one-way turnover is half the sum of absolute weight changes.")
        prior_weights = [
            st.number_input(f"Prior {ticker} (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key=f"prior_{ticker}") / 100
            for ticker in PROJECT2_TICKERS
        ]
    st.header("DGS10 review gate")
    decision_date = st.date_input("Annual rebalance decision date", value=date(2026, 9, 30), max_value=date.today())
    dgs10_threshold = st.number_input("DGS10 committee-review threshold (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.25)

try:
    analysis = run_project2_analysis(
        PRICE_FILE,
        annual_cost_bps=annual_cost_bps,
        use_last_36=period == "Last 36 monthly returns",
        target_return=target_return,
        minimum_reserve=reserve_minimum,
        expected_return_adjustment_bps=return_adjustment_bps,
        maximum_etf_weight=maximum_etf_weight,
        prior_weights=prior_weights,
    )
    base = run_project2_analysis(PRICE_FILE, annual_cost_bps=0.0)
except ValueError as error:
    st.error(f"Could not calculate Project 2 results: {error}")
    st.stop()

with st.spinner("Verifying the selected ALFRED DGS10 vintage…"):
    signal = cached_dgs10_signal(decision_date.isoformat(), dgs10_threshold)

st.header("Investment Mandate")
mandate_metrics = st.columns(2)
mandate_metrics[0].metric("Endowment assets", "$50.0m")
mandate_metrics[1].metric("Net annual return objective", "6.00%")
st.dataframe(
    pd.DataFrame([
        {"Mandate requirement": "Reserve allocation", "Requirement": "At least 4.00% in BIL"},
        {"Mandate requirement": "Five-day liquidity", "Requirement": "At least 85.00% redeemable within five business days"},
        {"Mandate requirement": "Single-company issuer exposure", "Requirement": f"No more than {ISSUER_LIMIT:.0%}"},
        {"Mandate requirement": "Portfolio restrictions", "Requirement": "No borrowing, shorting, or derivatives; annual rebalancing; 25% turnover threshold"},
    ]),
    hide_index=True,
    width="stretch",
)
st.caption(
    f"Universe: {', '.join(PROJECT2_TICKERS)}. Long-only {GRID_INCREMENT:.0%} grid. "
    "Items without dated, source-matched evidence remain UNVERIFIED."
)

st.header("Portfolio Comparison")
rows = comparison_rows(analysis)
st.dataframe(
    pd.DataFrame(rows), hide_index=True, width="stretch",
    column_config={column: st.column_config.NumberColumn(format="%.2f%%") for column in rows[0] if column != "Portfolio"},
)
if analysis["infeasible_reason"]:
    st.error(analysis["infeasible_reason"])

st.subheader("Change versus the historical 60-month, 0-bps base")
base_portfolio = base["constrained"]
current_portfolio = analysis["constrained"]
if current_portfolio:
    changes = pd.DataFrame({
        "ETF": PROJECT2_TICKERS,
        "Base weight": [weight * 100 for weight in base_portfolio["weights"]],
        "Scenario weight": [weight * 100 for weight in current_portfolio["weights"]],
        "Weight change": [(scenario - baseline) * 100 for scenario, baseline in zip(current_portfolio["weights"], base_portfolio["weights"])],
    })
    st.dataframe(changes, hide_index=True, width="stretch",
                 column_config={column: st.column_config.NumberColumn(format="%.2f%%") for column in changes.columns if column != "ETF"})
    metric_changes = {
        "Gross expected return": current_portfolio["expected_return"] - base_portfolio["expected_return"],
        "Net expected return": current_portfolio["net_expected_return"] - base_portfolio["net_expected_return"],
        "Annualized volatility": current_portfolio["volatility"] - base_portfolio["volatility"],
        "Reserve allocation": current_portfolio["reserve_weight"] - base_portfolio["reserve_weight"],
    }
    st.caption("Metric changes: " + " · ".join(f"{label}: {value:+.2%}" for label, value in metric_changes.items()))
else:
    st.caption("No scenario portfolio exists, so weight and metric changes are unavailable.")

st.subheader("Comparison with the reported Lab 15 allocation")
reported_weights = [0.70, 0.0, 0.0, 0.15, 0.15]
reference = pd.DataFrame({
    "ETF": PROJECT2_TICKERS,
    "Reported in lab15-notes.md": [weight * 100 for weight in reported_weights],
    "Recalculated 60-month / 0-bps": [weight * 100 for weight in base_portfolio["weights"]],
})
st.dataframe(reference, hide_index=True, width="stretch",
             column_config={column: st.column_config.NumberColumn(format="%.2f%%") for column in reference.columns if column != "ETF"})
st.caption("The zero-cost calculation reproduces the documented 70% BIL / 15% VTI / 15% VXUS allocation.")

if annual_cost_bps == 20.0:
    ten_bps_reference = run_project2_analysis(
        PRICE_FILE,
        annual_cost_bps=10.0,
        use_last_36=period == "Last 36 monthly returns",
        target_return=target_return,
        minimum_reserve=reserve_minimum,
        expected_return_adjustment_bps=return_adjustment_bps,
        maximum_etf_weight=maximum_etf_weight,
        prior_weights=prior_weights,
    )
    ten_bps_portfolio = ten_bps_reference["constrained"]
    st.subheader("Selected 20-bps scenario compared with the 10-bps reference")
    if ten_bps_portfolio and current_portfolio:
        cost_comparison = pd.DataFrame([
            {
                "Scenario": "10-bps reference",
                "Gross expected return": ten_bps_portfolio["expected_return"] * 100,
                "Net expected return": ten_bps_portfolio["net_expected_return"] * 100,
                "Annualized volatility": ten_bps_portfolio["volatility"] * 100,
                "Reserve allocation": ten_bps_portfolio["reserve_weight"] * 100,
            },
            {
                "Scenario": "Selected 20-bps scenario",
                "Gross expected return": current_portfolio["expected_return"] * 100,
                "Net expected return": current_portfolio["net_expected_return"] * 100,
                "Annualized volatility": current_portfolio["volatility"] * 100,
                "Reserve allocation": current_portfolio["reserve_weight"] * 100,
            },
        ])
        st.dataframe(
            cost_comparison,
            hide_index=True,
            width="stretch",
            column_config={column: st.column_config.NumberColumn(format="%.2f%%") for column in cost_comparison.columns if column != "Scenario"},
        )
        cost_weight_comparison = pd.DataFrame({
            "ETF": PROJECT2_TICKERS,
            "10-bps reference": [weight * 100 for weight in ten_bps_portfolio["weights"]],
            "Selected 20-bps scenario": [weight * 100 for weight in current_portfolio["weights"]],
            "Weight change": [(selected - reference) * 100 for selected, reference in zip(current_portfolio["weights"], ten_bps_portfolio["weights"])],
        })
        st.dataframe(
            cost_weight_comparison,
            hide_index=True,
            width="stretch",
            column_config={column: st.column_config.NumberColumn(format="%.2f%%") for column in cost_weight_comparison.columns if column != "ETF"},
        )
        st.caption("Both scenarios use the same selected window, target, reserve, return adjustment, ETF cap, and prior-allocation input. Only the planning implementation-cost input differs.")
    else:
        st.warning("A 10-bps or selected 20-bps constrained portfolio is infeasible under the other selected scenario controls, so no cost comparison is available.")

st.header("Source-Backed Fund Evidence")
evidence_rows = [
    {
        "ETF": ticker,
        "Sponsor": record["sponsor"],
        "Fund": record["fund_name"],
        "Official source": record["official_url"],
        "Source date / availability note": record["source_date"],
        "Published expense ratio": record["expense_ratio"] * 100,
        "Liquidity": record["liquidity_status"],
        "Issuer exposure": record["issuer_status"],
        "Underlying derivatives": record["underlying_derivatives_status"],
    }
    for ticker, record in FUND_EVIDENCE.items()
]
st.caption(f"Official-source index retrieved {RETRIEVAL_DATE}. It does not convert later-viewed holdings into September 30, 2026 evidence.")
st.dataframe(
    pd.DataFrame(evidence_rows), hide_index=True, width="stretch",
    column_config={
        "Official source": st.column_config.LinkColumn("Official source", display_text="Sponsor page"),
        "Published expense ratio": st.column_config.NumberColumn(format="%.3f%%"),
    },
)
if current_portfolio:
    active_expense_ratio = weighted_expense_ratio(current_portfolio["weights"], PROJECT2_TICKERS)
    if active_expense_ratio is not None:
        st.info(
            f"Weighted published fund expense ratio for active ETFs: {active_expense_ratio:.3%}. "
            "Fund expenses are generally reflected in adjusted ETF prices; the planning transaction/implementation-cost control is separate and is the only additional subtraction in the net-return scenario."
        )
st.caption("Detailed dates, limitations, lineage, and reproduction instructions: `project2_data_lineage.md`.")

st.header("Portfolio Weights, Risk, and Mandate Evidence")
for portfolio in analysis["portfolios"]:
    with st.expander(portfolio["name"], expanded=portfolio["name"] == "Constrained 5% grid"):
        weight_frame = pd.DataFrame({"ETF": PROJECT2_TICKERS, "Weight": [weight * 100 for weight in portfolio["weights"]]})
        st.bar_chart(weight_frame.set_index("ETF"), y="Weight", width="stretch")
        st.dataframe(weight_frame, hide_index=True, width="stretch",
                     column_config={"Weight": st.column_config.NumberColumn(format="%.2f%%")})
        st.caption(f"Worst monthly return in the selected sample: {portfolio['worst_month']:.2%}. Historical estimates are not forecasts.")
        st.dataframe(pd.DataFrame(portfolio["checks"]), hide_index=True, width="stretch")

st.header("Point-in-Time Signal")
st.write("Proposed prospective rule: use the selected ALFRED DGS10 vintage. At or above the threshold, require committee review before authorizing a rebalance; otherwise the allocation is only eligible for committee review.")
signal_columns = st.columns(2)
with signal_columns[0]:
    st.markdown("**Point-in-time signal status**")
    st.write(signal["status"])
    st.metric("DGS10 observation", "—" if signal["value"] is None else f"{signal['value']:.2f}%")
with signal_columns[1]:
    st.markdown("**Committee decision status**")
    st.write(signal["decision"])
    st.metric("Observation date", "—" if signal["observation_date"] is None else signal["observation_date"].isoformat())
st.info(signal["reason"])
st.caption(f"Decision/vintage cutoff: {signal['vintage_date']}. {signal['availability']}")
with st.expander("DGS10 data card and limitations"):
    st.markdown(Path(__file__).with_name("project2_point_in_time_signal.md").read_text(encoding="utf-8"))

st.header("Stress Testing")
st.write("The sidebar controls recalculate all portfolio results. The tables below reproduce the two documented Lab 15 comparisons using the same stored price file and 0-bps historical convention.")
stability = run_project2_analysis(PRICE_FILE, annual_cost_bps=0.0, use_last_36=True)
partner = run_project2_analysis(PRICE_FILE, annual_cost_bps=0.0, target_return=0.07)
stress_rows = []
for label, result in [("Lab 15 base reproduction", base), ("Lab 15 36-month reproduction", stability), ("Lab 15 7% target reproduction", partner)]:
    portfolio = result["constrained"]
    stress_rows.append({
        "Scenario": label,
        "Weights": " / ".join(f"{ticker} {weight:.0%}" for ticker, weight in zip(PROJECT2_TICKERS, portfolio["weights"])) if portfolio else "Infeasible",
        "Gross return": portfolio["expected_return"] * 100 if portfolio else None,
        "Net return": portfolio["net_expected_return"] * 100 if portfolio else None,
        "Volatility": portfolio["volatility"] * 100 if portfolio else None,
        "Reserve": portfolio["reserve_weight"] * 100 if portfolio else None,
    })
st.dataframe(pd.DataFrame(stress_rows), hide_index=True, width="stretch",
             column_config={column: st.column_config.NumberColumn(format="%.2f%%") for column in ["Gross return", "Net return", "Volatility", "Reserve"]})
st.caption("The 36-month and 7% target outputs are computed live from `prices.csv`; they are not hardcoded labels. See the report for any rounding differences from Lab 15.")

st.header("Investment Committee Recommendation")
conditions = stop_conditions(analysis, signal)
if conditions:
    st.error("STOP CONDITION TRIGGERED")
    for condition in conditions:
        st.write(f"- {condition}")
else:
    st.warning("No deterministic stop was triggered, but a committee decision is still required.")
st.caption("Not committee-ready while required liquidity, issuer look-through, derivatives, turnover, and verified implementation-cost evidence remain unverified.")
