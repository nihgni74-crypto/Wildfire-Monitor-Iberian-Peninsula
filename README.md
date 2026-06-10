# Wildfire Monitor - Spain and Balearic Islands
### Real-Time Geospatial Active Fire Dashboard for Environmental and GIS Analytics

This repository contains a high-performance, near-real-time active fire monitoring and analytics application designed specifically for the tracking, visualization, and statistical evaluation of wildfire hotspots across Mainland Spain and the Balearic Islands. Utilizing advanced remote sensing data streams, this dashboard serves as an enterprise-grade solution for environmental data analysts, emergency response coordinators, and GIS specialists.

---

## System Architecture

The workflow architecture below demonstrates the end-to-end data pipeline, from edge satellite ingestion to the client-side interactive rendering components:

```mermaid
graph TD
    %% Source Node
    A[NASA FIRMS API Server] -->|Asynchronous HTTPS Request| B[Data Ingestion Engine]
    
    %% Ingestion Node
    subgraph Data Engineering Pipeline [data_fetcher.py]
        B -->|Raw CSV Stream Input| C[Quality Assurance & Numeric Coercion]
        C -->|Drop Corrupted Coordinates| D[Temporal Parsing & ISO Standardization]
        D -->|Scientific Metrics Processing| E[FRP Intensity Stratification Tiers]
    end

    %% State Management
    E -->|Enriched Dataframe Payload| F[Streamlit Session State Cache]
    
    %% Application Layer
    subgraph UI & Analytical Subsystems [app.py]
        F -->|Global Temporal Filters| G[Streamlit Core Interface Layout]
        G -->|Spatial Geometry Mapping| H[Folium Map Builder Module]
        G -->|Statistical Data Vectors| I[Plotly Chart Engine Module]
    end
    
    %% Output Layer
    subgraph Geospatial Visualization [map_builder.py]
        H -->|Leaflet JS Engine| J[Dynamic Heatmap Layer]
        H -->|Leaflet JS Engine| K[Geographic Cluster Layer]
        H -->|Leaflet JS Engine| L[Proportional Circle Markers]
    end
    
    subgraph Statistical Graphics [charts.py]
        I -->|Multi-Axis Traces| M[Diurnal Polar Rose Charts]
        I -->|Multi-Axis Traces| N[Dual-Axis Historical Trends]
        I -->|Multi-Axis Traces| O[FRP Density Histograms]
    end

    %% Style Adjustments
    style A fill:#1a1c23,stroke:#ff6b35,stroke-width:2px;
    style F fill:#131929,stroke:#ff9a3c,stroke-width:2px;
    style G fill:#131929,stroke:#00cc96,stroke-width:2px;
Project Overview
Wildfires present a critical threat to ecosystems and communities across Spain, particularly under escalating climatic stress. This project provides a robust, automated framework that extracts near-real-time thermal anomaly data directly from orbital sensors, processes and enriches the dataset, and renders an interactive geospatial interface alongside advanced data visualizations.

The application is structured using modular design patterns, ensuring clear separation of concerns between data ingestion, geoprocessing, geospatial rendering, and analytics.

Key Features
Interactive Geospatial Visualization: Renders interactive maps featuring customizable basemaps (including CartoDB Dark Matter, CartoDB Positron, OpenStreetMap, and Esri World Imagery). Offers three sophisticated rendering layers:

Dynamic Heatmaps: Weighted by Fire Radiative Power (FRP) to highlight high-energy propagation zones.

Circle Markers: Individually scaled and color-coded based on discrete fire intensity levels.

Marker Clusters: Geographically aggregated groups with customizable aggregation radii for regional macro-analysis.

Advanced Plotly Analytics: Includes a suite of multi-axis statistical charts detailing:

Daily temporal hotspot frequencies.

Fire Radiative Power (FRP) density distributions.

Cumulative intensity classifications.

Polar/Rose hourly distribution charts to map diurnal fire behavior patterns.

Dual-axis historical trend series comparing mean and peak FRP values alongside total hotspot frequencies.

Geospatial Data Filtering: Supports interactive temporal sliding filters, allowing users to isolate active thermal anomalies by specific acquisition dates or analyze historical spans.

Raw Data Exploration and Export: Features tabular views of raw satellite records with multi-criteria attribute filtering (intensity tiers, minimum FRP thresholds, and diurnal indicators) paired with an automated CSV export system for offline GIS workflows.

Data Pipeline & Remote Sensing Methodology
The data architecture relies on data feeds from the National Aeronautics and Space Administration (NASA) Fire Information for Resource Management System (FIRMS) API. The pipeline ingests records from three core spaceborne instruments:

VIIRS SNPP (Suomi National Polar-orbiting Partnership): Delivers a 375-meter spatial resolution, optimized for early-stage detection of small or low-intensity thermal anomalies.

VIIRS NOAA-20: Provides secondary high-resolution (375m) orbital overpasses, ensuring a near-real-time update lag of under 3 hours.

MODIS (Moderate Resolution Imaging Spectroradiometer): Ingests historical and current macro-scale thermal anomalies at a 1-kilometer spatial resolution for macro-trend baselines.

Data Ingestion and Enrichment
Upon fetching raw comma-separated data streams from the API, the ingestion engine handles:

Numeric Coercion and Quality Assurance: Standardizes and cleans geographical coordinates, radiometric temperatures (Kelvin), and FRP values while dropping corrupted entries.

Temporal Parsing: Standardizes acquisition timestamps into localized ISO dates, tracking weekly distributions and acquisition schedules.

FRP Intensity Stratification: Categorizes raw Fire Radiative Power metrics into discrete operational classes using predefined scientific thresholds:

Very Low (< 10 MW)

Low (10–30 MW)

Moderate (30–75 MW)

High (75–150 MW)

Extreme (> 150 MW)

Visual Metric Derivation: Automatically calculates proportional pixel radii and hexadecimal color codes for geospatial markers based on the distribution of fire energy.

Geographical Scope
The application's geospatial query boundaries are constrained exclusively to Mainland Spain and the Balearic Islands. The coordinates utilize localized regional bounding boxes [-9.5, 35.0, 4.5, 44.0] to filter out surrounding continental datasets, providing a dedicated analytical environment tailored for Spanish environmental agencies and regional administrations.

Technical Stack
Core Language: Python 3.11+

Dashboard Framework: Streamlit (Custom responsive design with embedded asynchronous states)

Geospatial Mapping: Folium / Leaflet.js & Streamlit-Folium

Data Engineering & Analytics: Pandas, NumPy

Data Visualization: Plotly Express & Plotly Graph Objects

API Integration: Requests, Python-Dotenv

Project Architecture
wildfire-monitor/
├── app.py              # Main application configuration, custom CSS, UI tabs, and sidebar controllers
├── data_fetcher.py     # NASA FIRMS API interaction, exception handling, data engineering, and statistics computation
├── map_builder.py      # Leaflet map generation, spatial layers (Heatmap/Clusters), and HTML/CSS popup template design
├── charts.py           # Plotly analytical figures, theme configurations, and data visualization matrices
├── requirements.txt    # Application dependencies and package management definitions
└── .streamlit/
    └── config.toml     # Streamlit environment theme guidelines (Dark theme palette definitions)
Local Setup and Installation
1. Environment Preparation
Clone the repository and navigate to the project root directory:

Bash
git clone [https://github.com/nihgni74-crypto/wildfire-monitor-iberian-peninsula.git](https://github.com/nihgni74-crypto/wildfire-monitor-iberian-peninsula.git)
cd wildfire-monitor-iberian-peninsula
2. Dependency Management
Create an isolated virtual environment and install the specified library dependencies:

Bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

pip install -r requirements.txt
3. API Credentials Configuration
Obtain a free NASA FIRMS API key from the NASA MODAPS portal. Establish a localized environment configuration by replicating the template:

Bash
cp .env.example .env
Open the .env file and append your secure credential:

Code snippet
NASA_FIRMS_API_KEY=your_actual_nasa_firms_api_key
4. Running the Application
Launch the local web server using the Streamlit CLI:

Bash
streamlit run app.py
The application will automatically initialize and serve the interactive interface at http://localhost:8501.

Author Information
Niloofar Haghi GIS & Environmental Data Analyst Specializing in geospatial analysis, environmental modeling, and interactive data architecture.

LinkedIn Profile: linkedin.com/in/niloofar-haghi-99aa2a137

Data Credits: Active fire data provided courtesy of NASA FIRMS (Fire Information for Resource Management System).

This dashboard is designed as an analytical portfolio asset. For operational emergency alerts, always refer to official local emergency management authorities across Spain.