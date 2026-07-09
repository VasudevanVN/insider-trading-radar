import streamlit as st
import sqlite3
import pandas as pd
import numpy as np

DB_NAME = "insider_radar.db"

st.set_page_config(page_title="Insider Trading Anomaly Radar", layout="wide")

st.title("🚨 Insider Trading / Market Anomaly Radar")
st.markdown("This dashboard tracks SEC Form 4 insider filings and flags statistically unusual trading windows based on **Cumulative Abnormal Returns (CAR)**.")

conn = sqlite3.connect(DB_NAME)

# --- 1. Metrics Overview Sidebar ---
st.sidebar.header("Pipeline Status")
total_trades = pd.read_sql_query("SELECT COUNT(*) as count FROM insider_trades", conn).iloc[0]['count']
total_prices = pd.read_sql_query("SELECT COUNT(*) as count FROM market_prices", conn).iloc[0]['count']

st.sidebar.metric("Captured Insider Trades", total_trades)
st.sidebar.metric("Market Price Data Points", total_prices)

# --- 2. Calculate and Display Leaderboard ---
trades_df = pd.read_sql_query("SELECT * FROM insider_trades", conn)
prices_df = pd.read_sql_query("SELECT * FROM market_prices", conn)

if trades_df.empty or prices_df.empty:
    st.warning("Data is missing. Please run your ingestion and market data sync files first!")
else:
    # Math calculation identical to Phase 4
    prices_pivot = prices_df.pivot(index='price_date', columns='ticker', values='close_price').sort_index()
    returns_df = prices_pivot.pct_change().dropna()
    
    calculated_anomalies = []
    for _, trade in trades_df.iterrows():
        ticker = trade['ticker']
        trade_date = trade['trade_date']
        tx_type = trade['transaction_type']
        
        if ticker in returns_df.columns and 'SPY' in returns_df.columns:
            post_trade_returns = returns_df[returns_df.index >= trade_date].head(20)
            if not post_trade_returns.empty:
                car = float(np.sum(post_trade_returns[ticker].values - post_trade_returns['SPY'].values))
                perf = car * 100 if tx_type == 'P' else -car * 100
                suspicion_score = int(100 / (1 + np.exp(-0.2 * (perf - 5))))
                
                calculated_anomalies.append({
                    "Ticker": ticker,
                    "Insider Name": trade['insider_name'],
                    "Title": trade['title'],
                    "Trade Date": trade_date,
                    "Type": "Buy (P)" if tx_type == 'P' else "Sell (S)",
                    "Total Value ($)": f"${trade['total_value']:,}",
                    "20d Market Alpha (CAR %)": f"{round(car * 100, 2)}%",
                    "Suspicion Score": suspicion_score
                })
                
    results_df = pd.DataFrame(calculated_anomalies).sort_values(by="Suspicion Score", ascending=False)
    
    # Render Leaderboard
    st.subheader("🏆 Risk Anomaly Leaderboard")
    
    # Color code the suspicion score column
    st.dataframe(
        results_df,
        column_config={
            "Suspicion Score": st.column_config.ProgressColumn(
                "Suspicion Score", help="Risk rank based on post-event abnormal returns", min_value=0, max_value=100, format="%d"
            )
        },
        use_container_width=True,
        hide_index=True
    )

    # --- 3. Trend Visualizer Chart ---
    st.markdown("---")
    st.subheader("📈 Relative Price Movement Chart")
    
    # Pick ticker from our list to view chart
    selected_ticker = st.selectbox("Select a Ticker to visualize relative performance:", trades_df['ticker'].unique())
    
    # Normalize prices to 100 at the start of our tracking window to compare paths
    ticker_prices = prices_pivot[[selected_ticker, 'SPY']].dropna()
    if not ticker_prices.empty:
        normalized_prices = (ticker_prices / ticker_prices.iloc[0]) * 100
        st.line_chart(normalized_prices)
        st.caption("Chart shows the asset paths indexed to 100 at the start of the evaluation sequence. Spreads indicate alpha deviations.")

conn.close()