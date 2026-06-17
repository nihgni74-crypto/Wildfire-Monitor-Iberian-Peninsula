"""
Map Builder
-----------
Creates interactive Folium maps with fire hotspot markers,
heatmap layer, and cluster layer.
"""

import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen, MiniMap
import pandas as pd
import numpy as np


# ──────────────────────────────────────────────────────────────────
# COLOUR PALETTE (consistent with data_fetcher)
# ──────────────────────────────────────────────────────────────────

INTENSITY_COLORS = {
    "Very Low": "#FFFF00",
    "Low":      "#FFA500",
    "Moderate": "#FF4500",
    "High":     "#CC0000",
    "Extreme":  "#800080",
    "nan":      "#888888",
}

IBERIAN_CENTER = [39.5, -4.0]
DEFAULT_ZOOM   = 6


# ──────────────────────────────────────────────────────────────────
# MAIN MAP BUILDER
# ──────────────────────────────────────────────────────────────────

def build_map(
    df: pd.DataFrame,
    map_style: str = "Heatmap",
    basemap: str = "CartoDB Dark",
    selected_date: str = None,
) -> folium.Map:
    """
    Build and return an interactive Folium map.

    Parameters
    ----------
    df            : enriched fire DataFrame
    map_style     : "Heatmap" | "Markers" | "Clusters"
    basemap       : basemap tile name
    selected_date : ISO date string to filter data (None = all dates)
    """
    tiles_map = {
        "CartoDB Dark":    "CartoDB dark_matter",
        "CartoDB Light":   "CartoDB positron",
        "OpenStreetMap":   "OpenStreetMap",
        "Esri Satellite":  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    }
    tiles = tiles_map.get(basemap, "CartoDB dark_matter")

    m = folium.Map(
        location=IBERIAN_CENTER,
        zoom_start=DEFAULT_ZOOM,
        tiles=tiles,
        attr="© Antigravity · Data: NASA FIRMS",
        prefer_canvas=True,
    )

    # ── Optional satellite attr ────────────────────────────────────
    if basemap == "Esri Satellite":
        m = folium.Map(
            location=IBERIAN_CENTER,
            zoom_start=DEFAULT_ZOOM,
            tiles=tiles,
            attr="Tiles © Esri | Data: NASA FIRMS",
            prefer_canvas=True,
        )

    Fullscreen(position="topright").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)

    # ── Filter by date ─────────────────────────────────────────────
    plot_df = df.copy()
    if selected_date and "date_str" in plot_df.columns:
        plot_df = plot_df[plot_df["date_str"] == selected_date]

    if plot_df.empty:
        _add_no_data_marker(m)
        return m

    # ── Render chosen style ────────────────────────────────────────
    if map_style == "Heatmap":
        _add_heatmap(m, plot_df)
    elif map_style == "Clusters":
        _add_clusters(m, plot_df)
    else:  # Markers (default)
        _add_markers(m, plot_df)

    # ── Legend ─────────────────────────────────────────────────────
    _add_legend(m)

    return m


# ──────────────────────────────────────────────────────────────────
# LAYER BUILDERS
# ──────────────────────────────────────────────────────────────────

def _add_heatmap(m: folium.Map, df: pd.DataFrame) -> None:
    """Gradient heatmap weighted by FRP."""
    frp_vals = df["frp"].fillna(1).clip(1, 300)
    heat_data = list(zip(df["latitude"], df["longitude"], frp_vals))
    HeatMap(
        heat_data,
        min_opacity=0.35,
        max_zoom=12,
        radius=18,
        blur=14,
        gradient={
            0.0: "#000080",
            0.3: "#FFFF00",
            0.6: "#FFA500",
            0.8: "#FF4500",
            1.0: "#800080",
        },
    ).add_to(m)
    # Also add small dot markers for click info
    _add_markers(m, df, small=True)


def _add_markers(m: folium.Map, df: pd.DataFrame, small: bool = False) -> None:
    """Individual circle markers coloured by intensity."""
    feature_group = folium.FeatureGroup(name="Fire Hotspots", show=True)

    for _, row in df.iterrows():
        color  = row.get("marker_color", "#FF4500")
        radius = 4 if small else float(row.get("marker_size", 8))
        popup  = _build_popup(row)
        tooltip = (
            f"FRP: {row.get('frp', '?')} MW | "
            f"{row.get('intensity', '?')} | "
            f"{row.get('date_str', '')}"
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            opacity=0.9,
            popup=folium.Popup(popup, max_width=300),
            tooltip=tooltip,
        ).add_to(feature_group)

    feature_group.add_to(m)


def _add_clusters(m: folium.Map, df: pd.DataFrame) -> None:
    """MarkerCluster with coloured fire icons."""
    cluster = MarkerCluster(
        name="Fire Clusters",
        options={
            "spiderfyOnMaxZoom": True,
            "showCoverageOnHover": True,
            "maxClusterRadius": 60,
        },
    ).add_to(m)

    for _, row in df.iterrows():
        color  = _intensity_to_icon_color(row.get("intensity", "Low"))
        popup  = _build_popup(row)
        tooltip = f"{row.get('intensity','?')} – FRP: {row.get('frp','?')} MW"

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup, max_width=300),
            tooltip=tooltip,
            icon=folium.Icon(
                color=color,
                icon="fire",
                prefix="fa",
            ),
        ).add_to(cluster)


