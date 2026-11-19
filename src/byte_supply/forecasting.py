"""Monthly revenue regression and forecasting."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

FEATURES = ["time_index", "month", "month_sin", "month_cos"]


def _add_time_features(frame: pd.DataFrame, start_index: int = 0) -> pd.DataFrame:
    frame = frame.copy()
    frame["time_index"] = np.arange(start_index, start_index + len(frame))
    frame["month"] = frame["MonthStart"].dt.month
    frame["year"] = frame["MonthStart"].dt.year
    frame["month_sin"] = np.sin(2 * np.pi * frame["month"] / 12)
    frame["month_cos"] = np.cos(2 * np.pi * frame["month"] / 12)
    return frame


def build_monthly_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate transactions to monthly revenue/orders with time features."""
    monthly = (
        df.groupby(df["Date_Time"].dt.to_period("M"))
        .agg(Revenue=("Total_Amount", "sum"), Orders=("Transaction_ID", "count"))
        .reset_index(names="MonthStart")
    )
    monthly["MonthStart"] = monthly["MonthStart"].dt.to_timestamp()
    monthly = monthly.sort_values("MonthStart").reset_index(drop=True)
    return _add_time_features(monthly)


def make_models() -> dict[str, Pipeline]:
    return {
        "Linear Regression": Pipeline(
            [("scale", StandardScaler()), ("model", LinearRegression())]
        ),
        "Polynomial Regression (degree 2)": Pipeline(
            [
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("scale", StandardScaler()),
                ("model", LinearRegression()),
            ]
        ),
    }


@dataclass
class ModelComparison:
    metrics: pd.DataFrame
    predictions: pd.DataFrame
    split_index: int
    best_name: str
    models: dict = field(repr=False)


def compare_models(monthly: pd.DataFrame, train_frac: float = 0.8) -> ModelComparison:
    """Fit each model on a chronological train split and score on the hold-out."""
    split = int(len(monthly) * train_frac)
    X, y = monthly[FEATURES], monthly["Revenue"]
    X_train, X_test, y_train, y_test = X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]

    models = make_models()
    rows = []
    preds = monthly.iloc[split:][["MonthStart", "Revenue"]].copy()
    for name, model in models.items():
        model.fit(X_train, y_train)
        p = model.predict(X_test)
        preds[name] = p
        mse = mean_squared_error(y_test, p)
        rows.append(
            {
                "Model": name,
                "MAE (RM)": mean_absolute_error(y_test, p),
                "RMSE (RM)": np.sqrt(mse),
                "MAPE (%)": np.mean(np.abs((y_test - p) / y_test)) * 100,
                "R2": r2_score(y_test, p),
            }
        )
    metrics = pd.DataFrame(rows).sort_values("RMSE (RM)").reset_index(drop=True)
    best = metrics.loc[0, "Model"]
    preds["Residual"] = preds["Revenue"] - preds[best]
    return ModelComparison(metrics, preds, split, best, models)


def forecast_next_months(monthly: pd.DataFrame, model_name: str, periods: int = 12) -> pd.DataFrame:
    """Refit ``model_name`` on all history and forecast ``periods`` months ahead."""
    model = make_models()[model_name]
    model.fit(monthly[FEATURES], monthly["Revenue"])
    future = pd.DataFrame(
        {
            "MonthStart": pd.date_range(
                monthly["MonthStart"].max() + pd.offsets.MonthBegin(1), periods=periods, freq="MS"
            )
        }
    )
    future = _add_time_features(future, start_index=len(monthly))
    future["Forecast_Revenue"] = np.maximum(model.predict(future[FEATURES]), 0)
    return future[["MonthStart", "Forecast_Revenue"]]
