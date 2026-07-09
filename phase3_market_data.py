import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

DB_NAME = "insider_radar.db"

def init_market_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        price_date TEXT,
        close_price REAL,
        UNIQUE(ticker, price_date)
    )
    """)
    conn.commit()
    conn.close()

def fetch_and_store_prices():
    conn = sqlite3.connect(DB_NAME)
    trades_df = pd.read_sql_query("SELECT DISTINCT ticker, trade_date FROM insider_trades", conn)
    
    if trades_df.empty:
        print("❌ No tickers found in database. Run Phase 1 first!")
        conn.close()
        return

    init_market_table()
    cursor = conn.cursor()
    
    tickers = list(trades_df['ticker'].unique())
    if "SPY" not in tickers:
        tickers.append("SPY")
        
    print(f"📡 Syncing market infrastructure for: {tickers}")
    
    min_date_str = trades_df['trade_date'].min()
    start_date = (datetime.strptime(min_date_str, "%Y-%m-%d") - timedelta(days=5)).strftime("%Y-%m-%d")
    end_date = (datetime.strptime(min_date_str, "%Y-%m-%d") + timedelta(days=45)).strftime("%Y-%m-%d")
    
    for ticker in tickers:
        print(f"🔄 Downloading historical bars for {ticker}...")
        
        # FIX: multi_level_index=False flattens out the tables back to standard single columns!
        df = yf.download(ticker, start=start_date, end=end_date, multi_level_index=False, progress=False)
        
        if df.empty:
            print(f"⚠️ Yahoo Finance returned empty data for {ticker}.")
            continue
            
        inserted_rows = 0
        for date_idx, row in df.iterrows():
            p_date = date_idx.strftime('%Y-%m-%d')
            close_val = float(row['Close'])
            
            cursor.execute("""
            INSERT OR IGNORE INTO market_prices (ticker, price_date, close_price)
            VALUES (?, ?, ?)
            """, (ticker, p_date, close_val))
            
            if cursor.rowcount > 0:
                inserted_rows += 1
                
        print(f"✅ Successfully saved {inserted_rows} price rows for {ticker}.")
        
    conn.commit()
    conn.close()
    print("💾 Pricing Sync Complete!")

if __name__ == "__main__":
    fetch_and_store_prices()