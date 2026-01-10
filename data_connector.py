
# data_connector.py
import MetaTrader5 as mt
import pandas as pd
import config
from datetime import datetime

class MT5Connector:
    def __init__(self):
        self.connected = False

    def connect(self):
        if not mt.initialize():
            print("initialize() failed, error code =", mt.last_error())
            # Retry with explicit path if configured and failed
            # if hasattr(config, 'MT5_PATH') and config.MT5_PATH:
            #     mt.initialize(path=config.MT5_PATH)
            return False

        # Attempt Login
        if not mt.login(config.MT5_LOGIN, password=config.MT5_PASS, server=config.MT5_SERVER):
             print("failed to login, error code =", mt.last_error())
             mt.shutdown()
             return False
        
        self.connected = True
        print(f"Connected to MT5: {config.MT5_SERVER}")
        return True

    def disconnect(self):
        mt.shutdown()
        self.connected = False
        print("Disconnected from MT5")

    def get_candles(self, symbol, timeframe=config.TIMEFRAME, bars=config.HISTORY_BARS, start_pos=0):
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()

        rates = mt.copy_rates_from_pos(symbol, timeframe, start_pos, bars)
        if rates is None:
            print(f"Failed to copy rates for {symbol}, error code = {mt.last_error()}")
            return pd.DataFrame()
        
        df = pd.DataFrame(rates, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Ensure numeric
        # Ensure numeric and cast to compatible types for SQLite
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['tick_volume'] = df['tick_volume'].astype(int) # Standard int (int64 in py3)
        
        df['symbol'] = symbol
        return df

    def get_all_symbols_data(self):
        data = {}
        for symbol in config.SYMBOLS:
            df = self.get_candles(symbol)
            if not df.empty:
                data[symbol] = df
        return data
