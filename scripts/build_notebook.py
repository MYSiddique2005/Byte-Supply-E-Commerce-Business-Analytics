"""Regenerate notebooks/Byte_Supply_Big_Data_Analytics.ipynb from source cells."""
from pathlib import Path
import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = [
md("""# 🛒 Byte Supply — Big Data Analytics

**INTI International University · Mobility Program**

End-to-end analysis of **24,991 e-commerce transactions** (October 2021 – September 2026) for *Byte Supply*, a Malaysian online retailer of electronics, accessories and office products.

| Section | What it answers |
|---|---|
| 1. Data overview | What does the dataset contain? Is it clean? |
| 2. KPI analysis | How is the business performing overall and year by year? |
| 3. Required visualisations | Revenue trend · Category performance · Rating distribution |
| 4. Additional visualisations | Seasonality · Shopping hours · Payment mix · Delivery vs satisfaction |
| 5. Insight calculations | The numbers behind the business recommendations |
| 6. Machine learning | Linear vs Polynomial regression on monthly revenue |
| 7. Forecast | Next 12 months of revenue |
| 8. Recommendations | What Byte Supply should do next |

> All reusable logic lives in [`src/byte_supply`](../src/byte_supply); this notebook tells the story.
> The dataset is **synthetic** and is used to demonstrate the analytics workflow."""),
code("""import sys
from pathlib import Path

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
from IPython.display import display

from byte_supply import plots
from byte_supply.data import load_transactions, prepare, data_dictionary
from byte_supply.kpis import (overall_kpis, business_year_kpis, category_summary,
                              segment_summary, insight_metrics)
from byte_supply.forecasting import build_monthly_frame, compare_models, forecast_next_months

pd.set_option("display.float_format", "{:,.2f}".format)
plots.set_style()

df = prepare(load_transactions(ROOT / "data" / "byte_supply_transactions.csv"))
print(f"Loaded {len(df):,} rows × {df.shape[1]} columns")
df.head()"""),
md("""## 1. Data Overview & Preparation

`prepare()` parses timestamps and adds helper fields:

- **`YearMonth` / `Quarter`** – periods for time-series aggregation
- **`Business_Year`** – 1 → 5, each running **October → September**
- **`Is_Mega_Sale`** – the 9.9, 10.10, 11.11 and 12.12 shopping festivals
- **`Is_Late`** – late-delivery flag

Missing customer ratings are **kept as missing** (not every customer leaves a review) rather than imputed."""),
code("data_dictionary(df)"),
md("## 2. KPI Analysis\n\n### 2.1 Headline KPIs (full five-year period)"),
code("overall_kpis(df).to_frame(\"Value\")"),
md("### 2.2 KPIs by business year"),
code("""by_year = business_year_kpis(df)
by_year.style.format("{:,.2f}").background_gradient(subset=["Revenue", "Revenue_Growth_Pct"], cmap="Blues")"""),
md("""**Reading the table:** revenue more than doubled from Year 1 to Year 5, while AOV, on-time delivery and ratings all trended up and stock-outs fell from ~4% to ~1.7%. Gross margin stayed remarkably stable at ~36.5% — growth came from **volume**, not price."""),
md("## 3. Required Visualisations\n\n### 3.1 Monthly revenue trend"),
code("plots.monthly_revenue_trend(df);"),
md("### 3.2 Sales and profitability by category"),
code("""cat = category_summary(df)
plots.category_performance(cat)
cat"""),
md("""Small Electronics generates a third of revenue but has the **thinnest margin (30.6%)**. Phone Accessories and Office Supplies earn 42–44% — ideal add-on / bundle items."""),
md("### 3.3 Customer rating distribution"),
code("plots.rating_distribution(df);"),
md("## 4. Additional Visualisations\n\n### 4.1 Seasonality — revenue by month and business year"),
code("plots.seasonality_heatmap(df);"),
md("### 4.2 When do customers shop?"),
code("plots.hour_weekday_heatmap(df);"),
md("### 4.3 Payment method mix"),
code("plots.payment_mix(df);"),
md("### 4.4 Delivery performance and customer satisfaction\n\nShown as two aligned panels (rather than a dual-axis chart) so each measure keeps its own honest scale."),
code("plots.delivery_vs_rating(df);\nplots.late_delivery_impact(df);"),
md("### 4.5 Segment breakdowns"),
code("""for col in ["Customer_Segment", "Device", "Customer_State"]:
    print(f"\\n▶ {col}")
    display(segment_summary(df, col))"""),
md("## 5. Insight Calculations"),
code("insights = insight_metrics(df)\ninsights.to_frame(\"Value\")"),
md("""## 6. Machine Learning — Monthly Revenue Regression

**Target:** monthly revenue (60 observations).
**Features:** `time_index` (trend), `month`, and cyclical `month_sin` / `month_cos` (seasonality).
**Validation:** chronological **80/20 split** — train on the first 48 months, test on the last 12 — so the model never sees the future.

| Model | Idea |
|---|---|
| Linear Regression | Straight-line trend + seasonal terms |
| Polynomial Regression (degree 2) | Adds squared & interaction terms to capture curvature and stronger peaks |"""),
code("""monthly = build_monthly_frame(df)
comparison = compare_models(monthly, train_frac=0.8)
comparison.metrics"""),
code("""plots.actual_vs_predicted(monthly, comparison)
plots.residuals(comparison)
print("Selected model:", comparison.best_name)"""),
md("""The polynomial model wins on every metric (lower MAE/RMSE, higher R²) because it follows the Q4 peak more closely. Both models **under-predict extreme mega-sale months** — with only 60 monthly points, that is an expected limitation."""),
md("## 7. Next 12-Month Revenue Forecast\n\nThe selected model is refitted on all 60 months and projected forward."),
code("""forecast = forecast_next_months(monthly, comparison.best_name, periods=12)
plots.forecast_chart(monthly, forecast, comparison.best_name)
print(f"Forecast total: RM{forecast['Forecast_Revenue'].sum():,.0f}")
forecast"""),
md("""## 8. Key Insights & Recommendations

| # | Insight | Recommendation |
|---|---|---|
| 1 | **Q4 = ~29% of annual revenue**; Nov–Dec are peak months | Lock in inventory & courier capacity by September; plan campaigns around 10.10 / 11.11 / 12.12 |
| 2 | **Mega-sale margin ~25% vs ~37%** on normal days | Use mega-sales for acquisition, but bundle high-margin accessories to protect profit |
| 3 | **Late delivery ≈ −1.2 stars** (2.99 vs 4.20) | Add courier SLAs; route peak-season orders to the best-performing courier |
| 4 | **~35% of orders between 19:00–23:00** | Schedule push notifications, flash deals and ads for the evening window |
| 5 | **E-wallet share rising**, COD falling | Partner with e-wallet providers for cashback; gradually reduce COD cost exposure |
| 6 | **Small Electronics = 34% of sales but lowest margin** | Cross-sell Phone Accessories / Office Supplies (42–44% margin) at checkout |
| 7 | **Repeat-customer rate only ~24.5%** | Launch a loyalty / points programme targeted at first-time buyers |

### Limitations
- The dataset is **synthetic** — patterns illustrate the workflow, not real Malaysian consumer behaviour.
- It is a stored CSV, not a live stream; *velocity* is demonstrated through timestamp-level analysis.
- 60 monthly points is a small sample for ML; the forecast is a **model-based estimate**, not a guarantee.
- Missing ratings are left as missing, so rating KPIs describe *rated* orders only."""),
]

nb = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
})
out = Path(__file__).resolve().parents[1] / "notebooks" / "Byte_Supply_Big_Data_Analytics.ipynb"
nbf.write(nb, out)
print("wrote", out)
