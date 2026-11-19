"""Static charts (matplotlib / seaborn).

Every function returns a ``matplotlib.figure.Figure`` so it can be shown inline
in the notebook or saved to ``assets/figures`` by ``scripts/run_pipeline.py``.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

from .config import (
    ACCENT, GRID, MONTH_ABBR, MUTED, PALETTE, PRIMARY, SEQUENTIAL, SURFACE,
    TEXT, TEXT_SECONDARY, WEEKDAYS,
)

SEQ_CMAP = LinearSegmentedColormap.from_list("byte_seq", SEQUENTIAL)
RM = mtick.FuncFormatter(lambda v, _: f"RM{v/1000:,.0f}k" if abs(v) >= 1000 else f"RM{v:,.0f}")


def set_style() -> None:
    """Apply the project's chart style globally."""
    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.titlecolor": TEXT,
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.titlelocation": "left",
            "axes.titlepad": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.prop_cycle": plt.cycler(color=PALETTE),
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
            "legend.frameon": False,
            "font.size": 10,
            "lines.linewidth": 2,
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
        }
    )


def _subtitle(ax, text: str) -> None:
    ax.text(0, 1.01, text, transform=ax.transAxes, color=TEXT_SECONDARY, fontsize=9.5, va="bottom")


# --------------------------------------------------------------------------- #
# Required visualisations
# --------------------------------------------------------------------------- #
def monthly_revenue_trend(df: pd.DataFrame):
    monthly = df.groupby("YearMonth")["Total_Amount"].sum()
    x = monthly.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(x, monthly.values, color=PRIMARY, alpha=0.45, linewidth=1.5, marker="o", markersize=3,
            label="Monthly revenue")
    ax.plot(x, monthly.rolling(3).mean().values, color=PRIMARY, linewidth=2.5, label="3-month moving average")
    peak = monthly.idxmax()
    ax.annotate(f"Peak {peak.strftime('%b %Y')}\nRM{monthly.max():,.0f}",
                xy=(peak.to_timestamp(), monthly.max()), xytext=(-110, -8), textcoords="offset points",
                color=TEXT, fontsize=9, arrowprops=dict(arrowstyle="->", color=TEXT_SECONDARY))
    ax.yaxis.set_major_formatter(RM)
    ax.set_title("Monthly revenue, Oct 2021 – Sep 2026", pad=22)
    _subtitle(ax, "Steady growth with recurring Q4 peaks driven by mega-sale campaigns")
    ax.set_xlabel(""); ax.set_ylabel("Revenue")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


