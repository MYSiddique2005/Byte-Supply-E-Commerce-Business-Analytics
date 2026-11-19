"""Data loading and preparation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import DATA_PATH, MEGA_SALE_DAYS


def load_transactions(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Load the raw transaction CSV with ``Date_Time`` parsed as datetime."""
    return pd.read_csv(path, parse_dates=["Date_Time"])


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Add helper columns used throughout the analysis.

    * ``YearMonth``      – monthly period
    * ``Quarter``        – quarterly period
    * ``Business_Year``  – 1..5, where a business year runs October → September
    * ``Is_Mega_Sale``   – True on 9.9, 10.10, 11.11 and 12.12 shopping festivals
    * ``Is_Late``        – True when the delivery was late

    Missing customer ratings are intentionally *not* imputed.
    """
    out = df.copy()
    out["YearMonth"] = out["Date_Time"].dt.to_period("M")
    out["Quarter"] = out["Date_Time"].dt.to_period("Q")
    out["Business_Year"] = np.where(out["Month"] >= 10, out["Year"], out["Year"] - 1) - 2020
    out["Is_Mega_Sale"] = out["Date_Time"].dt.strftime("%m-%d").isin(MEGA_SALE_DAYS)
    out["Is_Late"] = out["Delivery_Status"].eq("Late")
    return out


def data_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    """Column-level summary: dtype, missing values and an example value."""
    return pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "missing": df.isna().sum(),
            "missing_pct": (df.isna().mean() * 100).round(2),
            "unique": df.nunique(),
            "example": df.iloc[0],
        }
    )
