import sqlite3

DB_NAME = "insider_radar.db"

def init_database():
    """
    Creates the SQLite database and initializes the insider_trades table.
    """
    # Connect to database file (it will be created automatically if it doesn't exist)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create table for insider trades
    # We use a UNIQUE constraint across ticker, insider_name, trade_date, and total_value to prevent duplicates.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insider_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        insider_name TEXT,
        title TEXT,
        trade_date TEXT,
        transaction_type TEXT,
        shares REAL,
        price REAL,
        total_value REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, insider_name, trade_date, total_value)
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"📦 Database '{DB_NAME}' initialized successfully with 'insider_trades' table.")

def save_trades_to_db(trades_list):
    """
    Takes a list of trade dictionaries (from Phase 1) and inserts them into the DB.
    """
    if not trades_list:
        print("No trades provided to save.")
        return 0
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    insert_query = """
    INSERT OR IGNORE INTO insider_trades 
    (ticker, insider_name, title, trade_date, transaction_type, shares, price, total_value)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    inserted_count = 0
    for t in trades_list:
        cursor.execute(insert_query, (
            t['ticker'],
            t['insider_name'],
            t['title'],
            t['trade_date'],
            t['transaction_type'],
            t['shares'],
            t['price'],
            t['total_value']
        ))
        # If rows were affected, it means it wasn't a duplicate and got saved
        if cursor.rowcount > 0:
            inserted_count += 1
            
    conn.commit()
    conn.close()
    return inserted_count

# --- Test the Database Module ---
if __name__ == "__main__":
    init_database()