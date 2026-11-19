"""Interactive Plotly dashboard exported as a single static HTML page.

The page is written to ``docs/index.html`` so it can be served by GitHub Pages.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from .config import (
    ACCENT, GRID, MONTH_ABBR, MUTED, PALETTE, PRIMARY, SEQUENTIAL, SURFACE,
    TEXT, TEXT_SECONDARY, WEEKDAYS,
)
from .kpis import category_summary, segment_summary

SEQ_SCALE = [[i / (len(SEQUENTIAL) - 1), c] for i, c in enumerate(SEQUENTIAL)]
FONT = "Inter, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif"


def _layout(fig: go.Figure, height: int = 420, **kw) -> go.Figure:
    kw.setdefault("margin", dict(l=10, r=10, t=30, b=10))
    fig.update_layout(
        height=height,
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family=FONT, color=TEXT_SECONDARY, size=12),
        hoverlabel=dict(bgcolor="white", font=dict(family=FONT, color=TEXT)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"),
        colorway=PALETTE,
        **kw,
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, zeroline=False)
    return fig


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #
def fig_trend(df: pd.DataFrame) -> go.Figure:
    m = df.groupby(df["YearMonth"].dt.to_timestamp()).agg(
        Revenue=("Total_Amount", "sum"), Profit=("Gross_Profit", "sum"), Orders=("Transaction_ID", "count")
    )
    fig = go.Figure()
    metrics = [("Revenue", "RM%{y:,.0f}"), ("Profit", "RM%{y:,.0f}"), ("Orders", "%{y:,} orders")]
    for i, (name, fmt) in enumerate(metrics):
        visible = i == 0
        fig.add_trace(go.Scatter(x=m.index, y=m[name], name=f"Monthly {name.lower()}", mode="lines+markers",
                                 line=dict(color=PRIMARY, width=2), marker=dict(size=6), visible=visible,
                                 hovertemplate=f"%{{x|%b %Y}}<br>{fmt}<extra></extra>"))
        fig.add_trace(go.Scatter(x=m.index, y=m[name].rolling(3).mean(), name="3-month average",
                                 line=dict(color=ACCENT, width=2, dash="dot"), visible=visible,
                                 hovertemplate=f"3-mo avg: {fmt}<extra></extra>"))
    buttons = []
    for i, (name, _) in enumerate(metrics):
        vis = [False] * 6
        vis[2 * i] = vis[2 * i + 1] = True
        buttons.append(dict(label=name, method="update", args=[{"visible": vis}]))
    fig.update_layout(
        updatemenus=[dict(type="buttons", direction="right", x=1, xanchor="right", y=1.15, buttons=buttons,
                          bgcolor="white", bordercolor=GRID, font=dict(color=TEXT))],
        hovermode="x unified",
    )
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.06),
                     rangeselector=dict(buttons=[dict(count=1, label="1y", step="year", stepmode="backward"),
                                                 dict(count=2, label="2y", step="year", stepmode="backward"),
                                                 dict(step="all", label="All")], x=0, y=1.12))
    return _layout(fig, 460, margin=dict(l=10, r=10, t=70, b=10))


def fig_category(df: pd.DataFrame) -> go.Figure:
    cat = category_summary(df).sort_values("Revenue")
    views = [
        ("Revenue", cat["Revenue"], "RM%{x:,.0f}<br>%{customdata:.1f}% of sales", cat["Share_Pct"], PRIMARY),
        ("Gross margin %", cat["Margin_Pct"], "%{x:.1f}% margin<extra></extra>", None, ACCENT),
        ("Gross profit", cat["Profit"], "RM%{x:,.0f} profit<extra></extra>", None, PALETTE[2]),
    ]
    fig = go.Figure()
    for i, (name, values, tmpl, cd, color) in enumerate(views):
        fig.add_trace(go.Bar(y=cat.index, x=values, orientation="h", name=name, visible=i == 0,
                             marker=dict(color=color, cornerradius=4), customdata=cd,
                             hovertemplate="<b>%{y}</b><br>" + tmpl + ("<extra></extra>" if cd is not None else ""),
                             text=[f"{v:,.0f}" if "%" not in name else f"{v:.1f}%" for v in values],
                             textposition="outside", cliponaxis=False))
    fig.update_layout(updatemenus=[dict(
        type="buttons", direction="right", x=1, xanchor="right", y=1.15, bgcolor="white", bordercolor=GRID,
        font=dict(color=TEXT),
        buttons=[dict(label=v[0], method="update", args=[{"visible": [j == i for j in range(3)]}])
                 for i, v in enumerate(views)])], showlegend=False)
    return _layout(fig, 380, margin=dict(l=10, r=60, t=60, b=10))


def fig_segments(df: pd.DataFrame) -> go.Figure:
    dims = {
        "State": "Customer_State",
        "Device": "Device",
        "Segment": "Customer_Segment",
        "Age group": "Customer_Age_Group",
        "Courier": "Courier",
        "Customer type": "Customer_Type",
    }
    fig = go.Figure()
    for i, (label, col) in enumerate(dims.items()):
        s = segment_summary(df, col).sort_values("Revenue")
        fig.add_trace(go.Bar(
            y=s.index, x=s["Revenue"], orientation="h", visible=i == 0, name=label,
            marker=dict(color=PRIMARY, cornerradius=4),
            customdata=s[["Orders", "AOV", "Avg_Rating", "On_Time_Pct", "Share_Pct"]].values,
            hovertemplate=("<b>%{y}</b><br>Revenue: RM%{x:,.0f} (%{customdata[4]:.1f}%)"
                           "<br>Orders: %{customdata[0]:,}<br>AOV: RM%{customdata[1]:.2f}"
                           "<br>Avg rating: %{customdata[2]:.2f}<br>On-time: %{customdata[3]:.1f}%<extra></extra>"),
        ))
    fig.update_layout(showlegend=False, updatemenus=[dict(
        type="dropdown", x=1, xanchor="right", y=1.15, bgcolor="white", bordercolor=GRID, font=dict(color=TEXT),
        buttons=[dict(label=f"Break down by: {k}", method="update",
                      args=[{"visible": [j == i for j in range(len(dims))]}]) for i, k in enumerate(dims)])])
    fig.update_xaxes(tickprefix="RM")
    return _layout(fig, 380, margin=dict(l=10, r=10, t=60, b=10))


def fig_seasonality(df: pd.DataFrame) -> go.Figure:
    piv = df.pivot_table(index="Month", columns="Business_Year", values="Total_Amount", aggfunc="sum")
    fig = go.Figure(go.Heatmap(
        z=piv.values / 1000, x=[f"Year {c}" for c in piv.columns], y=MONTH_ABBR, colorscale=SEQ_SCALE,
        xgap=2, ygap=2, text=(piv.values / 1000).round(0), texttemplate="%{text:.0f}",
        hovertemplate="%{y}, %{x}<br>RM%{z:,.1f}k<extra></extra>", colorbar=dict(title="RM k", thickness=12)))
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, 440)


def fig_hour_weekday(df: pd.DataFrame) -> go.Figure:
    hw = df.pivot_table(index="Day_of_Week", columns="Hour", values="Transaction_ID", aggfunc="count").reindex(WEEKDAYS)
    fig = go.Figure(go.Heatmap(
        z=hw.values, x=[f"{h:02d}:00" for h in hw.columns], y=hw.index, colorscale=SEQ_SCALE, xgap=1, ygap=1,
        hovertemplate="%{y} %{x}<br>%{z:,} orders<extra></extra>", colorbar=dict(title="Orders", thickness=12)))
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, 330)


def fig_payment(df: pd.DataFrame) -> go.Figure:
    pm = pd.crosstab(df["Business_Year"], df["Payment_Method"], normalize="index") * 100
    pm = pm[pm.mean().sort_values(ascending=False).index]
    fig = go.Figure()
    for color, col in zip(PALETTE, pm.columns):
        fig.add_trace(go.Bar(x=[f"Year {i}" for i in pm.index], y=pm[col], name=col,
                             marker=dict(color=color, line=dict(color=SURFACE, width=2)),
                             hovertemplate=f"<b>{col}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(ticksuffix="%", range=[0, 100])
    return _layout(fig, 400)


def fig_delivery(df: pd.DataFrame) -> go.Figure:
    from plotly.subplots import make_subplots

    q = df.groupby(df["Quarter"].dt.to_timestamp()).agg(
        on_time=("Delivery_Status", lambda s: (s == "On-time").mean() * 100), rating=("Rating", "mean"))
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=("On-time delivery rate", "Average customer rating"))
    fig.add_trace(go.Scatter(x=q.index, y=q["on_time"], name="On-time %", line=dict(color=PRIMARY),
                             marker=dict(size=7), mode="lines+markers",
                             hovertemplate="%{x|Q%q %Y}: %{y:.1f}%<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=q.index, y=q["rating"], name="Avg rating", line=dict(color=ACCENT),
                             marker=dict(size=7, symbol="square"), mode="lines+markers",
                             hovertemplate="%{x|%b %Y}: %{y:.2f} ★<extra></extra>"), 2, 1)
    fig.update_yaxes(ticksuffix="%", row=1, col=1)
    fig.update_layout(showlegend=False)
    for a in fig.layout.annotations:
        a.update(x=0, xanchor="left", font=dict(color=TEXT, size=13))
    return _layout(fig, 440)


def fig_top_products(df: pd.DataFrame, n: int = 10) -> go.Figure:
    p = (df.groupby(["Product_Name", "Category"]).agg(Revenue=("Total_Amount", "sum"),
                                                      Units=("Quantity", "sum"),
                                                      Profit=("Gross_Profit", "sum"))
         .reset_index().nlargest(n, "Revenue").sort_values("Revenue"))
    cats = sorted(df["Category"].unique())
    color = {c: PALETTE[i] for i, c in enumerate(cats)}
    fig = go.Figure()
    for c in cats:
        sub = p[p["Category"] == c]
        if sub.empty:
            continue
        fig.add_trace(go.Bar(y=sub["Product_Name"], x=sub["Revenue"], orientation="h", name=c,
                             marker=dict(color=color[c], cornerradius=4),
                             customdata=sub[["Units", "Profit"]].values,
                             hovertemplate=("<b>%{y}</b><br>Revenue: RM%{x:,.0f}<br>Units: %{customdata[0]:,}"
                                            "<br>Profit: RM%{customdata[1]:,.0f}<extra></extra>")))
    fig.update_yaxes(categoryorder="array", categoryarray=p["Product_Name"].tolist())
    fig.update_xaxes(tickprefix="RM")
    return _layout(fig, 420)


def fig_forecast(monthly: pd.DataFrame, comparison, forecast: pd.DataFrame) -> go.Figure:
    p = comparison.predictions
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly["MonthStart"], y=monthly["Revenue"], name="Actual",
                             line=dict(color=MUTED, width=2), mode="lines+markers", marker=dict(size=5),
                             hovertemplate="Actual: RM%{y:,.0f}<extra></extra>"))
    for color, name in zip([PALETTE[2], PRIMARY], ["Linear Regression", "Polynomial Regression (degree 2)"]):
        fig.add_trace(go.Scatter(x=p["MonthStart"], y=p[name], name=f"{name} (test)", line=dict(color=color),
                                 mode="lines+markers", marker=dict(size=7),
                                 hovertemplate=f"{name}: RM%{{y:,.0f}}<extra></extra>"))
    fig.add_trace(go.Scatter(x=forecast["MonthStart"], y=forecast["Forecast_Revenue"], name="12-month forecast",
                             line=dict(color=ACCENT, width=2.5, dash="dash"), mode="lines+markers",
                             marker=dict(size=8), hovertemplate="Forecast: RM%{y:,.0f}<extra></extra>"))
    fig.add_vrect(x0=p["MonthStart"].min(), x1=p["MonthStart"].max(), fillcolor=PRIMARY, opacity=0.06,
                  line_width=0, annotation_text="test window", annotation_position="top left")
    fig.add_vrect(x0=forecast["MonthStart"].min(), x1=forecast["MonthStart"].max(), fillcolor=ACCENT,
                  opacity=0.07, line_width=0, annotation_text="forecast", annotation_position="top left")
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(tickprefix="RM")
    return _layout(fig, 460)


# --------------------------------------------------------------------------- #
# Page assembly
# --------------------------------------------------------------------------- #
def _div(fig: go.Figure) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False,
                       config={"displaylogo": False, "responsive": True})


def _table(frame: pd.DataFrame) -> str:
    return frame.to_html(classes="tbl", border=0, index=False, float_format=lambda v: f"{v:,.2f}")


def build_dashboard(df, kpis, by_year, insights, monthly, comparison, forecast, out: Path) -> Path:
    tiles = [
        ("Total revenue", f"RM{kpis['Total revenue (RM)']/1e6:,.2f}M", "Oct 2021 – Sep 2026"),
        ("Orders", f"{kpis['Number of orders']:,.0f}", f"{kpis['Unique customers']:,.0f} unique customers"),
        ("Avg order value", f"RM{kpis['Average order value (RM)']:,.2f}", "per transaction"),
        ("Gross margin", f"{kpis['Gross margin (%)']:.1f}%", f"RM{kpis['Gross profit (RM)']/1e3:,.0f}k gross profit"),
        ("Avg rating", f"{kpis['Average rating (rated orders)']:.2f} ★", f"{kpis['Rated orders (%)']:.0f}% of orders rated"),
        ("On-time delivery", f"{kpis['On-time delivery rate (%)']:.1f}%", f"stock-out rate {kpis['Stock-out rate (%)']:.1f}%"),
        ("YoY growth (Y5)", f"+{by_year['Revenue_Growth_Pct'].iloc[-1]:.1f}%", "business year 5 vs year 4"),
        ("12-mo forecast", f"RM{forecast['Forecast_Revenue'].sum()/1e3:,.0f}k", comparison.best_name.split(" (")[0]),
    ]
    tiles_html = "".join(
        f'<div class="tile"><div class="tl">{a}</div><div class="tv">{b}</div><div class="ts">{c}</div></div>'
        for a, b, c in tiles
    )
    yr = by_year.reset_index()[["Business_Year", "Orders", "Revenue", "Gross_Profit", "AOV", "Margin_Pct",
                                "Revenue_Growth_Pct", "Avg_Rating", "On_Time_Pct"]]
    yr.columns = ["Year", "Orders", "Revenue (RM)", "Gross profit (RM)", "AOV (RM)", "Margin %", "Growth %",
                  "Avg rating", "On-time %"]
    yr["Orders"] = yr["Orders"].map("{:,}".format)
    yr["Growth %"] = yr["Growth %"].map(lambda v: "—" if pd.isna(v) else f"{v:+.1f}")
    metrics = comparison.metrics.copy()

    sections = [
        ("trend", "Revenue trend", "Switch between revenue, profit and orders; drag the slider to zoom.", _div(fig_trend(df))),
        ("category", "Category performance", "Small Electronics leads on sales; accessories lead on margin.", _div(fig_category(df))),
        ("segments", "Customer & channel explorer", "Use the dropdown to slice revenue by any dimension. Hover for AOV, rating and on-time %.", _div(fig_segments(df))),
        ("products", "Top 10 products", "Best sellers by revenue, coloured by category.", _div(fig_top_products(df))),
        ("seasonality", "Seasonality", "Revenue (RM thousand) by calendar month and business year.", _div(fig_seasonality(df))),
        ("timing", "When customers shop", "Order volume by hour of day and weekday.", _div(fig_hour_weekday(df))),
        ("payments", "Payment mix", "Share of orders by payment method — click legend items to isolate.", _div(fig_payment(df))),
        ("delivery", "Delivery & satisfaction", f"Late orders average {insights['Rating when late']:.2f}★ vs {insights['Rating when on time']:.2f}★ when on time.", _div(fig_delivery(df))),
        ("forecast", "Machine learning forecast", f"Chronological 80/20 split; best model: <b>{comparison.best_name}</b>.", _div(fig_forecast(monthly, comparison, forecast)) + _table(metrics)),
        ("years", "Business-year scorecard", "A business year runs October → September.", _table(yr)),
    ]
    nav = "".join(f'<a href="#{sid}">{title}</a>' for sid, title, *_ in sections)
    body = "".join(
        f'<section id="{sid}" class="card"><h2>{title}</h2><p class="sub">{sub}</p>{content}</section>'
        for sid, title, sub, content in sections
    )
    insight_items = [
        f"<b>{insights['Q4 revenue share (%)']:.1f}%</b> of all revenue lands in Q4 (Oct–Dec).",
        f"Mega-sale days run at <b>{insights['Mega-sale gross margin (%)']:.1f}%</b> margin vs "
        f"<b>{insights['Other days gross margin (%)']:.1f}%</b> on other days — volume at a price.",
        f"Late deliveries cost about <b>{insights['Rating when on time'] - insights['Rating when late']:.1f} stars</b> per order.",
        f"<b>{insights['Evening orders 19:00-22:59 (%)']:.1f}%</b> of orders are placed between 19:00 and 23:00.",
        f"Repeat-customer rate is <b>{kpis['Repeat customer rate (%)']:.1f}%</b> — the biggest growth lever.",
    ]
    insights_html = "".join(f"<li>{i}</li>" for i in insight_items)

    html = TEMPLATE.format(
        tiles=tiles_html, nav=nav, body=body, insights=insights_html, generated=date.today().isoformat(),
        surface=SURFACE, text=TEXT, text2=TEXT_SECONDARY, grid=GRID, primary=PRIMARY, accent=ACCENT,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Byte Supply — Interactive Analytics Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  :root {{ --surface:{surface}; --text:{text}; --text2:{text2}; --grid:{grid}; --primary:{primary}; --accent:{accent}; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#f3f2ee; color:var(--text); font-family:Inter,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  header {{ background:linear-gradient(135deg,#0d366b 0%,#2a78d6 70%,#3987e5 100%); color:white; padding:42px 24px 90px; }}
  header .wrap {{ max-width:1200px; margin:0 auto; }}
  header h1 {{ margin:0 0 6px; font-size:32px; letter-spacing:-.5px; }}
  header p {{ margin:0; opacity:.85; }}
  .badge {{ display:inline-block; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.3); border-radius:999px; padding:3px 12px; font-size:12px; margin-bottom:14px; }}
  main {{ max-width:1200px; margin:-64px auto 40px; padding:0 16px; }}
  .tiles {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
  .tile {{ background:var(--surface); border-radius:12px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  .tl {{ font-size:12px; text-transform:uppercase; letter-spacing:.6px; color:var(--text2); }}
  .tv {{ font-size:26px; font-weight:700; margin:4px 0 2px; }}
  .ts {{ font-size:12px; color:var(--text2); }}
  nav {{ position:sticky; top:0; z-index:5; background:rgba(243,242,238,.92); backdrop-filter:blur(6px); padding:12px 0; margin:16px 0 4px; display:flex; flex-wrap:wrap; gap:6px; }}
  nav a {{ font-size:13px; color:var(--text); text-decoration:none; background:var(--surface); border:1px solid var(--grid); border-radius:999px; padding:5px 12px; }}
  nav a:hover {{ border-color:var(--primary); color:var(--primary); }}
  .card {{ background:var(--surface); border-radius:12px; padding:20px 22px; margin:14px 0; box-shadow:0 1px 3px rgba(0,0,0,.08); scroll-margin-top:64px; }}
  .card h2 {{ margin:0; font-size:18px; }}
  .sub {{ margin:4px 0 8px; color:var(--text2); font-size:14px; }}
  .insights ul {{ margin:8px 0 0; padding-left:20px; line-height:1.8; }}
  .tbl {{ width:100%; border-collapse:collapse; margin-top:14px; font-size:13px; font-variant-numeric:tabular-nums; }}
  .tbl th {{ text-align:right; color:var(--text2); font-weight:600; border-bottom:2px solid var(--grid); padding:8px; }}
  .tbl td {{ text-align:right; border-bottom:1px solid var(--grid); padding:8px; }}
  .tbl th:first-child, .tbl td:first-child {{ text-align:left; }}
  @media (max-width:800px) {{ .tiles {{ grid-template-columns:repeat(2,1fr); }} }}
  footer {{ text-align:center; color:var(--text2); font-size:12px; padding:20px; }}
  footer a {{ color:var(--primary); }}
</style>
</head>
<body>
<header><div class="wrap">
  <span class="badge">INTI International University · Mobility Program</span>
  <h1>Byte Supply — E-Commerce Analytics</h1>
  <p>24,991 transactions · 5 business years · 30 products · interactive KPIs, segmentation and ML forecasting</p>
</div></header>
<main>
  <div class="tiles">{tiles}</div>
  <nav>{nav}</nav>
  <section class="card insights"><h2>Key insights</h2><ul>{insights}</ul></section>
  {body}
</main>
<footer>Synthetic dataset for coursework · generated {generated} ·
<a href="https://github.com/MYSiddique2005/Byte-Supply-E-Commerce-Business-Analytics">source on GitHub</a></footer>
</body>
</html>
"""
