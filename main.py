
# main.py
import sys
import pandas as pd
from data_connector import MT5Connector
from database import DatabaseManager
from analysis import Analyzer
import config

def main():
    print(f"=== Midas Technical Analysis (Mode: {config.ACTIVE_METHOD}) ===")
    
    db = DatabaseManager()
    connector = MT5Connector()
    
    # 1. Sync Data if needed
    if config.DATA_SOURCE in ['MT5', 'BOTH']:
        if connector.connect():
            for symbol in config.SYMBOLS:
                print(f"Syncing {symbol}...")
                df = connector.get_candles(symbol, bars=config.HISTORY_BARS)
                db.save_market_data(df, symbol)
            connector.disconnect()

    # 2. Run Analysis
    for symbol in config.SYMBOLS:
        print(f"\n--- Analysis: {symbol} ---")
        
        df = db.load_candles(symbol, limit=config.HISTORY_BARS)
        if df.empty:
            print(f"No data for {symbol} in DB. Run 'python download_history.py' first.")
            continue
            
        print(f"Processing {len(df)} candles...")

        if config.ACTIVE_METHOD == 'ZIGZAG' or config.ACTIVE_METHOD == 'NN_PREDICTION':
            df['zigzag'] = Analyzer.calculate_zigzag(df)
            swings = Analyzer.analyze_swings(df)
            db.save_swings(swings, symbol)
            
            if config.ACTIVE_METHOD == 'NN_PREDICTION':
                prediction = Analyzer.predict_next_swing_nn(swings)
                if prediction:
                    print(f"Prediction: {prediction['direction']} to {prediction['target_price']:.2f}")

        elif config.ACTIVE_METHOD == 'SMT':
            # SMT requires two symbols, we'll use first two from config
            if len(config.SYMBOLS) >= 2:
                s1, s2 = config.SYMBOLS[0], config.SYMBOLS[1]
                if symbol == s1: # Run once for the pair
                    df1 = db.load_candles(s1)
                    df2 = db.load_candles(s2)
                    # Note: detect_smt_divergence logic would need to be in analysis.py
                    print(f"Running SMT Comparison between {s1} and {s2}...")
                    # Implementation details...
            else:
                print("SMT requires at least 2 symbols in config.SYMBOLS")

    print("\nDone.")

if __name__ == "__main__":
    main()