def category_performance(cat: pd.DataFrame):
    cat = cat.sort_values("Revenue")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    axes[0].barh(cat.index, cat["Revenue"], color=PRIMARY, height=0.6)
    for i, (v, s) in enumerate(zip(cat["Revenue"], cat["Share_Pct"])):
        axes[0].text(v + 8000, i, f"RM{v/1000:,.0f}k  ({s:.1f}%)", va="center", fontsize=9, color=TEXT)
    axes[0].xaxis.set_major_formatter(RM)
    axes[0].set_xlim(0, cat["Revenue"].max() * 1.3)
    axes[0].set_title("Revenue by category", pad=22)
    _subtitle(axes[0], "Small Electronics drives one third of sales")

    axes[1].barh(cat.index, cat["Margin_Pct"], color=ACCENT, height=0.6)
    for i, v in enumerate(cat["Margin_Pct"]):
        axes[1].text(v + 0.6, i, f"{v:.1f}%", va="center", fontsize=9, color=TEXT)
    axes[1].set_yticklabels([])
    axes[1].set_xlim(0, cat["Margin_Pct"].max() * 1.2)
    axes[1].xaxis.set_major_formatter(mtick.PercentFormatter())
    axes[1].set_title("Gross margin by category", pad=22)
    _subtitle(axes[1], "…but accessories earn the richest margins")
    for ax in axes:
        ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def rating_distribution(df: pd.DataFrame):
    rc = df["Rating"].dropna().astype(int).value_counts().sort_index()
    mean = df["Rating"].mean()
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(rc.index.astype(str), rc.values, color=PRIMARY, width=0.6)
    for b, v in zip(bars, rc.values):
        ax.text(b.get_x() + b.get_width() / 2, v + rc.max() * 0.015, f"{v:,}\n{v/rc.sum()*100:.1f}%",
                ha="center", va="bottom", fontsize=9, color=TEXT, zorder=4,
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
    # Bars sit at x positions 0..4, so rating r is drawn at r - 1.
    ax.axvline(mean - 1, color=ACCENT, linestyle="--", linewidth=2, zorder=3,
               label=f"Average rating = {mean:.2f}")
    ax.set_ylim(0, rc.max() * 1.18)
    ax.set_title("Customer rating distribution", pad=22)
    _subtitle(ax, f"{df['Rating'].notna().mean()*100:.0f}% of orders were rated; most customers give 4–5 stars")
    ax.set_xlabel("Rating (1 = worst, 5 = best)"); ax.set_ylabel("Rated orders")
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:,.0f}"))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Additional visualisations
# --------------------------------------------------------------------------- #
def seasonality_heatmap(df: pd.DataFrame):
    piv = df.pivot_table(index="Month", columns="Business_Year", values="Total_Amount", aggfunc="sum")
    piv.index = MONTH_ABBR
    piv.columns = [f"Year {c}" for c in piv.columns]
    fig, ax = plt.subplots(figsize=(9, 6.5))
    sns.heatmap(piv / 1000, annot=True, fmt=".0f", cmap=SEQ_CMAP, linewidths=2, linecolor=SURFACE,
                cbar_kws={"label": "Revenue (RM thousand)"}, ax=ax)
    ax.set_title("Revenue by month and business year (RM thousand)", pad=22)
    _subtitle(ax, "October–December is consistently the strongest quarter")
    ax.set_xlabel("Business year (Oct–Sep)"); ax.set_ylabel("")
    fig.tight_layout()
    return fig


def hour_weekday_heatmap(df: pd.DataFrame):
    hw = df.pivot_table(index="Day_of_Week", columns="Hour", values="Transaction_ID",
                        aggfunc="count").reindex(WEEKDAYS)
    fig, ax = plt.subplots(figsize=(13, 4.8))
    sns.heatmap(hw, cmap=SEQ_CMAP, linewidths=1, linecolor=SURFACE, cbar_kws={"label": "Orders"}, ax=ax)
    ax.set_title("When customers order: hour of day × weekday", pad=22)
    _subtitle(ax, "Evening (19:00–23:00) is prime time every day of the week")
    ax.set_xlabel("Hour of day"); ax.set_ylabel("")
    fig.tight_layout()
    return fig


def payment_mix(df: pd.DataFrame):
    pm = pd.crosstab(df["Business_Year"], df["Payment_Method"], normalize="index") * 100
    pm = pm[pm.mean().sort_values(ascending=False).index]
    pm.index = [f"Year {i}" for i in pm.index]
    fig, ax = plt.subplots(figsize=(11, 5))
    pm.plot(kind="bar", stacked=True, width=0.6, ax=ax, color=PALETTE[: pm.shape[1]],
            edgecolor=SURFACE, linewidth=1.5)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 100)
    ax.set_title("Payment method share by business year", pad=22)
    _subtitle(ax, "E-wallets keep gaining share at the expense of cash on delivery")
    ax.set_xlabel(""); ax.set_ylabel("Share of orders")
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="x", visible=False)
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", title="Payment method")
    fig.tight_layout()
    return fig


