"""Byte Supply — e-commerce business analytics toolkit.

Modules
-------
config       Paths, colour palette and shared constants.
data         Loading and feature preparation for the transaction dataset.
kpis         Business KPI and insight calculations.
forecasting  Monthly revenue regression models and 12-month forecast.
plots        Static (matplotlib/seaborn) charts used in the notebook and README.
dashboard    Interactive Plotly dashboard exported to ``docs/index.html``.
"""

from .data import load_transactions, prepare
from .kpis import (
    overall_kpis,
    business_year_kpis,
    category_summary,
    insight_metrics,
    segment_summary,
)
from .forecasting import build_monthly_frame, compare_models, forecast_next_months

__all__ = [
    "load_transactions",
    "prepare",
    "overall_kpis",
    "business_year_kpis",
    "category_summary",
    "insight_metrics",
    "segment_summary",
    "build_monthly_frame",
    "compare_models",
    "forecast_next_months",
]

__version__ = "1.0.0"
