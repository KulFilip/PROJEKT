
# database.py
import pandas as pd
from sqlalchemy import create_engine
import config

class DatabaseManager:
    def __init__(self, connection_string=config.DB_CONNECTION_STRING):
        self.engine = create_engine(connection_string)

    def save_market_data(self, df, symbol):
        """
        Saves OHLCV data to the database.
        Appends new data, ignores duplicates if possible (handled by logic or ignoring errors).
        For simplicity in SQLite without primary key constraints tailored for time, 
        we will load existing max time and append only new.
        """
        if df.empty:
            return

        table_name = f'candles_{symbol}'
        
        # Check last time
        try:
            last_time_query = f"SELECT MAX(time) FROM {table_name}"
            last_time = pd.read_sql(last_time_query, self.engine).iloc[0, 0]
        except Exception:
            last_time = None

        if last_time:
            # Filter new data
            new_data = df[df['time'] > last_time]
        else:
            new_data = df

        if not new_data.empty:
            new_data.to_sql(table_name, self.engine, if_exists='append', index=False)
            print(f"[{symbol}] Saved {len(new_data)} new candles to DB.")
        else:
            print(f"[{symbol}] No new data to save.")

    def save_swings(self, swings_df, symbol):
        """
        Saves swing analysis data.
        """
        if swings_df.empty:
            return
            
        table_name = f'swings_{symbol}'
        # Similar logic: append. Ideally we'd have unique IDs. 
        # For now, we append all for analysis, or could filter by start_time.
        try:
            last_time_query = f"SELECT MAX(start_time) FROM {table_name}"
            last_time = pd.read_sql(last_time_query, self.engine).iloc[0, 0]
        except:
            last_time = None
            
        if last_time:
            new_data = swings_df[swings_df['start_time'] > last_time]
        else:
            new_data = swings_df

        if not new_data.empty:
            # Convert dict/lists to string if necessary, but here data is simple
            new_data.to_sql(table_name, self.engine, if_exists='append', index=False)
            print(f"[{symbol}] Saved {len(new_data)} swings to DB.")

    def load_swings(self, symbol):
        try:
            df = pd.read_sql(f"SELECT * FROM swings_{symbol}", self.engine)
            if not df.empty:
                df['start_time'] = pd.to_datetime(df['start_time'])
                df['end_time'] = pd.to_datetime(df['end_time'])
            return df
        except:
            return pd.DataFrame()
            
    def load_candles(self, symbol, limit=5000):
        try:
            query = f"SELECT * FROM candles_{symbol} ORDER BY time DESC LIMIT {limit}"
            df = pd.read_sql(query, self.engine)
            if not df.empty:
                 df['time'] = pd.to_datetime(df['time'])
            return df.sort_values('time').reset_index(drop=True)
        except:
            return pd.DataFrame()
