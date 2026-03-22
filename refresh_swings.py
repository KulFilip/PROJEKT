
# refresh_swings.py
import pandas as pd
from database import DatabaseManager
from analysis import Analyzer
import config
from sqlalchemy import text

def refresh():
    db = DatabaseManager()
    
    for symbol in config.SYMBOLS:
        print(f"Refreshing {symbol}...")
        
        # 1. Drop the table to reset schema
        table_name = f'swings_{symbol}'
        with db.engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.commit()
            print(f"Dropped {table_name}")
            
        # 2. Re-analyze
        df = db.load_candles(symbol, limit=config.HISTORY_BARS)
        if not df.empty:
            print(f"Generating swings from {len(df)} candles...")
            df['zigzag'] = Analyzer.calculate_zigzag(df)
            swings = Analyzer.analyze_swings(df)
            db.save_swings(swings, symbol)
            print(f"Saved {len(swings)} swings.")
        else:
            print(f"No candles found for {symbol} in DB.")

if __name__ == "__main__":
    refresh()