# ──────────────────────────────────────────────────────────────────
# POPUP & HELPERS
# ──────────────────────────────────────────────────────────────────

def _build_popup(row: pd.Series) -> str:
    frp        = row.get("frp", "N/A")
    brightness = row.get("brightness", "N/A")
    confidence = row.get("confidence", "N/A")
    satellite  = row.get("satellite", row.get("instrument", "N/A"))
    acq_date   = row.get("date_str", "N/A")
    acq_time   = str(row.get("acq_time", "N/A")).zfill(4)
    intensity  = row.get("intensity", "N/A")
    daynight   = row.get("daynight_label", "N/A").replace("[Day] ", "").replace("[Night] ", "")
    lat        = round(row["latitude"],  4)
    lon        = round(row["longitude"], 4)
    city       = row.get("city", "Unknown")
    region     = row.get("region", "Unknown")

    time_str = f"{acq_time[:2]}:{acq_time[2:]}" if len(acq_time) == 4 else acq_time

    color = INTENSITY_COLORS.get(intensity, "#FF4500")

    return f"""
    <div style="font-family:'Roboto', 'Open Sans', sans-serif;min-width:240px;color:#111">
      <div style="background:{color};color:#fff;padding:8px 12px;border-radius:6px 6px 0 0;
                  font-weight:700;font-size:14px">
        {intensity} Intensity Fire
      </div>
      <div style="padding:10px 12px;background:#f9f9f9;border-radius:0 0 6px 6px;
                  border:1px solid #ddd;border-top:none">
        <table style="width:100%;border-collapse:collapse;font-size:12px">
          <tr><td style="color:#555;padding:3px 0">Region</td>
              <td style="text-align:right;font-weight:600">{city}, {region}</td></tr>
          <tr><td style="color:#555;padding:3px 0">Coordinates</td>
              <td style="text-align:right;font-weight:600">{lat}°N, {lon}°E</td></tr>
          <tr><td style="color:#555;padding:3px 0">FRP</td>
              <td style="text-align:right;font-weight:600">{frp} MW</td></tr>
          <tr><td style="color:#555;padding:3px 0">Brightness</td>
              <td style="text-align:right;font-weight:600">{brightness} K</td></tr>
          <tr><td style="color:#555;padding:3px 0">Satellite</td>
              <td style="text-align:right;font-weight:600">{satellite}</td></tr>
          <tr><td style="color:#555;padding:3px 0">Date</td>
              <td style="text-align:right;font-weight:600">{acq_date}</td></tr>
          <tr><td style="color:#555;padding:3px 0">Time (UTC)</td>
              <td style="text-align:right;font-weight:600">{time_str}</td></tr>
          <tr><td style="color:#555;padding:3px 0">Confidence</td>
              <td style="text-align:right;font-weight:600">{confidence}</td></tr>
          <tr><td style="color:#555;padding:3px 0">{daynight}</td>
              <td></td></tr>
        </table>
      </div>
    </div>
    """


def _intensity_to_icon_color(intensity: str) -> str:
    return {
        "Very Low": "beige",
        "Low":      "orange",
        "Moderate": "red",
        "High":     "darkred",
        "Extreme":  "purple",
    }.get(intensity, "red")


def _add_no_data_marker(m: folium.Map) -> None:
    folium.Marker(
        location=IBERIAN_CENTER,
        popup="No fire data for selected filters.",
        icon=folium.Icon(color="gray", icon="info-sign"),
    ).add_to(m)


def _add_legend(m: folium.Map) -> None:
    legend_html = """
    <div style="
        position: fixed; bottom: 50px; left: 15px; z-index: 1000;
        background: rgba(15,15,25,0.92); border-radius: 12px;
        padding: 14px 18px; font-family:'Segoe UI',sans-serif;
        backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1);
        color: #fff; box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
      <div style="font-weight:700;font-size:13px;margin-bottom:10px;
                  letter-spacing:.5px;color:#FF9A3C">
        FIRE INTENSITY (FRP)
      </div>
      <div style="display:flex;flex-direction:column;gap:6px;font-size:12px">
        <div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;
             background:#FFFF00;margin-right:8px;vertical-align:middle"></span>Very Low  &lt; 10 MW</div>
        <div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;
             background:#FFA500;margin-right:8px;vertical-align:middle"></span>Low  10–30 MW</div>
        <div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;
             background:#FF4500;margin-right:8px;vertical-align:middle"></span>Moderate  30–75 MW</div>
        <div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;
             background:#CC0000;margin-right:8px;vertical-align:middle"></span>High  75–150 MW</div>
        <div><span style="display:inline-block;width:12px;height:12px;border-radius:50%;
             background:#800080;margin-right:8px;vertical-align:middle"></span>Extreme  &gt; 150 MW</div>
      </div>
      <div style="margin-top:10px;font-size:10px;color:#aaa">
        FRP = Fire Radiative Power
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
