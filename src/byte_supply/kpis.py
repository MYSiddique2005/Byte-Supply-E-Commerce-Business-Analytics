"""Business KPI and insight calculations."""

from __future__ import annotations

import pandas as pd


def _on_time_pct(s: pd.Series) -> float:
    return (s == "On-time").mean() * 100


def overall_kpis(df: pd.DataFrame) -> pd.Series:
    """Headline KPIs for the full five-year period."""
    rev = df["Total_Amount"].sum()
    profit = df["Gross_Profit"].sum()
    monthly = df.groupby("YearMonth")["Total_Amount"].sum()
    orders_per_customer = df.groupby("Customer_ID").size()
    return pd.Series(
        {
            "Total revenue (RM)": rev,
            "Number of orders": len(df),
            "Unique customers": df["Customer_ID"].nunique(),
            "Average order value (RM)": rev / len(df),
            "Gross profit (RM)": profit,
            "Gross margin (%)": profit / rev * 100,
            "Average rating (rated orders)": df["Rating"].mean(),
            "Rated orders (%)": df["Rating"].notna().mean() * 100,
            "On-time delivery rate (%)": _on_time_pct(df["Delivery_Status"]),
            "Stock-out rate (%)": df["Stock_Out_Flag"].mean() * 100,
            "Repeat customer rate (%)": (orders_per_customer >= 2).mean() * 100,
            "Average monthly sales growth (%)": monthly.pct_change().mean() * 100,
        }
    )


def business_year_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """KPIs per business year (October → September)."""
    by = df.groupby("Business_Year").agg(
        Orders=("Transaction_ID", "count"),
        Revenue=("Total_Amount", "sum"),
        Gross_Profit=("Gross_Profit", "sum"),
        Avg_Rating=("Rating", "mean"),
        On_Time_Pct=("Delivery_Status", _on_time_pct),
        Stock_Out_Pct=("Stock_Out_Flag", lambda s: s.mean() * 100),
    )
    by["AOV"] = by["Revenue"] / by["Orders"]
    by["Revenue_Growth_Pct"] = by["Revenue"].pct_change() * 100
    by["Margin_Pct"] = by["Gross_Profit"] / by["Revenue"] * 100
    return by


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue, profit, share and margin by product category."""
    rev = df["Total_Amount"].sum()
    cat = df.groupby("Category").agg(
        Revenue=("Total_Amount", "sum"),
        Profit=("Gross_Profit", "sum"),
        Orders=("Transaction_ID", "count"),
    )
    cat["Share_Pct"] = cat["Revenue"] / rev * 100
    cat["Margin_Pct"] = cat["Profit"] / cat["Revenue"] * 100
    return cat.sort_values("Revenue", ascending=False)


def segment_summary(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Orders, revenue, AOV and rating for any categorical column."""
    seg = df.groupby(column).agg(
        Orders=("Transaction_ID", "count"),
        Revenue=("Total_Amount", "sum"),
        Avg_Rating=("Rating", "mean"),
        On_Time_Pct=("Delivery_Status", _on_time_pct),
    )
    seg["AOV"] = seg["Revenue"] / seg["Orders"]
    seg["Share_Pct"] = seg["Revenue"] / seg["Revenue"].sum() * 100
    return seg.sort_values("Revenue", ascending=False)


def insight_metrics(df: pd.DataFrame) -> pd.Series:
    """Numbers that back the key business insights."""
    rev = df["Total_Amount"].sum()
    q4 = df[df["Month"].isin([10, 11, 12])]
    mega = df[df["Is_Mega_Sale"]]
    rest = df[~df["Is_Mega_Sale"]]
    return pd.Series(
        {
            "Q4 revenue share (%)": q4["Total_Amount"].sum() / rev * 100,
            "Mega-sale days": mega["Date"].nunique(),
            "Mega-sale gross margin (%)": mega["Gross_Profit"].sum() / mega["Total_Amount"].sum() * 100,
            "Other days gross margin (%)": rest["Gross_Profit"].sum() / rest["Total_Amount"].sum() * 100,
            "Rating when late": df.loc[df["Is_Late"], "Rating"].mean(),
            "Rating when on time": df.loc[~df["Is_Late"], "Rating"].mean(),
            "Evening orders 19:00-22:59 (%)": df["Hour"].between(19, 22).mean() * 100,
        }
    )
