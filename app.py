"""
Wildfire Monitor – Iberian Peninsula
Real-Time Active Fire Dashboard using NASA FIRMS API
-----------------------------------------------------
Author : Niloofar
Data   : NASA FIRMS (VIIRS / MODIS) – https://firms.modaps.eosdis.nasa.gov
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os

from data_fetcher import fetch_fire_data, compute_stats, REGIONS, SENSORS
from map_builder import build_map
from charts import (
    fires_per_day_bar,
    frp_histogram,
    intensity_donut,
    frp_time_series,
    hourly_polar,
    top_fires_table,
)
from forecasting import forecast_hotspots
from streamlit_folium import st_folium

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Wildfire Monitor – Iberian Peninsula",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help":    "https://firms.modaps.eosdis.nasa.gov/api/",
        "Report a bug": None,
        "About":       "Real-time wildfire monitoring dashboard powered by NASA FIRMS & Streamlit.",
    },
)

# ══════════════════════════════════════════════════════════════════
# CUSTOM CSS  – Dark fire theme
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<style>
  /* ── Google Fonts ─────────────────────────────────────────── */
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Open+Sans:wght@400;600;700&display=swap');

  /* ── Global ───────────────────────────────────────────────── */
  html, body, [class*="css"] {
    font-family: 'Roboto', 'Open Sans', sans-serif;
    background-color: #080C14;
    color: #E8EAF0;
  }

  /* ── Sidebar ──────────────────────────────────────────────── */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1422 0%, #080C14 100%);
    border-right: 1px solid rgba(255,107,53,0.15);
  }
  section[data-testid="stSidebar"] * { color: #E8EAF0 !important; }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stSlider label,
  section[data-testid="stSidebar"] .stTextInput label {
    font-weight: 600; font-size: 13px; letter-spacing: .3px;
  }

  /* ── Metric cards ─────────────────────────────────────────── */
  div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #131929 0%, #0D1422 100%);
    border: 1px solid rgba(255,107,53,0.2);
    border-radius: 16px;
    padding: 18px 20px !important;
    box-shadow: 0 4px 24px rgba(255,107,53,0.08);
    transition: transform .2s, box-shadow .2s;
  }
  div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(255,107,53,0.18);
  }
  div[data-testid="metric-container"] label { color: #8892A4 !important; font-size: 12px !important; }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 28px !important; font-weight: 800 !important; color: #FF9A3C !important;
  }

  /* ── Buttons ──────────────────────────────────────────────── */
  div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #FF6B35 0%, #FF4500 100%) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important;
    padding: 10px 24px !important; width: 100%;
    transition: all .2s; letter-spacing: .3px;
    box-shadow: 0 4px 16px rgba(255,107,53,0.35) !important;
  }
  div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 22px rgba(255,107,53,0.55) !important;
  }

  /* ── Section header ───────────────────────────────────────── */
  .section-title {
    font-size: 17px; font-weight: 700; color: #FF9A3C;
    margin: 24px 0 12px; letter-spacing: .3px;
    display: flex; align-items: center; gap: 8px;
  }
  .section-title::after {
    content: ""; flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(255,154,60,.3), transparent);
  }

  /* ── Hero banner ──────────────────────────────────────────── */
  .hero-banner {
    background: linear-gradient(135deg, #1A0A00 0%, #0D1422 50%, #0A0014 100%);
    border: 1px solid rgba(255,107,53,0.25);
    border-radius: 20px; padding: 28px 36px; margin-bottom: 24px;
    position: relative; overflow: hidden;
  }
  .hero-banner::before {
    content: ""; position: absolute; top: -40px; right: -40px;
    width: 200px; height: 200px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,107,53,.15) 0%, transparent 70%);
  }
  .hero-title {
    font-size: 32px; font-weight: 800; line-height: 1.2;
    background: linear-gradient(135deg, #FF9A3C 0%, #FF6B35 50%, #CC0000 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .hero-subtitle {
    font-size: 14px; color: #8892A4; margin-top: 8px; font-weight: 400;
  }
  .hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(255,107,53,0.12); border: 1px solid rgba(255,107,53,0.3);
    border-radius: 20px; padding: 4px 14px;
    font-size: 12px; font-weight: 600; color: #FF9A3C;
    margin-top: 12px;
  }
  .live-dot {
    width: 8px; height: 8px; border-radius: 50%; background: #FF6B35;
    animation: pulse 1.5s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: .5; transform: scale(1.4); }
  }

  /* ── Tabs ─────────────────────────────────────────────────── */
  button[data-baseweb="tab"] {
    background: transparent !important; border: none !important;
    color: #8892A4 !important; font-weight: 600 !important; font-size: 13px !important;
    padding: 10px 18px !important; border-radius: 10px 10px 0 0 !important;
    transition: all .2s;
  }
  button[data-baseweb="tab"]:hover { color: #FF9A3C !important; }
  button[data-baseweb="tab"][aria-selected="true"] {
    color: #FF9A3C !important;
    border-bottom: 2px solid #FF6B35 !important;
  }

  /* ── Info / warning blocks ────────────────────────────────── */
  div[data-testid="stAlert"] {
    background: rgba(255,107,53,0.08) !important;
    border: 1px solid rgba(255,107,53,0.25) !important;
    border-radius: 12px !important;
    color: #E8EAF0 !important;
  }

  /* ── Scrollbar ────────────────────────────────────────────── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #080C14; }
  ::-webkit-scrollbar-thumb { background: #FF6B35; border-radius: 3px; }

  /* ── Folium map container ─────────────────────────────────── */
  .folium-map { border-radius: 16px; overflow: hidden; }

  /* ── Dataframe ────────────────────────────────────────────── */
  div[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,107,53,0.15) !important;
    border-radius: 12px !important; overflow: hidden !important;
  }

  /* ── Hide Streamlit branding ──────────────────────────────── */
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:16px 0 8px">
      <div style="font-size:16px;font-weight:800;color:#FF9A3C;letter-spacing:.5px">
        WILDFIRE MONITOR
      </div>
      <div style="font-size:11px;color:#8892A4;margin-top:4px">
        NASA FIRMS • Real-Time Data
      </div>
    </div>
    <hr style="border-color:rgba(255,107,53,0.2);margin:12px 0">
    """, unsafe_allow_html=True)

    st.markdown("#### Region")
    region_key = st.selectbox(
        "Select Region",
        options=list(REGIONS.keys()),
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("#### Sensor")
    sensor_key = st.selectbox(
        "Select Sensor",
        options=list(SENSORS.keys()),
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("#### Days of Data")
    days = st.slider("Days back", min_value=1, max_value=10, value=7, step=1)

    st.markdown("#### Map Style")
    map_style = st.radio(
        "Map style",
        ["Heatmap", "Markers", "Clusters"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("#### Basemap")
    basemap = st.selectbox(
        "Basemap",
        ["CartoDB Dark", "CartoDB Light", "OpenStreetMap", "Esri Satellite"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("#### NASA API Key")
    api_key_input = st.text_input(
        "API Key (optional)",
        value="",
        type="password",
        placeholder="Leave blank for demo data",
        label_visibility="collapsed",
        help="Get a free key at https://firms.modaps.eosdis.nasa.gov/api/area/",
    )
    st.markdown(
        "<div style='font-size:11px;color:#8892A4;margin-top:4px'>"
        "🆓 <a href='https://firms.modaps.eosdis.nasa.gov/api/area/' "
        "style='color:#FF9A3C' target='_blank'>Get free API key</a>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    fetch_btn = st.button("Fetch / Refresh Data", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:11px;color:#8892A4;line-height:1.6">
      <b style="color:#FF9A3C">Data Sources</b><br>
      • NASA FIRMS VIIRS & MODIS<br>
      • Near-real-time (≤3h lag)<br>
      • Resolution: 375m (VIIRS)<br><br>
      <b style="color:#FF9A3C">Built with</b><br>
      Python · Streamlit<br>
      Folium · Plotly<br>
      NASA FIRMS API
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SESSION STATE – cache the dataframe
# ══════════════════════════════════════════════════════════════════

if "df" not in st.session_state:
    st.session_state.df = None
if "last_fetched" not in st.session_state:
    st.session_state.last_fetched = None
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None


# ══════════════════════════════════════════════════════════════════
# DATA FETCH
# ══════════════════════════════════════════════════════════════════

# Auto-load on first visit or manual refresh
if st.session_state.df is None or fetch_btn:
    with st.spinner("Fetching fire data from NASA FIRMS…"):
        key = api_key_input.strip() if api_key_input.strip() else None
        df = fetch_fire_data(
            region_key=region_key,
            sensor_key=sensor_key,
            days=days,
            api_key=key,
        )
    st.session_state.df = df
    st.session_state.last_fetched = datetime.now()

df = st.session_state.df


# ══════════════════════════════════════════════════════════════════
# HERO BANNER
# ══════════════════════════════════════════════════════════════════

is_demo = "NASA FIRMS API" not in st.session_state.get("source", "demo")
last_t  = st.session_state.last_fetched
last_str = last_t.strftime("%d %b %Y  %H:%M:%S UTC") if last_t else "—"

st.markdown(f"""
<div class="hero-banner">
  <div class="hero-title">Wildfire Monitor – Iberian Peninsula</div>
  <div class="hero-subtitle">
    Real-time active fire detection powered by NASA FIRMS satellite data
    (VIIRS 375m · MODIS 1km)
  </div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:14px">
    <div class="hero-badge"><span class="live-dot"></span> LIVE DATA</div>
    <div class="hero-badge">{sensor_key.split("(")[0].strip()}</div>
    <div class="hero-badge">{region_key}</div>
    <div class="hero-badge">Last {days} days</div>
    <div class="hero-badge">Updated: {last_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Demo data warning
if not api_key_input.strip():
    st.info(
        "Demo Mode – Showing sample data. "
        "Enter your free [NASA FIRMS API key](https://firms.modaps.eosdis.nasa.gov/api/area/) "
        "in the sidebar to load real satellite data."
    )


# ══════════════════════════════════════════════════════════════════
# KPI METRICS ROW
# ══════════════════════════════════════════════════════════════════

stats = compute_stats(df)

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric("Total Hotspots",   f"{stats['total']:,}")
with col2:
    st.metric("Mean FRP",         f"{stats['frp_mean']} MW")
with col3:
    st.metric("Peak FRP",        f"{stats['frp_max']} MW")
with col4:
    st.metric("High/Extreme",     f"{stats['high_pct']}%")
with col5:
    st.metric("Days Covered",     f"{stats['days_span']}")
with col6:
    st.metric("Nighttime",        f"{stats['night_pct']}%")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# DATE FILTER SLIDER
# ══════════════════════════════════════════════════════════════════

if "date_str" in df.columns and df["date_str"].nunique() > 1:
    available_dates = sorted(df["date_str"].unique())
    all_label = "All Dates"
    date_options = [all_label] + available_dates

    st.markdown('<div class="section-title">Filter by Date</div>', unsafe_allow_html=True)
    selected_date_option = st.select_slider(
        "Date",
        options=date_options,
        value=all_label,
        label_visibility="collapsed",
    )
    selected_date = None if selected_date_option == all_label else selected_date_option
else:
    selected_date = None

# Filtered df for map
map_df = df if selected_date is None else df[df["date_str"] == selected_date]

st.markdown(
    f"<div style='font-size:12px;color:#8892A4;margin-bottom:16px'>"
    f"Showing <b style='color:#FF9A3C'>{len(map_df):,}</b> hotspots"
    f"{' on ' + selected_date if selected_date else ' (all dates)'}.</div>",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════

tab_map, tab_charts, tab_forecast, tab_data, tab_about = st.tabs([
    "Interactive Map",
    "Analytics",
    "Predictive Analytics",
    "Raw Data",
    "About",
])


# ─────────────────────────────────────────
# TAB 1 – MAP
# ─────────────────────────────────────────
with tab_map:
    st.markdown('<div class="section-title">Interactive Fire Map</div>', unsafe_allow_html=True)

    if map_df.empty:
        st.warning("No hotspots found for the selected filters.")
    else:
        with st.spinner("Rendering map…"):
            fmap = build_map(
                df=map_df,
                map_style=map_style,
                basemap=basemap,
                selected_date=None,  # already pre-filtered
            )
            st_folium(fmap, height=560, use_container_width=True)

    st.markdown(
        "<div style='font-size:11px;color:#8892A4;margin-top:8px'>"
        "💡 Click any hotspot marker for details. Use ⛶ top-right for fullscreen. "
        "FRP = Fire Radiative Power (energy released per second)."
        "</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────
# TAB 2 – ANALYTICS
# ─────────────────────────────────────────
with tab_charts:
    st.markdown('<div class="section-title">Fire Analytics & Statistics</div>', unsafe_allow_html=True)

    # Row 1: Bar + Donut
    r1c1, r1c2 = st.columns([3, 2])
    with r1c1:
        st.plotly_chart(fires_per_day_bar(df), use_container_width=True)
    with r1c2:
        st.plotly_chart(intensity_donut(df), use_container_width=True)

    # Row 2: Time series (full width)
    st.plotly_chart(frp_time_series(df), use_container_width=True)

    # Row 3: Histogram + Polar
    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.plotly_chart(frp_histogram(df), use_container_width=True)
    with r3c2:
        st.plotly_chart(hourly_polar(df), use_container_width=True)

    # Top 10 table
    st.markdown('<div class="section-title">Top 10 Most Intense Fires</div>', unsafe_allow_html=True)
    top_df = top_fires_table(df)

    # Style the table
    def highlight_intensity(val):
        colors = {
            "Extreme":  "background: rgba(128,0,128,0.25); color: #E070E0",
            "High":     "background: rgba(204,0,0,0.25);   color: #FF6060",
            "Moderate": "background: rgba(255,69,0,0.2);   color: #FF8C60",
            "Low":      "background: rgba(255,165,0,0.15); color: #FFB84D",
            "Very Low": "background: rgba(255,255,0,0.1);  color: #DDDD44",
        }
        return colors.get(val, "")

    if "Intensity" in top_df.columns:
        styled = top_df.style.map(
            highlight_intensity, subset=["Intensity"]
        ).format({"FRP (MW)": "{:.1f}", "Latitude": "{:.4f}", "Longitude": "{:.4f}"})
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.dataframe(top_df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────
# TAB 2.5 – FORECASTING
# ─────────────────────────────────────────
with tab_forecast:
    st.markdown('<div class="section-title">Predictive Hotspot Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:13px;color:#8892A4;margin-bottom:16px;max-width:800px;line-height:1.6'>"
        "Using Facebook's <b>Prophet</b> time-series forecasting algorithm, this module predicts the daily fire "
        "hotspot counts for the next 90 days. "
        "<i>Note: If the loaded dataset covers less than 30 days, the model automatically simulates historical seasonal data "
        "to demonstrate long-term forecasting capabilities.</i>"
        "</div>",
        unsafe_allow_html=True,
    )
    
    with st.spinner("Running forecasting model (Prophet)…"):
        forecast_fig = forecast_hotspots(df, days_to_predict=90)
        st.plotly_chart(forecast_fig, use_container_width=True)

# ─────────────────────────────────────────
# TAB 3 – RAW DATA
# ─────────────────────────────────────────
with tab_data:
    st.markdown('<div class="section-title">Raw Fire Data</div>', unsafe_allow_html=True)

    # Filter controls
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        intensity_filter = st.multiselect(
            "Intensity",
            options=["Very Low", "Low", "Moderate", "High", "Extreme"],
            default=["Moderate", "High", "Extreme"],
        )
    with fc2:
        min_frp = st.number_input("Min FRP (MW)", value=0.0, step=5.0)
    with fc3:
        if "daynight" in df.columns:
            dn_filter = st.multiselect(
                "Day/Night",
                options=["D", "N"],
                default=["D", "N"],
                format_func=lambda x: "Day" if x == "D" else "Night",
            )
        else:
            dn_filter = ["D", "N"]

    filtered = df.copy()
    if intensity_filter and "intensity" in filtered.columns:
        filtered = filtered[filtered["intensity"].isin(intensity_filter)]
    if "frp" in filtered.columns:
        filtered = filtered[filtered["frp"] >= min_frp]
    if dn_filter and "daynight" in filtered.columns:
        filtered = filtered[filtered["daynight"].isin(dn_filter)]

    st.markdown(
        f"<div style='font-size:12px;color:#8892A4;margin-bottom:8px'>"
        f"Showing <b style='color:#FF9A3C'>{len(filtered):,}</b> of {len(df):,} records</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(filtered, use_container_width=True, height=480)

    # Download button
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"wildfire_iberia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ─────────────────────────────────────────
# TAB 4 – ABOUT
# ─────────────────────────────────────────
with tab_about:
    st.markdown("""
    <div style="max-width:760px">
    """, unsafe_allow_html=True)

    st.markdown("## 🔥 Wildfire Monitor – Technical Overview")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        ### 📡 Data Sources
        | Source | Details |
        |--------|---------|
        | **NASA FIRMS** | Free near-real-time active fire API |
        | **VIIRS SNPP** | 375m resolution, polar orbit |
        | **VIIRS NOAA-20** | Latest satellite, ≤3h lag |
        | **MODIS** | 1km, Terra & Aqua satellites |

        ### 🔬 Key Metrics Explained
        | Metric | Meaning |
        |--------|---------|
        | **FRP** | Fire Radiative Power (MW) – energy released |
        | **Brightness** | Radiometric temperature (Kelvin) |
        | **Confidence** | Detection reliability (High/Nominal/Low) |
        """)
    with col_b:
        st.markdown("""
        ### 🛠️ Technology Stack
        | Tool | Purpose |
        |------|---------|
        | **Python 3.11** | Core language |
        | **Streamlit** | Web dashboard framework |
        | **Folium** | Interactive Leaflet.js maps |
        | **Plotly** | Dynamic charts |
        | **Pandas** | Data manipulation |
        | **NASA FIRMS API** | Satellite fire data |

        ### 🌍 Coverage
        - **Spain & Portugal** – Default region
        - **Mediterranean Basin** – Optional wider view
        - **Europe** – Broad continental view
        """)

    st.markdown("""
    ### 🔥 Intensity Classification
    | Class | FRP Range | Description |
    |-------|-----------|-------------|
    | 🟡 Very Low | < 10 MW | Small vegetation fire |
    | 🟠 Low | 10–30 MW | Moderate vegetation |
    | 🔴 Moderate | 30–75 MW | Active forest fire |
    | 🔴 High | 75–150 MW | Large forest fire |
    | 🟣 Extreme | > 150 MW | Catastrophic megafire |

    ### ⚠️ Limitations & Notes
    - Near-real-time data has 3–12 hour lag depending on satellite overpass.
    - Cloud cover and smoke can reduce detection accuracy.
    - VIIRS 375m is significantly more accurate than MODIS 1km for small fires.
    - Demo data is generated synthetically to illustrate dashboard features.

    ---
    *Built by Niloofar · GIS & Environmental Data Analyst · 2026*
    *Data: [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov) | Hosted: [Streamlit Cloud](https://streamlit.io/cloud)*
    """)

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<div style="
  text-align:center; margin-top:48px; padding:20px;
  border-top:1px solid rgba(255,107,53,0.12);
  font-size:12px; color:#8892A4; line-height:1.8
">
  <b style="color:#FF9A3C">Wildfire Monitor</b> &nbsp;|&nbsp;
  Data: <a href="https://firms.modaps.eosdis.nasa.gov" style="color:#FF9A3C" target="_blank">NASA FIRMS</a>
  &nbsp;|&nbsp;
  VIIRS / MODIS Satellite Detection
  &nbsp;|&nbsp;
  Built with Python & Streamlit
  <br>
  <span style="font-size:10px;color:#4A5568">
    This tool is for educational and research purposes. Always consult official emergency services for real fire alerts.
  </span>
</div>
""", unsafe_allow_html=True)
