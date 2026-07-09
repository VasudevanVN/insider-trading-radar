import sqlite3
import pandas as pd

DB_NAME = "insider_radar.db"

def inspect_saved_data():
    conn = sqlite3.connect(DB_NAME)
    
    print("📋 --- Insider Trades Table ---")
    trades = pd.read_sql_query("SELECT * FROM insider_trades LIMIT 5", conn)
    print(trades if not trades.empty else "Empty table")
    
    print("\n📈 --- Market Prices Table Summary ---")
    prices_summary = pd.read_sql_query(
        "SELECT ticker, COUNT(*), MIN(price_date), MAX(price_date) FROM market_prices GROUP BY ticker", conn
    )
    print(prices_summary if not prices_summary.empty else "Empty table")
    
    conn.close()

if __name__ == "__main__":
    inspect_saved_data()