def delivery_vs_rating(df: pd.DataFrame):
    """Two aligned panels (shared x) instead of a dual-axis chart."""
    q = df.groupby("Quarter").agg(
        on_time=("Delivery_Status", lambda s: (s == "On-time").mean() * 100),
        rating=("Rating", "mean"),
    )
    xq = q.index.to_timestamp()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True)
    a1.plot(xq, q["on_time"], color=PRIMARY, marker="o", markersize=5)
    a1.yaxis.set_major_formatter(mtick.PercentFormatter())
    a1.set_title("On-time delivery rate by quarter", pad=22)
    _subtitle(a1, "Logistics improved steadily — and ratings followed")
    a2.plot(xq, q["rating"], color=ACCENT, marker="s", markersize=5)
    a2.set_title("Average customer rating by quarter")
    a2.set_ylabel("Rating (1–5)")
    fig.tight_layout()
    return fig


def late_delivery_impact(df: pd.DataFrame):
    r = df.groupby("Delivery_Status")["Rating"].mean().reindex(["On-time", "Late"])
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(r.index[::-1], r.values[::-1], color=[ACCENT, PRIMARY], height=0.5)
    for b, v in zip(bars, r.values[::-1]):
        ax.text(v + 0.05, b.get_y() + b.get_height() / 2, f"{v:.2f} ★", va="center", color=TEXT)
    ax.set_xlim(0, 5)
    ax.set_title("Average rating by delivery status", pad=22)
    _subtitle(ax, f"A late parcel costs ~{r['On-time'] - r['Late']:.1f} stars")
    ax.set_xlabel("Average rating"); ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# Machine learning
# --------------------------------------------------------------------------- #
def actual_vs_predicted(monthly: pd.DataFrame, comparison):
    preds = comparison.predictions
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly["MonthStart"], monthly["Revenue"], color=MUTED, marker="o", markersize=3,
            linewidth=1.5, label="Actual revenue")
    for color, name in zip([PRIMARY, ACCENT], ["Linear Regression", "Polynomial Regression (degree 2)"]):
        ax.plot(preds["MonthStart"], preds[name], color=color, marker="o", markersize=5, label=name)
    ax.axvline(monthly.iloc[comparison.split_index]["MonthStart"], color=TEXT_SECONDARY, linestyle="--",
               linewidth=1)
    ax.text(monthly.iloc[comparison.split_index]["MonthStart"], ax.get_ylim()[1], " test period →",
            va="top", color=TEXT_SECONDARY, fontsize=9)
    ax.yaxis.set_major_formatter(RM)
    ax.set_title("Actual vs predicted monthly revenue (chronological 80/20 split)", pad=22)
    _subtitle(ax, f"Best model on hold-out: {comparison.best_name}")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


def residuals(comparison):
    p = comparison.predictions
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.scatter(p[comparison.best_name], p["Residual"], s=60, color=PRIMARY, edgecolor=SURFACE, linewidth=1.5)
    ax.axhline(0, color=TEXT_SECONDARY, linestyle="--", linewidth=1)
    ax.xaxis.set_major_formatter(RM); ax.yaxis.set_major_formatter(RM)
    ax.set_title(f"Residuals — {comparison.best_name}", pad=22)
    _subtitle(ax, "Residuals scatter around zero with no strong pattern")
    ax.set_xlabel("Predicted revenue"); ax.set_ylabel("Actual − predicted")
    fig.tight_layout()
    return fig


def forecast_chart(monthly: pd.DataFrame, forecast: pd.DataFrame, model_name: str):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(monthly["MonthStart"], monthly["Revenue"], color=PRIMARY, marker="o", markersize=3,
            label="Historical revenue")
    bridge = pd.concat([monthly[["MonthStart", "Revenue"]].tail(1).rename(columns={"Revenue": "Forecast_Revenue"}),
                        forecast])
    ax.plot(bridge["MonthStart"], bridge["Forecast_Revenue"], color=ACCENT, marker="o", markersize=5,
            linestyle="--", label=f"12-month forecast")
    ax.axvspan(forecast["MonthStart"].min(), forecast["MonthStart"].max(), color=ACCENT, alpha=0.06)
    ax.yaxis.set_major_formatter(RM)
    ax.set_title("Next 12 months revenue forecast", pad=22)
    _subtitle(ax, f"{model_name} · forecast total RM{forecast['Forecast_Revenue'].sum():,.0f}")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig
