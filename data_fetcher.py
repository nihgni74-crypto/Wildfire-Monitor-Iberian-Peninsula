"""
NASA FIRMS Data Fetcher
-----------------------
Fetches active fire data from NASA FIRMS API for Spain and Portugal.
Supports VIIRS (SNPP & NOAA-20) and MODIS sensors.
"""

import requests
import pandas as pd
import numpy as np
import io
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

load_dotenv()

# ──────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────

NASA_API_KEY = os.getenv("NASA_FIRMS_API_KEY", "DEMO_KEY")

# Bounding boxes: [West, South, East, North]
REGIONS = {
    "Spain + Portugal": "-9.5,35.8,4.5,43.9",
    "Spain only":       "-9.5,35.8,4.5,43.9",
    "Portugal only":    "-9.5,36.9,-6.2,42.2",
    "Iberian Peninsula + Balearics": "-9.5,35.0,4.5,44.0",
    "Mediterranean Basin": "-5.0,35.0,35.0,47.0",
    "Europe (Wide)":    "-12.0,34.0,32.0,71.0",
}

SENSORS = {
    "VIIRS SNPP (High Resolution)": "VIIRS_SNPP_SP",
    "VIIRS NOAA-20 (Most Recent)":  "VIIRS_NOAA20_NRT",
    "MODIS (Historical)":           "MODIS_NRT",
}

BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# DEMO DATA – used when API key is not set or quota exceeded
DEMO_FIRE_DATA = {
    "latitude":   [40.41, 39.87, 41.23, 38.56, 37.98, 42.10, 39.34, 40.75,
                   38.12, 41.67, 39.50, 40.22, 37.65, 38.90, 41.45, 40.60,
                   38.35, 39.78, 41.01, 40.89, 38.67, 39.23, 40.55, 37.89,
                   41.34, 39.11, 40.78, 38.45, 37.12, 41.90],
    "longitude":  [-3.70, -4.23, -1.87, -6.12, -5.45, -2.34, -3.45, -4.89,
                   -7.23, -3.12, -4.56, -2.78, -5.67, -6.34, -1.23, -3.90,
                   -6.78, -4.01, -2.56, -3.45, -5.12, -3.89, -4.23, -5.90,
                   -1.67, -4.78, -3.34, -6.56, -7.45, -2.89],
    "brightness": [320, 345, 298, 378, 412, 289, 334, 367, 301, 356,
                   389, 312, 423, 345, 278, 398, 334, 367, 289, 412,
                   301, 356, 389, 312, 423, 345, 278, 398, 445, 267],
    "frp":        [12.3, 24.7, 8.9, 45.2, 67.8, 6.7, 18.4, 32.1, 11.2, 28.9,
                   55.3, 14.6, 89.4, 23.7, 5.4, 61.2, 18.4, 32.1, 6.7, 67.8,
                   11.2, 28.9, 55.3, 14.6, 89.4, 23.7, 5.4, 61.2, 102.3, 4.1],
    "confidence": ["high","nominal","nominal","high","high","nominal","nominal","high",
                   "nominal","high","high","nominal","high","nominal","nominal","high",
                   "nominal","high","nominal","high","nominal","high","high","nominal",
                   "high","nominal","nominal","high","high","nominal"],
    "acq_date":   [(datetime.now() - timedelta(days=i % 7)).strftime("%Y-%m-%d")
                   for i in range(30)],
    "acq_time":   [f"{(6 + i * 37) % 24:02d}{(i * 17) % 60:02d}" for i in range(30)],
    "satellite":  ["N20" if i % 2 == 0 else "Suomi-NPP" for i in range(30)],
    "instrument": ["VIIRS"] * 30,
    "daynight":   ["D" if (6 + i * 37) % 24 < 18 else "N" for i in range(30)],
    "version":    ["2.0NRT"] * 30,
    "track":      [0.4] * 30,
    "scan":       [0.4] * 30,
    "bright_t31": [290 + i % 20 for i in range(30)],
}


# ──────────────────────────────────────────────────────────────────
# MAIN FETCH FUNCTION
# ──────────────────────────────────────────────────────────────────

