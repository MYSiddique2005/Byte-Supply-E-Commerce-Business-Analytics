"""End-to-end pipeline: load data → KPIs → charts → ML forecast → dashboard.

Usage
-----
    python scripts/run_pipeline.py

Outputs
-------
    assets/figures/*.png   static charts (used in the README)
    reports/*.csv          KPI tables, model metrics and the 12-month forecast
    docs/index.html        interactive dashboard (served by GitHub Pages)
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from byte_supply import plots  # noqa: E402
from byte_supply.config import DOCS_DIR, FIGURES_DIR, REPORTS_DIR  # noqa: E402
from byte_supply.dashboard import build_dashboard  # noqa: E402
from byte_supply.data import load_transactions, prepare  # noqa: E402
from byte_supply.forecasting import build_monthly_frame, compare_models, forecast_next_months  # noqa: E402
from byte_supply.kpis import (  # noqa: E402
    business_year_kpis, category_summary, insight_metrics, overall_kpis,
)


def save(fig, name: str) -> None:
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  ✓ {path.relative_to(FIGURES_DIR.parents[1])}")


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data…")
    df = prepare(load_transactions())
    print(f"  {len(df):,} rows × {df.shape[1]} columns")

    print("Computing KPIs…")
    kpis = overall_kpis(df)
    by_year = business_year_kpis(df)
    cat = category_summary(df)
    insights = insight_metrics(df)
    kpis.round(2).rename("Value").to_csv(REPORTS_DIR / "kpi_summary.csv", index_label="KPI")
    by_year.round(2).to_csv(REPORTS_DIR / "business_year_kpis.csv")
    cat.round(2).to_csv(REPORTS_DIR / "category_summary.csv")
    insights.round(2).rename("Value").to_csv(REPORTS_DIR / "insight_metrics.csv", index_label="Metric")

    print("Training models…")
    monthly = build_monthly_frame(df)
    comparison = compare_models(monthly)
    forecast = forecast_next_months(monthly, comparison.best_name)
    comparison.metrics.round(3).to_csv(REPORTS_DIR / "model_metrics.csv", index=False)
    forecast.round(2).to_csv(REPORTS_DIR / "forecast_12_months.csv", index=False)
    print(comparison.metrics.round(3).to_string(index=False))

    print("Rendering static charts…")
    plots.set_style()
    save(plots.monthly_revenue_trend(df), "01_monthly_revenue_trend")
    save(plots.category_performance(cat), "02_category_performance")
    save(plots.rating_distribution(df), "03_rating_distribution")
    save(plots.seasonality_heatmap(df), "04_seasonality_heatmap")
    save(plots.hour_weekday_heatmap(df), "05_hour_weekday_heatmap")
    save(plots.payment_mix(df), "06_payment_mix")
    save(plots.delivery_vs_rating(df), "07_delivery_vs_rating")
    save(plots.late_delivery_impact(df), "08_late_delivery_impact")
    save(plots.actual_vs_predicted(monthly, comparison), "09_actual_vs_predicted")
    save(plots.residuals(comparison), "10_residuals")
    save(plots.forecast_chart(monthly, forecast, comparison.best_name), "11_forecast")

    print("Building interactive dashboard…")
    out = build_dashboard(df, kpis, by_year, insights, monthly, comparison, forecast, DOCS_DIR / "index.html")
    print(f"  ✓ {out.relative_to(DOCS_DIR.parent)}")
    print("Done.")


if __name__ == "__main__":
    main()
