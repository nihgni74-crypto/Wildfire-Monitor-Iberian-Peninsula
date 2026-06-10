"""
Charts Builder
--------------
All Plotly charts used in the Streamlit dashboard.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ──────────────────────────────────────────────────────────────────
# SHARED THEME
# ──────────────────────────────────────────────────────────────────

DARK_BG    = "#0B0F1A"
CARD_BG    = "#131929"
ACCENT     = "#FF6B35"
ACCENT2    = "#FF9A3C"
GRID_COLOR = "rgba(255,255,255,0.06)"
TEXT_COLOR = "#E8EAF0"

BASE_LAYOUT = dict(
    paper_bgcolor=DARK_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT_COLOR, size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    xaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, linecolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
)

# Layout without legend (for subplots that set legend separately)
BASE_LAYOUT_NO_LEGEND = {k: v for k, v in BASE_LAYOUT.items() if k != "legend"}

INTENSITY_PALETTE = {
    "Very Low": "#FFFF00",
    "Low":      "#FFA500",
    "Moderate": "#FF4500",
    "High":     "#CC0000",
    "Extreme":  "#800080",
}

INTENSITY_ORDER = ["Very Low", "Low", "Moderate", "High", "Extreme"]


# ──────────────────────────────────────────────────────────────────
# 1. FIRES PER DAY – Bar
# ──────────────────────────────────────────────────────────────────

def fires_per_day_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty or "date_str" not in df.columns:
        return _empty_fig("No data")

    daily = df.groupby("date_str").size().reset_index(name="count")
    daily = daily.sort_values("date_str")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["date_str"],
        y=daily["count"],
        marker=dict(
            color=daily["count"],
            colorscale=[[0, "#FF6B35"], [0.5, "#FF4500"], [1, "#800080"]],
            line=dict(width=0),
        ),
        hovertemplate="<b>%{x}</b><br>🔥 %{y} hotspots<extra></extra>",
        text=daily["count"],
        textposition="outside",
        textfont=dict(size=10, color=TEXT_COLOR),
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="🔥 Daily Hotspot Count", font=dict(size=14, color=ACCENT2)),
        xaxis_title="Date",
        yaxis_title="Hotspots",
        bargap=0.3,
    )
    return fig


# ──────────────────────────────────────────────────────────────────
# 2. FRP DISTRIBUTION – Histogram
# ──────────────────────────────────────────────────────────────────

def frp_histogram(df: pd.DataFrame) -> go.Figure:
    if df.empty or "frp" not in df.columns:
        return _empty_fig("No FRP data")

    frp = df["frp"].dropna()

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=frp,
        nbinsx=30,
        marker=dict(
            color=frp,
            colorscale="YlOrRd",
            line=dict(width=0.3, color=DARK_BG),
        ),
        hovertemplate="FRP: %{x:.1f} MW<br>Count: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="📊 FRP Distribution (MW)", font=dict(size=14, color=ACCENT2)),
        xaxis_title="Fire Radiative Power (MW)",
        yaxis_title="Count",
        bargap=0.05,
    )
    return fig


# ──────────────────────────────────────────────────────────────────
# 3. INTENSITY PIE CHART
# ──────────────────────────────────────────────────────────────────

def intensity_donut(df: pd.DataFrame) -> go.Figure:
    if df.empty or "intensity" not in df.columns:
        return _empty_fig("No intensity data")

    counts = (
        df["intensity"]
        .value_counts()
        .reindex(INTENSITY_ORDER, fill_value=0)
    )
    active = counts[counts > 0]

    fig = go.Figure(go.Pie(
        labels=active.index,
        values=active.values,
        hole=0.55,
        marker=dict(
            colors=[INTENSITY_PALETTE.get(k, "#888") for k in active.index],
            line=dict(color=DARK_BG, width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>%{value} hotspots (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="🍩 Intensity Distribution", font=dict(size=14, color=ACCENT2)),
        showlegend=False,
        annotations=[dict(
            text=f"<b>{len(df)}</b><br><span style='font-size:9px'>total</span>",
            x=0.5, y=0.5, font=dict(size=16, color=TEXT_COLOR),
            showarrow=False,
        )],
    )
    return fig


# ──────────────────────────────────────────────────────────────────
# 4. FRP SCATTER (lat vs lon coloured by FRP)
# ──────────────────────────────────────────────────────────────────

def frp_scatter_map(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty_fig("No data")

    fig = go.Figure(go.Scattermapbox(
        lat=df["latitude"],
        lon=df["longitude"],
        mode="markers",
        marker=dict(
            size=df.get("marker_size", pd.Series([8] * len(df))).clip(4, 25),
            color=df["frp"].fillna(0),
            colorscale="YlOrRd",
            colorbar=dict(
                title="FRP (MW)",
                thickness=12,
                len=0.6,
                bgcolor="rgba(0,0,0,0)",
                tickfont=dict(color=TEXT_COLOR),
                titlefont=dict(color=TEXT_COLOR),
            ),
            opacity=0.85,
        ),
        hovertemplate=(
            "<b>🔥 Fire Hotspot</b><br>"
            "Lat: %{lat:.4f}  Lon: %{lon:.4f}<br>"
            "FRP: %{marker.color:.1f} MW<extra></extra>"
        ),
    ))
    fig.update_layout(
        paper_bgcolor=DARK_BG,
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=39.5, lon=-4.0),
            zoom=5,
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        title=dict(text="🗺️ Scatter Map (FRP)", font=dict(size=14, color=ACCENT2)),
        height=400,
    )
    return fig


# ──────────────────────────────────────────────────────────────────
# 5. HOURLY PATTERN – Polar / Rose Chart
# ──────────────────────────────────────────────────────────────────

def hourly_polar(df: pd.DataFrame) -> go.Figure:
    if df.empty or "acq_time" not in df.columns:
        return _empty_fig("No time data")

    hours = pd.to_numeric(
        df["acq_time"].astype(str).str.zfill(4).str[:2],
        errors="coerce"
    ).dropna().astype(int)

    hour_counts = hours.value_counts().sort_index().reindex(range(24), fill_value=0)

    fig = go.Figure(go.Barpolar(
        r=hour_counts.values,
        theta=hour_counts.index * 15,
        width=[15] * 24,
        marker=dict(
            color=hour_counts.values,
            colorscale="Inferno",
            line=dict(color=DARK_BG, width=0.5),
        ),
        hovertemplate="Hour %{theta:.0f}°→ %{r} detections<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        polar=dict(
            bgcolor=CARD_BG,
            radialaxis=dict(showticklabels=False, gridcolor=GRID_COLOR),
            angularaxis=dict(
                tickvals=list(range(0, 360, 30)),
                ticktext=[f"{h:02d}h" for h in range(0, 24, 2)],
                direction="clockwise",
                gridcolor=GRID_COLOR,
                tickfont=dict(color=TEXT_COLOR, size=10),
            ),
        ),
        font=dict(color=TEXT_COLOR),
        margin=dict(l=30, r=30, t=40, b=30),
        title=dict(text="🕐 Hourly Detection Pattern", font=dict(size=14, color=ACCENT2)),
    )
    return fig


# ──────────────────────────────────────────────────────────────────
# 6. FRP TIME SERIES
# ──────────────────────────────────────────────────────────────────

def frp_time_series(df: pd.DataFrame) -> go.Figure:
    if df.empty or "acq_date" not in df.columns:
        return _empty_fig("No data")

    ts = (
        df.groupby("date_str")["frp"]
        .agg(["mean", "max", "count"])
        .reset_index()
        .sort_values("date_str")
    )

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=("Mean & Max FRP (MW)", "Daily Hotspot Count"),
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4],
    )

    # Mean FRP area
    fig.add_trace(go.Scatter(
        x=ts["date_str"], y=ts["mean"],
        mode="lines+markers",
        name="Mean FRP",
        line=dict(color=ACCENT2, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(255,154,60,0.15)",
        hovertemplate="Mean FRP: %{y:.1f} MW<extra></extra>",
    ), row=1, col=1)

    # Max FRP line
    fig.add_trace(go.Scatter(
        x=ts["date_str"], y=ts["max"],
        mode="lines+markers",
        name="Max FRP",
        line=dict(color="#CC0000", width=2, dash="dot"),
        hovertemplate="Max FRP: %{y:.1f} MW<extra></extra>",
    ), row=1, col=1)

    # Count bars
    fig.add_trace(go.Bar(
        x=ts["date_str"], y=ts["count"],
        name="Count",
        marker=dict(color=ACCENT, opacity=0.75),
        hovertemplate="Hotspots: %{y}<extra></extra>",
    ), row=2, col=1)

    fig.update_layout(
        **BASE_LAYOUT_NO_LEGEND,
        title=dict(text="FRP Trend Over Time", font=dict(size=14, color=ACCENT2)),
        height=420,
        showlegend=True,
    )
    fig.update_layout(
        legend=dict(orientation="h", y=1.05, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR)
    return fig


# ──────────────────────────────────────────────────────────────────
# 7. TOP 10 HOTTEST FIRES TABLE
# ──────────────────────────────────────────────────────────────────

def top_fires_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return top-10 fires by FRP as a formatted DataFrame."""
    cols = [c for c in ["date_str", "latitude", "longitude", "frp",
                         "brightness", "intensity", "confidence", "satellite"]
            if c in df.columns]
    top = df.nlargest(10, "frp")[cols].copy()

    rename = {
        "date_str":   "Date",
        "latitude":   "Latitude",
        "longitude":  "Longitude",
        "frp":        "FRP (MW)",
        "brightness": "Brightness (K)",
        "intensity":  "Intensity",
        "confidence": "Confidence",
        "satellite":  "Satellite",
    }
    top = top.rename(columns={k: v for k, v in rename.items() if k in top.columns})
    return top.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────
# UTILITY
# ──────────────────────────────────────────────────────────────────

def _empty_fig(msg: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg,
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=16, color="#888"),
    )
    fig.update_layout(**BASE_LAYOUT, height=250)
    return fig
