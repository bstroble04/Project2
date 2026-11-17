"""Date-level, point-in-time DGS10 governance signal for Project 2.

The signal intentionally uses an ALFRED vintage, never today's revised FRED
series. It is a proposed prospective committee-review rule, not a backtest.
"""

from __future__ import annotations

from datetime import date
from io import StringIO
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests


SERIES_ID = "DGS10"
SERIES_NAME = "10-Year Treasury Constant Maturity Rate"
SOURCE_URL = "https://alfred.stlouisfed.org/graph/alfredgraph.csv?id={series_id}&vintage_date={vintage_date}"


def fetch_dgs10_vintage(vintage_date: date) -> pd.DataFrame:
    """Fetch the ALFRED vintage available on the date-level decision cutoff."""
    url = SOURCE_URL.format(series_id=quote(SERIES_ID), vintage_date=vintage_date.isoformat())
    response = requests.get(url, timeout=30, headers={"User-Agent": "FIN43900-Project2/1.0"})
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text), na_values=["."], keep_default_na=True)
    if frame.empty or len(frame.columns) < 2:
        raise ValueError("ALFRED returned no usable DGS10 observations.")
    frame = frame.iloc[:, :2].copy()
    frame.columns = ["observation_date", "value"]
    frame["observation_date"] = pd.to_datetime(frame["observation_date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame.dropna(subset=["observation_date"]).sort_values("observation_date")


def unverified_signal(decision_date: date, threshold: float, reason: str) -> dict[str, Any]:
    """Return an explicit no-signal state when a vintage cannot be verified."""
    return {
        "status": "UNVERIFIED",
        "decision": "DO NOT AUTHORIZE REBALANCE",
        "reason": reason,
        "decision_date": decision_date,
        "vintage_date": decision_date,
        "threshold": threshold,
        "observation_date": None,
        "value": None,
        "availability": "No verified ALFRED vintage was available to the application.",
    }


def evaluate_dgs10_signal(
    historical_frame: pd.DataFrame,
    decision_date: date,
    threshold: float,
) -> dict[str, Any]:
    """Apply a proposed date-level DGS10 committee-review gate.

    Rule: if the latest nonmissing DGS10 observation in the ALFRED vintage as of
    ``decision_date`` is at or above ``threshold``, require committee review before
    authorizing a rebalance. Otherwise the signal is eligible for review. This rule
    does not claim a historical trading strategy or alter prices/return estimates.
    """
    if threshold < 0:
        raise ValueError("The DGS10 threshold cannot be negative.")
    required_columns = {"observation_date", "value"}
    if not required_columns.issubset(historical_frame.columns):
        return unverified_signal(decision_date, threshold, "The ALFRED data did not contain the required date and value columns.")
    frame = historical_frame.copy()
    frame["observation_date"] = pd.to_datetime(frame["observation_date"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    eligible = frame.loc[
        frame["observation_date"].notna()
        & frame["value"].notna()
        & (frame["observation_date"].dt.date <= decision_date)
    ].sort_values("observation_date")
    if eligible.empty:
        return unverified_signal(
            decision_date,
            threshold,
            "No nonmissing DGS10 observation dated on or before the selected decision date was present in the ALFRED vintage.",
        )
    latest = eligible.iloc[-1]
    value = float(latest["value"])
    decision = "COMMITTEE REVIEW REQUIRED" if value >= threshold else "ELIGIBLE FOR COMMITTEE REVIEW"
    return {
        "status": "AVAILABLE WITH DATE-LEVEL LIMITATION",
        "decision": decision,
        "reason": (
            f"Latest DGS10 observation in the ALFRED vintage is {value:.2f}%, "
            f"which is {'at or above' if value >= threshold else 'below'} the {threshold:.2f}% review threshold."
        ),
        "decision_date": decision_date,
        "vintage_date": decision_date,
        "observation_date": latest["observation_date"].date(),
        "value": value,
        "threshold": threshold,
        "availability": (
            "ALFRED confirms the observation was present in the selected date-level vintage. "
            "The graph export does not provide an intraday release timestamp; do not use this rule for intraday decisions."
        ),
    }


def live_dgs10_signal(decision_date: date, threshold: float) -> dict[str, Any]:
    """Fetch and evaluate one vintage, returning UNVERIFIED instead of revised data on failure."""
    try:
        return evaluate_dgs10_signal(fetch_dgs10_vintage(decision_date), decision_date, threshold)
    except (requests.RequestException, ValueError, pd.errors.ParserError) as error:
        return unverified_signal(decision_date, threshold, f"Could not verify the ALFRED vintage: {error}")
