# Quant Trading Analytics Dashboard
---
# Overview

This project implements a quantitative trading analytics dashboard for high-frequency tick data, designed to demonstrate end-to-end data ingestion, statistical analysis, and visualization in line with the Quant Developer assignment requirements.

The system processes Binance tick-level crypto data, computes statistical relationships between asset pairs, and visualizes hedge ratios, spreads, z-scores, correlations, stationarity tests, and alerts through an interactive dashboard.

The design emphasizes modularity, robustness, and reproducibility, closely mirroring how real-world quant analytics pipelines are structured.
---
# Key Features
- Tick-level crypto data ingestion (Binance WebSocket compatible)
- Schema normalization and UTC-safe timestamp handling
- Multi-timeframe resampling (1s / 1m / 5m)
- Hedge ratio estimation with robust fallback logic
- Spread and rolling z-score computation
- Rolling correlation analysis
- Augmented Dickey-Fuller (ADF) stationarity test
- Mean-reversion backtest (signal validation)
- Interactive Streamlit dashboard with alerts
- CSV export for further analysis

---
# Architecture

The system follows a feed-agnostic, layered architecture separating ingestion, processing, analytics, and visualization.
This enables easy replacement of the data source (file-based or live WebSocket) without changing analytics logic.

# Architecture Flow
Data Source → Ingestion → Resampling → Analytics → Visualization → Alerts & Export

# Architecture Components

1) Data Source
- Binance WebSocket (HTML collector)
- NDJSON tick files for offline / demo mode

2) Ingestion & Normalization (storage.py)
- Parses NDJSON
-Normalizes schema
-Enforces UTC timestamps

3) Resampling Engine (resampler.py)
- Converts ticks into OHLC bars
- Supports 1s / 1m / 5m intervals

4) Analytics Engine (analytics.py)
- Hedge ratio (OLS with ratio fallback)
- Spread & z-score
- Rolling correlation
- ADF test
- Mean-reversion backtest

5) Frontend Dashboard (app.py)
- Interactive charts
- User controls
- Live metrics & alerts

6) Alerts & Export
- Z-score threshold alerts
- CSV data export

---
# Data Ingestion
Live tick data is collected using the provided HTML WebSocket tool connecting to Binance.
For this prototype, the collected data is stored as NDJSON and uploaded into the dashboard.
The ingestion layer is intentionally feed-agnostic — the same processing pipeline can directly consume a live WebSocket stream or message queue with minimal changes.

---
# OHLC Support

The application internally generates OHLC bars from tick data using configurable resampling intervals.
The ingestion and resampling layers are designed to also support pre-aggregated OHLC CSV files with minimal modification, if required.

---
# Analytics Details
Hedge Ratio Estimation

- Primary method: Ordinary Least Squares (OLS)
- Fallback method: Ratio-based hedge
- The fallback is triggered when data variance is too low or regression becomes ill-conditioned

This approach prevents misleading analytics when working with sparse or flat tick data.

---
# Spread & Z-Score
- Spread is computed using the estimated hedge ratio
- Rolling z-score highlights deviations from the mean
- User-defined thresholds trigger alerts

---
# Rolling Correlation
- Measures short-term relationship stability between assets
- Helps validate pair-trading suitability

---
# Stationarity Test (ADF)
- Augmented Dickey-Fuller test is applied to the spread
- Indicates whether the spread is mean-reverting

---
# Backtest
A simple mean-reversion backtest is included to:
- Validate signal intuition
- Demonstrate end-to-end analytics flow
This backtest is not intended to represent execution-level performance.

---
# Alerts
- Z-score threshold alerts update dynamically
- Visual cues highlight statistical anomalies in near-real-time

---
# Frontend
The dashboard is built using Streamlit + Plotly and includes:
- Symbol selection
- Timeframe selection
- Rolling window control
- Interactive charts and metrics
- Tab-based navigation for analytics views

# Environment Reproducibility
Exact dependency versions are pinned to ensure consistent behavior across machines and operating systems.

---
# Requirements
```
pandas==2.2.2
numpy==1.26.4
statsmodels==0.14.2
plotly==5.22.0
streamlit==1.36.0
```

---
# Running the Application
1. Create Virtual Environment
```
python -m venv venv
```

2. Activate Environment
- Windows
```
venv\Scripts\activate
```

- macOS / Linux
```
source venv/bin/activate
```

3. Install Dependencies
```
pip install -r requirements.txt
```

4. Run Dashboard
```
streamlit run app.py
```


---
# Notes on Live Analytics

While the demo uses uploaded tick files, analytics are recomputed incrementally on resampled windows.
In a live WebSocket setup, metrics such as z-score and alerts would update continuously, while longer-horizon plots update at their respective resampling frequencies.

---
# ChatGPT Usage Disclosure
ChatGPT was used as a development assistant for:
- Debugging
- Code refinement
- Documentation clarity

---
# Conclusion
This project demonstrates a production-inspired quant analytics pipeline, balancing statistical rigor with practical robustness.
The modular design, defensive data handling, and clear analytics flow align closely with real-world quantitative engineering practices.

---