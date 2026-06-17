"""
Forecasting Module
------------------
Uses Prophet to predict future wildfire hotspots based on historical and seasonal trends.
"""

import pandas as pd
import numpy as np
from prophet import Prophet
import plotly.graph_objects as go
import logging

log = logging.getLogger(__name__)

DARK_BG = "#0B0F1A"
CARD_BG = "#131929"
ACCENT = "#FF6B35"
ACCENT2 = "#FF9A3C"
GRID_COLOR = "rgba(255,255,255,0.06)"
TEXT_COLOR = "#E8EAF0"

BASE_LAYOUT = dict(
    paper_bgcolor=DARK_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family="Roboto, 'Open Sans', sans-serif", color=TEXT_COLOR, size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    xaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
)


def _generate_simulated_history(current_date: pd.Timestamp, years: int = 3) -> pd.DataFrame:
    """
    Generate simulated historical daily fire counts to enable long-term forecasting demo.
    Fires peak in July-August in the Iberian Peninsula.
    """
    np.random.seed(42)
    start_date = current_date - pd.DateOffset(years=years)
    dates = pd.date_range(start=start_date, end=current_date)
    
    # Base background fires
    base = 5 + np.random.poisson(5, len(dates))
    
    # Summer peak (July=7, August=8)
    month = dates.month
    summer_multiplier = np.where(month.isin([7, 8]), 10, np.where(month.isin([6, 9]), 4, 1))
    
    counts = base * summer_multiplier + np.random.normal(0, 5, len(dates))
    counts = np.clip(counts, 0, None).astype(int)
    
    return pd.DataFrame({"ds": dates, "y": counts})


def forecast_hotspots(df: pd.DataFrame, days_to_predict: int = 90) -> go.Figure:
    """
    Run Prophet to forecast daily fire counts.
    If the real dataset is too small (< 30 days), combines it with a simulated
    historical baseline to demonstrate seasonal forecasting.
    """
    if df.empty or "date_str" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No data available for forecasting", showarrow=False, font=dict(color=TEXT_COLOR))
        fig.update_layout(**BASE_LAYOUT)
        return fig

    # Aggregate real data
    daily = df.groupby("date_str").size().reset_index(name="count")
    daily["date_str"] = pd.to_datetime(daily["date_str"])
    daily = daily.rename(columns={"date_str": "ds", "count": "y"})
    
    # If real data is short, add simulated history to show seasonal capability
    if len(daily) < 30:
        latest_date = daily["ds"].max()
        history = _generate_simulated_history(latest_date, years=3)
        # Remove the dates from history that overlap with our real data
        history = history[history["ds"] < daily["ds"].min()]
        # Combine
        train_df = pd.concat([history, daily], ignore_index=True)
    else:
        train_df = daily.copy()

    # Fit Prophet
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    model.fit(train_df)
    
    # Predict
    future = model.make_future_dataframe(periods=days_to_predict)
    forecast = model.predict(future)
    
    # Plotting
    fig = go.Figure()

    # Historical Data
    fig.add_trace(go.Scatter(
        x=train_df["ds"], y=train_df["y"],
        mode="markers",
        name="Historical Observations",
        marker=dict(color="rgba(255, 255, 255, 0.4)", size=4),
        hovertemplate="Observed: %{y}<extra></extra>"
    ))

    # Forecast Line
    fig.add_trace(go.Scatter(
        x=forecast["ds"], y=forecast["yhat"],
        mode="lines",
        name="Forecast",
        line=dict(color=ACCENT, width=2.5),
        hovertemplate="Forecast: %{y:.0f}<extra></extra>"
    ))

    # Confidence Interval (yhat_upper, yhat_lower)
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast["ds"], forecast["ds"][::-1]]),
        y=pd.concat([forecast["yhat_upper"], forecast["yhat_lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(255, 107, 53, 0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=False,
        name="Confidence Interval"
    ))

    # Add a vertical line for "Today"
    today = daily["ds"].max()
    fig.add_vline(x=today, line_width=2, line_dash="dash", line_color=ACCENT2)
    fig.add_annotation(
        x=today, y=forecast["yhat_upper"].max() * 0.9,
        text="Today", showarrow=False, font=dict(color=ACCENT2),
        xanchor="right", xshift=-10
    )

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Predictive Analytics: 90-Day Hotspot Forecast (Prophet Model)", font=dict(size=14, color=ACCENT2)),
        xaxis_title="Date",
        yaxis_title="Daily Hotspots",
        hovermode="x unified",
        height=450,
    )
    
    # Zoom into the last 1 year + prediction by default
    start_view = today - pd.DateOffset(months=6)
    end_view = today + pd.DateOffset(days=days_to_predict)
    fig.update_xaxes(range=[start_view, end_view])

    return fig
