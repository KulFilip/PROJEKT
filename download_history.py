
# download_history.py
import config
from data_connector import MT5Connector
from database import DatabaseManager
import pandas as pd
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
        all_chunks = []
        for i in range(0, total_to_fetch, chunk_size):
            print(f"Fetching bars {i} to {i+chunk_size}...")
            df = connector.get_candles(symbol, bars=chunk_size, start_pos=i)
            
            if df.empty:
                print(f"No more data available for {symbol} at pos {i}")
                break
            
            all_chunks.append(df)
            time.sleep(0.1) # Small sleep to be nice to MT5
        
        if all_chunks:
            full_df = pd.concat(all_chunks).drop_duplicates(subset=['time']).sort_values('time')
            print(f"Saving {len(full_df)} total bars for {symbol} to database...")
            db.save_market_data(full_df, symbol)
        else:
            print(f"No data fetched for {symbol}")

    connector.disconnect()
    print("\nDownload complete.")

if __name__ == "__main__":
    download_all()
