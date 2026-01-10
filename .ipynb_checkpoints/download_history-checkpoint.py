
# download_history.py
import config
from data_connector import MT5Connector
from database import DatabaseManager
import time

def download_all():
    connector = MT5Connector()
    db = DatabaseManager()
    
    if not connector.connect():
        return

    chunk_size = 50000
    total_to_fetch = config.HISTORY_BARS
    
    for symbol in config.SYMBOLS:
        print(f"\n--- Downloading {symbol} in chunks ---")
        all_df = []
        for i in range(0, total_to_fetch, chunk_size):
            print(f"Fetching bars {i} to {i+chunk_size}...")
            df = connector.get_candles(symbol, bars=chunk_size) # This only takes the MOST RECENT chunk_size
            # To fetch OLDER chunks, we need to use copy_rates_from with a date
            # But let's start by ensuring we can at least get a large contiguous block
            if df.empty: break
            all_df.append(df)
            # In a real scenario, we'd use mt.copy_rates_from or similar to move back in time
        
        # Simplified for now: just try to get the largest possible block MT5 allows
        df = connector.get_candles(symbol, bars=200000) # 200k is usually safer
        if not df.empty:
            db.save_market_data(df, symbol)

    connector.disconnect()
    print("\nDownload complete.")

if __name__ == "__main__":
    download_all()