def fetch_fire_data(
    region_key: str = "Spain + Portugal",
    sensor_key: str = "VIIRS SNPP (High Resolution)",
    days: int = 7,
    api_key: str = None,
) -> pd.DataFrame:
    """
    Fetch active fire data from NASA FIRMS.

    Parameters
    ----------
    region_key : str  – key from REGIONS dict
    sensor_key : str  – key from SENSORS dict
    days       : int  – 1–10 days of data
    api_key    : str  – NASA FIRMS API key (falls back to env var)

    Returns
    -------
    pd.DataFrame with enriched fire data
    """
    key = api_key or NASA_API_KEY

    if key in ("your_api_key_here", "DEMO_KEY", "", None):
        log.info("No API key found - using demo data")
        return _build_demo_df()

    bbox   = REGIONS.get(region_key, REGIONS["Spain + Portugal"])
    sensor = SENSORS.get(sensor_key, SENSORS["VIIRS SNPP (High Resolution)"])
    url    = f"{BASE_URL}/{key}/{sensor}/{bbox}/{days}"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        if "<!DOCTYPE" in resp.text[:50] or len(resp.text) < 30:
            log.warning("API returned HTML or empty - using demo data")
            return _build_demo_df()

        df = pd.read_csv(io.StringIO(resp.text))

        if df.empty:
            log.info("No fires detected - returning demo dataframe")
            return _build_demo_df()

        return _enrich(df)

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "?"
        log.warning("HTTP %s error - using demo data", status)
        return _build_demo_df()

    except Exception as e:
        log.warning("Fetch error: %s - using demo data", e)
        return _build_demo_df()


# ──────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────

def _build_demo_df() -> pd.DataFrame:
    """Return the static demo dataset, enriched."""
    df = pd.DataFrame(DEMO_FIRE_DATA)
    return _enrich(df)


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns used by the dashboard."""
    df = df.copy()

    # ── Numeric coercions ──────────────────────────────────────────
    for col in ("frp", "brightness", "latitude", "longitude"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Datetime ───────────────────────────────────────────────────
    if "acq_date" in df.columns:
        df["acq_date"] = pd.to_datetime(df["acq_date"], errors="coerce")
        df["date_str"] = df["acq_date"].dt.strftime("%Y-%m-%d")
        df["day_of_week"] = df["acq_date"].dt.day_name()
    else:
        today = datetime.now()
        df["acq_date"] = today
        df["date_str"] = today.strftime("%Y-%m-%d")
        df["day_of_week"] = today.strftime("%A")

    # ── FRP intensity classification ───────────────────────────────
    if "frp" in df.columns:
        frp = df["frp"].fillna(0)
        df["intensity"] = pd.cut(
            frp,
            bins=[-np.inf, 10, 30, 75, 150, np.inf],
            labels=["Very Low", "Low", "Moderate", "High", "Extreme"],
        ).astype(str)
        df["intensity_score"] = pd.cut(
            frp,
            bins=[-np.inf, 10, 30, 75, 150, np.inf],
            labels=[1, 2, 3, 4, 5],
        ).astype(float)
        df["marker_size"] = 6 + frp.clip(0, 200) / 8
        df["marker_color"] = frp.apply(_frp_to_color)

    # ── Day/Night label ────────────────────────────────────────────
    if "daynight" in df.columns:
        df["daynight_label"] = df["daynight"].map({"D": "[Day] Daytime", "N": "[Night] Nighttime"}).fillna("Unknown")

    # ── Confidence normalise ───────────────────────────────────────
    if "confidence" in df.columns:
        conf_map = {"l": "Low", "n": "Nominal", "h": "High",
                    "low": "Low", "nominal": "Nominal", "high": "High"}
        df["confidence"] = df["confidence"].astype(str).str.lower().map(
            lambda x: conf_map.get(x, x.capitalize())
        )

    # ── Drop NaN lat/lon ───────────────────────────────────────────
    df = df.dropna(subset=["latitude", "longitude"])

    return df.reset_index(drop=True)


def _frp_to_color(frp: float) -> str:
    """Map Fire Radiative Power → CSS colour for Folium markers."""
    if frp < 10:   return "#FFFF00"   # yellow  – very low
    if frp < 30:   return "#FFA500"   # orange  – low
    if frp < 75:   return "#FF4500"   # red-orange – moderate
    if frp < 150:  return "#CC0000"   # dark red – high
    return "#800080"                  # purple  – extreme


# ──────────────────────────────────────────────────────────────────
# STATISTICS
# ──────────────────────────────────────────────────────────────────

def compute_stats(df: pd.DataFrame) -> dict:
    """Return a dict of dashboard KPI values."""
    if df.empty:
        return {"total": 0, "frp_mean": 0, "frp_max": 0,
                "high_pct": 0, "days_span": 0, "night_pct": 0}

    frp_vals  = df["frp"].dropna()
    high_mask = df.get("intensity", pd.Series()).isin(["High", "Extreme"])

    return {
        "total":     len(df),
        "frp_mean":  round(frp_vals.mean(), 1) if not frp_vals.empty else 0,
        "frp_max":   round(frp_vals.max(),  1) if not frp_vals.empty else 0,
        "high_pct":  round(high_mask.sum() / len(df) * 100, 1),
        "days_span": int(df["acq_date"].nunique()) if "acq_date" in df.columns else 0,
        "night_pct": round((df.get("daynight", pd.Series()) == "N").mean() * 100, 1),
    }
