import sqlite3
import pandas as pd
import numpy as np

DB_NAME = "insider_radar.db"

def calculate_anomaly_scores():
    conn = sqlite3.connect(DB_NAME)
    
    # 1. Fetch our recorded insider trades
    trades_df = pd.read_sql_query("SELECT * FROM insider_trades", conn)
    # 2. Fetch our daily market prices
    prices_df = pd.read_sql_query("SELECT * FROM market_prices", conn)
    
    if trades_df.empty or prices_df.empty:
        print("❌ Missing database elements. Ensure Phase 1-3 ran successfully.")
        conn.close()
        return

    print("🧠 Processing statistical event study matrix...")

    # Pivot prices table to make calculations seamless: Rows=Dates, Columns=Tickers
    prices_pivot = prices_df.pivot(index='price_date', columns='ticker', values='close_price').sort_index()
    
    # Calculate daily percent returns
    returns_df = prices_pivot.pct_change().dropna()

    calculated_anomalies = []

    for _, trade in trades_df.iterrows():
        ticker = trade['ticker']
        trade_date = trade['trade_date']
        tx_type = trade['transaction_type'] # 'P' (Purchase) or 'S' (Sale)
        
        if ticker not in returns_df.columns or 'SPY' not in returns_df.columns:
            continue
            
        # Isolate dates after the trade occurred (the forward-looking evaluation window)
        post_trade_returns = returns_df[returns_df.index >= trade_date].head(20) # Look at next 20 trading days (~1 month)
        
        if post_trade_returns.empty:
            continue
            
        # Calculate Daily Abnormal Returns (AR = Stock Return - Market Return)
        # Note: For a true hedge-fund model we would use alpha/beta regression, 
        # but a market-adjusted spread is a rock-solid, production-ready baseline.
        stock_ret = post_trade_returns[ticker].values
        market_ret = post_trade_returns['SPY'].values
        abnormal_returns = stock_ret - market_ret
        
        # Sum them up to get Cumulative Abnormal Return (CAR)
        car = float(np.sum(abnormal_returns))
        
        # --- Compute the Composite Suspicion Score (0 to 100) ---
        # Rule 1: Purchases 'P' are suspicious if the stock skyrockets over the market (Positive CAR)
        # Rule 2: Sales 'S' are highly suspicious if the executive dodged a bullet and the stock crashes (Negative CAR)
        if tx_type == 'P':
            performance_factor = car * 100  # Positive CAR increases suspicion
        else:
            performance_factor = -car * 100 # Negative CAR increases suspicion
            
        # Standardize score into a clean 0 - 100 range using a sigmoidal transformation
        suspicion_score = int(100 / (1 + np.exp(-0.2 * (performance_factor - 5))))
        
        calculated_anomalies.append({
            "ticker": ticker,
            "insider_name": trade['insider_name'],
            "title": trade['title'],
            "trade_date": trade_date,
            "type": tx_type,
            "total_value": trade['total_value'],
            "car_20d": round(car * 100, 2), # percentage form
            "suspicion_score": max(0, min(100, suspicion_score)) # clamp boundaries
        })

    # Display compiled intelligence report
    results_df = pd.DataFrame(calculated_anomalies)
    
    print("\n🚨 🏆 --- QUANT RADAR ANOMALY LEADERBOARD --- 🏆 🚨")
    if not results_df.empty:
        # Rank by highest Suspicion Score
        results_df = results_df.sort_values(by="suspicion_score", ascending=False)
        print(results_df[['ticker', 'insider_name', 'type', 'total_value', 'car_20d', 'suspicion_score']].to_string(index=False))
    else:
        print("No trades qualified for abnormality scoring windows.")
        
    conn.close()

if __name__ == "__main__":
    calculate_anomaly_scores()