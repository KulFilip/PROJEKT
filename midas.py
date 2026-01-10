import plotly.graph_objects as go
import datetime
import glob
import os
import subprocess
import numpy as np
import pandas as pd
import MetaTrader5 as mt
import pytz
import time
import shutil
import openpyxl
import itertools
import socket

from pandas import Timestamp
from plotly.subplots import make_subplots
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook, load_workbook
from datetime import datetime
from collections import OrderedDict
from scipy import signal
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from itertools import zip_longest

# Ustawienia wyświetlania pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

date_time = time.strftime("%Y-%m-%d-%H-%M")

# Poprawiona ścieżka - dodano r przed stringiem (raw string)
logFilePath = os.path.join(r"C:\Program Files\MetaTrader 5 IC Markets EU\MQL5\Logs",
                           "".join([str(datetime.now().date()).replace('-', ''), '.log']))

try:
    if os.path.exists(logFilePath):
        os.remove(logFilePath)
except Exception as e:
    print(f"no log file to remove: {e}")

# Dane logowania
mt_login = 52667259
mt_pass = '@sjVSZf8Fso7FE'
server = 'ICMarketsSC-Demo'

if not mt.initialize():
    print("initialize() failed, error code =", mt.last_error())
    quit()

if not mt.login(mt_login, mt_pass, server):
    print("failed to login, error code =", mt.last_error())
    mt.shutdown()
    quit()

account_info = mt.account_info()

# Lambdy i selekcja symboli
spreads = lambda x: mt.symbol_info_tick(x).ask - mt.symbol_info_tick(x).bid
select_symbol = lambda x: mt.symbol_select(x, True)

def selector(symbol_list):
    for x in symbol_list:
        mt.symbol_select(x.name, True)
    print('selected')

# Pobieranie symboli z wykluczeniem
all_symb = mt.symbols_get(
    group="*,!*DOG*,!*F40*,!*BTC*,!*ETH*,!*KSM*,!*XRP*,!*MTZ*,!*LTC*,!*GLM*,!*AAVE*,!*AVX*,!*BCH*,!*NOK*,!*SEK*,!*SGD*,!*TRY*,!*CZK*,!*PLN*,!*ADA*,!*HUF*,!*DKK*,!*EOS*,!*XLM*,!*DSH*,!*ZAR*,!*THB*,!*MXN*,!*DOT*,!*UNI*,!*BNB*,!*KMS*,!*LUN*,!*LNK*,*!HKD*,!*BND*,!*EXP.*,!*NYSE*,!*NAS*")

forex = pd.DataFrame(data=all_symb)
# Mapowanie nazw kolumn na podstawie indeksów MT5 (kolumna 93 to zazwyczaj 'name')
forex_symbol_list = forex.iloc[:, 93]
forex.set_index(forex_symbol_list, inplace=True)

# Obliczenia na ramce danych
forex['spread'] = (forex.iloc[:, 34] - forex.iloc[:, 31]).astype('float')
forex['time'] = forex[10]
forex['t_spread'] = forex[12]
forex['ticks_bookdepth'] = forex[14]
forex['bid'] = forex[31]
forex['bidhigh'] = forex[32]
forex['bidlow'] = forex[33]
forex['ask'] = forex[34]
forex['askhigh'] = forex[35]
forex['asklow'] = forex[36]
forex['last'] = forex[36]
forex['lasthigh'] = forex[37]
forex['lastlow'] = forex[38]
forex['volume_real'] = forex[39]
forex['volumehigh_real'] = forex[40]
forex['volumelow_real'] = forex[41]
forex['option_strike'] = forex[42]
forex['point'] = forex[43].astype('float64')
forex['trade_tick_value'] = forex[44]
forex['trade_tick_value_profit'] = forex[45]
forex['trade_tick_value_loss'] = forex[46]
forex['trade_tick_size'] = forex[47]
forex['trade_contract_size'] = forex[48]
forex['volume_min'] = forex[53]
forex['volume_max'] = forex[54]
forex['volume_step'] = forex[55]
forex['swap_long'] = forex[57]
forex['swap_short'] = forex[58]
forex['session_open'] = forex[64]
forex['session_close'] = forex[65]
forex['symbol_name'] = forex[93].astype('str')

from_high = forex['bidhigh'] - forex['bid']
from_low = forex['bid'] - forex['bidlow']
forex['daily_range'] = forex['bidhigh'] - forex['bidlow']

# Unikanie dzielenia przez zero przy obliczaniu procentów
daily_range_safe = forex['daily_range'].replace(0, np.nan)
prc_from_high = from_high / daily_range_safe * 100
prc_from_low = from_low / daily_range_safe * 100

marza = 0.002
forex['kapital'] = forex['bid'] / forex['trade_contract_size'] * marza
forex['from_high'] = prc_from_high
forex['from_low'] = prc_from_low

pct_high_filt = prc_from_high <= 45
pct_low_filt = prc_from_low < 45
# Korekta: zmieniono (pct_high_filt | pct_high_filt) na (pct_high_filt | pct_low_filt)
pct_filt = (pct_high_filt | pct_low_filt)

forex['zysk'] = ((forex['daily_range'] / forex['trade_contract_size'] * forex['trade_tick_value_profit']) - 
                 forex['t_spread'] * forex['trade_tick_value_profit']).astype(float)

forex['dayli_%_atr'] = (forex['zysk'] / forex['kapital'] * 100).astype(float)

