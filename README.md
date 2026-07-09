# 🚨 Insider Trading & Market Anomaly Radar

An end-to-end quantitative analytics application that ingests daily SEC EDGAR Form 4 filings (corporate executive stock transactions) and evaluates subsequent asset performance against the S&P 500 index. By utilizing **Event Study Methodology** and calculating **Cumulative Abnormal Returns (CAR)**, the system filters out macro market noise and flags statistically significant trading anomalies through a dynamic web frontend.

## 📊 App Previews
* **Data Metrics & Risk Leaderboard:** Displays localized transactional logs parsed straight from federal endpoints alongside progress metrics.
* **Alpha Visualizer:** Relies on indexed time-series vector streams to map equity movements directly against benchmark paths to uncover performance deviations.
<img width="959" height="472" alt="Screenshot 2026-07-09 203150" src="https://github.com/user-attachments/assets/d5f425ce-b9fd-4d9f-8c99-684a49fd6f44" />
<img width="959" height="475" alt="Screenshot 2026-07-09 203202" src="https://github.com/user-attachments/assets/95214362-71ad-4c6e-9971-0d4cd3e1a1e0" />

---

## 🏗️ System Architecture & Data Pipeline

The platform is designed across a decoupled, five-phase pipeline to ensure data integrity and process automation:

1. **Ingestion Engine (`phase1_ingestion.py`)**: Connects to the SEC EDGAR REST API to pull daily index registries, extracts target Form 4 filings, handles URL translations, and processes deep XML tree traversals to scrape clean insider details.
2. **Storage Layer (`phase2_database.py`)**: Initializes a relational SQLite database schema. Employs `INSERT OR IGNORE` state controls across unique multi-column constraints to prevent row replication.
3. **Market Enrichment (`phase3_market_data.py`)**: Interfaces with the Yahoo Finance API (`yfinance`) to fetch historical daily pricing bars for both the parsed asset tickers and the market benchmark (`SPY`).
4. **Quant Stats Engine (`phase4_stats_engine.py`)**: Computes day-by-day percentage return variations post-event to track asset adjustments detached from core market movements.
5. **Analytics Frontend (`app.py`)**: A web-based executive dashboard built using **Streamlit** that processes real-time database queries, computes alpha matrices on-the-fly, and serves interactive time-series charts.

---

## 🛠️ Tech Stack & Analytical Methods

* **Language:** Python 3.13
* **Frontend UI:** Streamlit 
* **Data Engineering & Vector Math:** Pandas, NumPy
* **API Ingestion Libraries:** Requests, ElementTree XML Parser, yfinance
* **Database Management:** SQLite3 (Relational)
* **Statistical Framework:** Event Study Methodology (Market-Adjusted Performance Spread)

---

## 📐 The Core Math: How "Suspicion" is Quantified

To separate routine executive liquidity trades (e.g., scheduled 10b5-1 plans) from opportunistic market timing, the system isolates **Abnormal Return ($AR$)** over a 20-day post-event sequence:

$$AR_{it} = R_{it} - R_{mt}$$

Where $R_{it}$ represents the daily percentage return of the target stock and $R_{mt}$ represents the baseline return of the market index ($SPY$). Summing these deltas yields the **Cumulative Abnormal Return (CAR)**:

$$CAR_i = \sum_{t=T_1}^{T_2} AR_{it}$$

The final **Suspicion Score (0-100)** applies a sigmoidal transformation to the calculated CAR matrix. Insider purchases ($P$) are penalized/flagged when the asset aggressively decouples and skyrockets over the market index, while sales ($S$) gain score weight if the executive successfully sidestepped a significant stock decline.

---

## 🚀 How To Run Locally

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/insider-trading-radar.git](https://github.com/YOUR_USERNAME/insider-trading-radar.git)
cd insider-trading-radar
```
### 2. Install Project Dependencies
Ensure your environment is running Python 3.11+ and install the structured libraries:
```bash
pip install pandas numpy requests yfinance streamlit
```
### 3. Populating Data & Launching the App
Run the ingestion files sequentially to initialize the database records, then trigger the Streamlit engine:
```
# Pull daily master entries and populate database tables
python phase1_ingestion.py

# Download historical stock pricing paths around active trade windows
python phase3_market_data.py

# Fire up the Streamlit engine server locally
streamlit run app.py
```
## 📈 Key Learnings & Technical Takeaways
* SEC Data Normalization: Overcame strict SEC automated rate-limiting policies by enforcing custom user-agent request mappings and parsing embedded text headers to locate clean XML payloads.
* Vectorized Data Transformations: Avoided performance-heavy row loops by pivoting temporal tables across dynamic date-indexes to calculate parallel percentage shifts across varying assets simultaneously.
* Relational Storage Strategies: Designed localized SQL indexing layers to safeguard transactional streams against overlapping ingestion duplicates.
