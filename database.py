
# database.py
import pandas as pd
from sqlalchemy import create_engine, text
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

    def save_performance_metrics(self, model_name, symbol, scores):
        """
        Saves model performance metrics for comparison.
        """
        data = {
            'timestamp': [pd.Timestamp.now()],
            'model_name': [model_name],
            'symbol': [symbol],
            'direction_accuracy': [scores.get('direction_accuracy')],
            'price_mape': [scores.get('price_mape')],
            'range_mape': [scores.get('range_mape')],
            'duration_mape': [scores.get('duration_mape')]
        }
        df = pd.DataFrame(data)
        df.to_sql('backtest_performance', self.engine, if_exists='append', index=False)
        print(f"Logged performance for {model_name} to database.")

    def load_performance_comparison(self):
        """
        Loads all saved performance metrics for comparison.
        """
        try:
            return pd.read_sql("SELECT * FROM backtest_performance ORDER BY timestamp DESC", self.engine)
        except:
            return pd.DataFrame()
    def save_behavioral_signals(self, signals_df, symbol):
        """
        Saves behavioral analysis signals (Climax, Effort-Result, Absorption, etc.).
        Dynamically adds missing columns to the SQLite table.
        """
        if signals_df.empty:
            return
            
        table_name = f'behavioral_signals_{symbol}'
        
        # Ensure time is in a queryable format
        signals_df['time'] = pd.to_datetime(signals_df['time'])
        
        # Dynamically check/add columns
        try:
            # Check existing columns
            existing_cols = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 0", self.engine).columns.tolist()
            for col in signals_df.columns:
                if col not in existing_cols:
                    print(f"Adding missing column '{col}' to {table_name}")
                    # Basic mapping: all new columns as TEXT/NUMERIC based on type
                    dtype = "NUMERIC" if pd.api.types.is_numeric_dtype(signals_df[col]) else "TEXT"
                    with self.engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col} {dtype}"))
        except Exception:
            # Table probably doesn't exist yet, to_sql will create it
            pass

        # Append logic with basic duplication check (by time)
        try:
            last_time_query = f"SELECT MAX(time) FROM {table_name}"
            last_time_str = pd.read_sql(last_time_query, self.engine).iloc[0, 0]
            if last_time_str:
                last_time = pd.to_datetime(last_time_str)
                new_data = signals_df[signals_df['time'] > last_time]
            else:
                new_data = signals_df
        except:
            new_data = signals_df

        if not new_data.empty:
            new_data.to_sql(table_name, self.engine, if_exists='append', index=False)
            print(f"[{symbol}] Saved {len(new_data)} behavioral signals to DB.")

    def load_behavioral_signals(self, symbol):
        try:
            df = pd.read_sql(f"SELECT * FROM behavioral_signals_{symbol}", self.engine)
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
            return df
        except:
            return pd.DataFrame()
    def save_forex_metrics(self, df, symbol):
        """
        Saves calculated forex statistics (volume trends, rolling etc.) to DB.
        """
        if df.empty: return
        table_name = f'forex_metrics_{symbol}'
        
        # We only save columns that are not OHLCV (which are in candles table)
        # Assuming df has 'time' as index or column
        cols_to_save = [c for c in df.columns if c not in ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']]
        if 'time' not in cols_to_save: cols_to_save.append('time')
        
        metrics_df = df[cols_to_save]
        metrics_df['time'] = pd.to_datetime(metrics_df['time'])

        # Dynamic schema handling
        try:
            existing_cols = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 0", self.engine).columns.tolist()
            for col in metrics_df.columns:
                if col not in existing_cols:
                    dtype = "NUMERIC" if pd.api.types.is_numeric_dtype(metrics_df[col]) else "TEXT"
                    with self.engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col} {dtype}"))
        except Exception:
            pass

        # Save new data
        try:
            last_time_str = pd.read_sql(f"SELECT MAX(time) FROM {table_name}", self.engine).iloc[0, 0]
            if last_time_str:
                last_time = pd.to_datetime(last_time_str)
                new_data = metrics_df[metrics_df['time'] > last_time]
            else:
                new_data = metrics_df
        except:
            new_data = metrics_df

        if not new_data.empty:
            new_data.to_sql(table_name, self.engine, if_exists='append', index=False)
            print(f"[{symbol}] Saved {len(new_data)} forex metrics to DB.")

    def load_forex_metrics(self, symbol, limit=5000):
        try:
            query = f"SELECT * FROM forex_metrics_{symbol} ORDER BY time DESC LIMIT {limit}"
            df = pd.read_sql(query, self.engine)
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
            return df.sort_values('time').reset_index(drop=True)
        except:
            return pd.DataFrame()