# Filtrowanie głównej tablicy
columns_to_show = ['spread', 'time', 't_spread', 'dayli_%_atr', 'from_high', 'from_low', 'bid', 'bidhigh', 
                   'bidlow', 'ask', 'zysk', 'kapital', 'askhigh', 'asklow', 'last', 'lasthigh', 'lastlow', 
                   'point', 'trade_tick_value', 'trade_tick_value_profit', 'trade_tick_value_loss', 
                   'trade_tick_size', 'trade_contract_size', 'volume_min', 'volume_max', 'volume_step', 
                   'swap_long', 'swap_short', 'daily_range', 'symbol_name']

filter_forex_board = forex.loc[(forex['t_spread'] <= 200) & pct_filt, columns_to_show]

def get_key_levels(symbol):
    # Pobieranie danych (pozostawiono logikę pobierania wielu TF, mimo że użyto tylko H1)
    H1_rates = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_H1, 0, 24)
    if H1_rates is None: return pd.DataFrame()
    
    D1 = pd.DataFrame(H1_rates, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])
    D1['time'] = pd.to_datetime(D1['time'], unit='s')
    cols_numeric = ['open', 'high', 'low', 'close', 'tick_volume']
    D1[cols_numeric] = D1[cols_numeric].apply(pd.to_numeric)
    D1['symbol'] = symbol
    D1['timeframe'] = 'D1'
    return D1

symbol_list_filtered = filter_forex_board['symbol_name'].tolist()

def get_candles(symbol):
    rates = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_M1, 0, 200)
    if rates is None: return pd.DataFrame()
    
    df = pd.DataFrame(rates, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])
    df['time'] = pd.to_datetime(df['time'], unit='s')
    cols_numeric = ['open', 'high', 'low', 'close', 'tick_volume']
    df[cols_numeric] = df[cols_numeric].apply(pd.to_numeric)
    
    df['symbol'] = symbol
    df['o-c'] = df['open'] - df['close']
    df['kierunek'] = ['donbar' if d >= 0 else 'upbar' for d in df['o-c']]
    
    # Analiza wolumenu i anomalii
    df['max_vol_50'] = df['tick_volume'] > df['tick_volume'].rolling(window=50, min_periods=30).max().shift()
    df['zmiana_kier_up'] = (df['kierunek'].shift() == 'donbar') & (df['kierunek'] == 'upbar')
    df['zmiana_kier_down'] = (df['kierunek'].shift() == 'upbar') & (df['kierunek'] == 'donbar')
    df['vol50_zm'] = (df['max_vol_50'].shift() == True) & ((df['zmiana_kier_up']) | (df['zmiana_kier_down']))
    
    df['spread'] = abs(df['high'] - df['low'])
    df['ewm_vol_20'] = df['tick_volume'].ewm(span=60, adjust=False).mean()
    df['spr_ewm_20'] = df['spread'].ewm(span=60, adjust=False).mean()
    
    df['spdr_ch_20'] = (df['spread'] - df['spr_ewm_20']) / df['spr_ewm_20'] * 100
    df['vol_ch_20'] = (df['tick_volume'] - df['ewm_vol_20']) / df['ewm_vol_20'] * 100
    
    high_vol = df['tick_volume'] > (1.9 * df['ewm_vol_20'])
    df['high_vol'] = high_vol
    lower_sprd = df['spread'] > df['spr_ewm_20']
    df['low_sprd'] = high_vol & lower_sprd
    
    df['cum_max_high'] = df['high'].cummax()
    df['high_is_higher'] = df['high'] > df['cum_max_high'].shift()
    
    df['cum_min_low'] = df['low'].rolling(window=60, min_periods=10).min()
    df['lower_low'] = df['low'] < df['cum_min_low']
    
    df['vol_h_25'] = (df['tick_volume'].rolling(window=30).max().shift() > 
                      df['tick_volume'].rolling(window=25).max().shift())
    
    df['vol_is_lower'] = df['tick_volume'] < df['tick_volume'].shift()
    
    df['wfo_na_spadki'] = (df.high_is_higher) & (df.vol_h_25)
    df['wfo_na_wzrosty'] = (df.lower_low) & (df.vol_is_lower) & (high_vol)
    
    # Separacja barów dla średnich kroczących wolumenu
    filtr_up_bar = df[df['kierunek'] == 'upbar']
    filtr_don_bar = df[df['kierunek'] == 'donbar']

    # Obliczanie trendów wolumenu (z użyciem ffill() zamiast fillna(method='ffill'))
    for span in [4, 7, 15, 30]:
        up_col = f'upvm{span}'
        dn_col = f'dnvm{span}'
        trend_col = f'vol_trend{span}'
        
        df[up_col] = filtr_up_bar['tick_volume'].ewm(span=span, adjust=False).mean()
        df[dn_col] = filtr_don_bar['tick_volume'].ewm(span=span, adjust=False).mean()
        
        df[up_col] = df[up_col].ffill()
        df[dn_col] = df[dn_col].ffill()
        
        df[trend_col] = (df[up_col] - df[dn_col]).astype(float)
        
        df[f'up_trend_{span}'] = df[trend_col] > 0
        df[f'dn_trend_{span}'] = (df[dn_col] - df[up_col]) > 0
        df[f'up_trend_{span}'] = df[f'up_trend_{span}'].ffill()
        df[f'dn_trend_{span}'] = df[f'dn_trend_{span}'].ffill()

    return df

# Przykładowe wywołanie dla EURUSD (zgodnie z logiką kodu)
eurusd_data = get_candles('EURUSD')
print(eurusd_data.tail())