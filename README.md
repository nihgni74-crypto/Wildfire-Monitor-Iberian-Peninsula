# 🔥 Wildfire Monitor – Iberian Peninsula
### Real-Time Active Fire Dashboard | NASA FIRMS + Python + Streamlit

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![NASA FIRMS](https://img.shields.io/badge/Data-NASA_FIRMS-orange?logo=nasa)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Live Demo
**→ [your-app.streamlit.app](https://your-app.streamlit.app)**

---

## 📸 Features

| Feature | Details |
|---------|---------|
| 🗺️ **Interactive Map** | Heatmap · Marker · Cluster views (Folium) |
| 📊 **6 Analytics Charts** | Daily trends, FRP distribution, hourly polar, intensity donut |
| 🛰️ **3 Satellite Sources** | VIIRS SNPP · VIIRS NOAA-20 · MODIS NRT |
| 🌍 **6 Regions** | Spain · Portugal · Mediterranean · Europe |
| ⬇️ **CSV Export** | Download filtered data |
| 📅 **Date Slider** | Filter by day with real-time map update |
| 🎨 **Dark Fire Theme** | Premium UI with glassmorphism effects |

---

## 🛠️ Local Setup

### 1. Clone / download
```bash
git clone https://github.com/YOUR_USERNAME/wildfire-monitor.git
cd wildfire-monitor
```

### 2. Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Get your FREE NASA API Key
Go to → **https://firms.modaps.eosdis.nasa.gov/api/area/**
(takes ~1 minute, completely free)

### 5. Set API key
Copy `.env.example` to `.env` and paste your key:
```
NASA_FIRMS_API_KEY=your_actual_key_here
```

### 6. Run the app
```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## ☁️ Deploy to Streamlit Cloud (FREE)

1. Push to GitHub (public repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → select `app.py`
4. Add secret: `NASA_FIRMS_API_KEY = "your_key"`
5. **Deploy** → get your public URL in ~2 minutes!

---

## 📁 Project Structure

```
wildfire-monitor/
├── app.py              ← Main Streamlit application
├── data_fetcher.py     ← NASA FIRMS API + data enrichment
├── map_builder.py      ← Folium interactive maps
├── charts.py           ← Plotly analytics charts
├── requirements.txt    ← Python dependencies
├── .streamlit/
│   └── config.toml     ← Streamlit theme config
└── .env.example        ← API key template
```

---

## 🔬 Data Explained

### Sensors
| Sensor | Resolution | Lag | Best For |
|--------|------------|-----|---------|
| VIIRS SNPP | **375m** | ~3h | Accuracy, small fires |
| VIIRS NOAA-20 | **375m** | ~3h | Most current data |
| MODIS NRT | 1km | ~3h | Historical patterns |

### Fire Intensity (FRP)
| Color | FRP | Meaning |
|-------|-----|---------|
| 🟡 Yellow | < 10 MW | Small / smoldering |
| 🟠 Orange | 10–30 MW | Active low vegetation |
| 🔴 Red | 30–75 MW | Forest fire |
| 🔴 Dark Red | 75–150 MW | Large forest fire |
| 🟣 Purple | > 150 MW | Catastrophic megafire |

---

## 👩‍💻 Author

**Niloofar** – GIS & Environmental Data Analyst  
📍 Spain | 🌍 Remote-friendly  
🔗 [LinkedIn](https://linkedin.com/www.linkedin.com/in/niloofar-haghi-99aa2a137) | [GitHub](https://github.com/your-username)

---

*Data sourced from [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov) – Fire Information for Resource Management System*
