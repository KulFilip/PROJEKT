
# config.py
import os
import MetaTrader5 as mt

# MT5 Connection Settings
MT5_LOGIN = 52667259
MT5_PASS = '@sjVSZf8Fso7FE'
MT5_SERVER = 'ICMarketsSC-Demo'
# MT5_PATH = r"C:\Program Files\MetaTrader 5 IC Markets EU\terminal64.exe" # Uncomment if needed

# Database Settings
DB_NAME = 'market_data.db'
DB_CONNECTION_STRING = f'sqlite:///{DB_NAME}'

# Analysis Settings
SYMBOLS = ['XAUUSD', 'XAGUSD']
TIMEFRAME = mt.TIMEFRAME_M1
HISTORY_BARS = 2000000  # Approx 3 years of M1 data (1.5M+ bars)
DATA_SOURCE = 'DB'      # Options: 'MT5' (fresh), 'DB' (cached), 'BOTH' (sync then DB)

# Execution Control
ACTIVE_METHOD = 'NN_PREDICTION' # Options: 'ZIGZAG', 'SMT', 'NN_PREDICTION'

# ZigZag Settings
ZIGZAG_DEPTH = 12
ZIGZAG_DEVIATION = 5
ZIGZAG_BACKSTEP = 3
POINT = 0.01  # For XAUUSD
