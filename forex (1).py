import plotly.graph_objects as go
import datetime
import glob
import os
import subprocess

from pandas import Timestamp
from plotly.subplots import make_subplots
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import MetaTrader5 as mt
import pytz
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
from datetime import datetime
import time
import shutil
import openpyxl
from openpyxl import Workbook
from openpyxl import load_workbook
from collections import OrderedDict
from scipy import signal
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import itertools
import socket
from scipy.signal import find_peaks
import datetime
from itertools import zip_longest

date_time = time.strftime("%Y-%m-%d-%H-%M")
logFilePath = os.path.join("C:\Program Files\MetaTrader 5 IC Markets EU\MQL5\Logs",
                           "".join([str(datetime.date.today()).replace('-', ''), '.log']))
try:
    os.remove(logFilePath)
except:
    print("no log file to remove")
# TODO: choose symbols: lowest fees,move furthest, soonest,quickest
mt_login = 51070207
mt_pass = 'ZzDvRUj5'
server = 'ICMarketsSC-Demo'
mt.initialize()
mt.login(mt_login, mt_pass, server)
account_info = mt.account_info()
# spread by lambda # we use select to make sure all symbols accessible
spreads = lambda x: mt.symbol_info_tick(x)._asdict()['ask'] - mt.symbol_info_tick(x)._asdict()['bid']
select_symbol = lambda x: mt.symbol_select(x, True)
symbol_list = mt.symbols_get()


def selector(symbol_list):
    for x in symbol_list:
        select_symbol
    print('selected')


# Get all symbols avilable to us
select_symbol = lambda x: mt.symbol_select(x, True)
path_list = lambda x: path_list.append(x)
all_symb = mt.symbols_get(
    group="*,!*DOG*,!*F40*,!*BTC*,!*ETH*,!*KSM*,!*XRP*,!*MTZ*,!*LTC*,!*GLM*,!*AAVE*,!*AVX*,!*BCH*,!*NOK*,!*SEK*,!*SGD*,!*TRY*,!*CZK*,!*PLN*,!*ADA*,!*HUF*,!*DKK*,!*EOS*,!*XLM*,!*DSH*,!*ZAR*,!*THB*,!*MXN*,!*DOT*,!*UNI*,!*BNB*,!*KMS*,!*LUN*,!*LNK*,*!HKD*,!*BND*,!*EXP.*,!*NYSE*,!*NAS*")


def selector(x):
    return select_symbol


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
forex = pd.DataFrame(data=all_symb)
# created a list of symbols met group method criteria
forex_symbol_list = forex.iloc[:, 93]
forex.set_index(forex_symbol_list, inplace=True)
# bid 31 , ask 34 ask@sell bid@buy # method doesn's return real results!
# column no. 13 is called # spread check type and proceed with group
# forex[93].apply(pd.to_numeric
# spread_filt = forex.loc[:,['spread']]
forex['spread'] = (forex.iloc[:, 34] - forex.iloc[:, 31]).astype('float')
# forex.sort_values(by='spread',ascending=True, inplace=True)
how_many = forex.shape[0]
forex['time'] = forex[10]
forex['t_spread'] = forex[12]
forex['ticks_bookdepth'] = forex[14]
forex['bid'] = forex[31]
# bidhigh=13536.18, bidlow=13304.58, ask=13531.78, askhigh=13540.58, asklow=13310.18,
forex['bidhigh'] = forex[32]
forex['bidlow'] = forex[33]
forex['ask'] = forex[34]
forex['askhigh'] = forex[35]
forex['asklow'] = forex[36]
forex['askhigh'] = forex[35]
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
forex['daily_range'] = daily_range = forex['bidhigh'] - forex['bidlow']
prc_from_high = from_high / daily_range * 100
prc_from_low = from_low / daily_range * 100
marza = 0.002
forex['kapital'] = forex['bid'] / forex['trade_contract_size'] * marza
forex['from_high'] = prc_from_high
forex['from_low'] = prc_from_low
pct_high_filt = prc_from_high <= 45
pct_low_filt = prc_from_low < 45
pct_filt = (pct_high_filt | pct_high_filt)
forex['zysk'] = ((forex['daily_range'] / forex['trade_contract_size'] * forex['trade_tick_value_profit']) - forex[
    't_spread'] * forex['trade_tick_value_profit'])
forex['zysk'].astype(float)
forex['dayli_%_atr'] = forex['zysk'] / forex['kapital'] * 100
forex['dayli_%_atr'].astype(float)

filter_forex_board = forex.loc[(forex['t_spread'] <= 200) & pct_filt, ['spread',
                                                                       'time',
                                                                       't_spread',
                                                                       'dayli_%_atr',
                                                                       'from_high',
                                                                       'from_low',
                                                                       'bid',
                                                                       'bidhigh',
                                                                       'bidlow',
                                                                       'ask',
                                                                       'zysk',
                                                                       'kapital',
                                                                       'askhigh',
                                                                       'asklow',
                                                                       'last',
                                                                       'lasthigh',
                                                                       'lastlow',
                                                                       'point',
                                                                       'trade_tick_value',
                                                                       'trade_tick_value_profit',
                                                                       'trade_tick_value_loss',
                                                                       'trade_tick_size',
                                                                       'trade_contract_size',
                                                                       'volume_min',
                                                                       'volume_max',
                                                                       'volume_step',
                                                                       'swap_long',
                                                                       'swap_short',
                                                                       'from_high',
                                                                       'from_low', 'daily_range', 'symbol_name']]
filter_forex_symbol_name = forex.loc[forex['symbol_name'] == 'EURUSD', ['spread',
                                                                        'time',
                                                                        't_spread',
                                                                        'zysk',
                                                                        'from_high', 'from_low', 'dayli_%_atr',
                                                                        'kapital',
                                                                        'bid',
                                                                        'bidhigh',
                                                                        'bidlow',
                                                                        'ask',
                                                                        'askhigh',
                                                                        'asklow',
                                                                        'last',
                                                                        'lasthigh',
                                                                        'lastlow',
                                                                        'point',
                                                                        'trade_tick_value',
                                                                        'trade_tick_value_profit',
                                                                        'trade_tick_value_loss',
                                                                        'trade_tick_size',
                                                                        'trade_contract_size',
                                                                        'volume_min',
                                                                        'volume_max',
                                                                        'volume_step',
                                                                        'swap_long',
                                                                        'swap_short',
                                                                        'from_high',
                                                                        'from_low', 'daily_range', 'symbol_name']]


def get_key_levels(symbol):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    D1 = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_D1, 0, 7)
    H1 = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_H1, 0, 24)
    H4 = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_H1, 0, 24)
    M15 = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_M15, 0, 32)
    M5 = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_M15, 0, 96)
    M1 = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_M1, 0, 120)

    D1 = pd.DataFrame(H1, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])
    D1['time'] = pd.to_datetime(D1['time'], unit='s')
    D1[['open', 'high', 'low', 'close', 'tick_volume']] = D1[['open', 'high', 'low', 'close', 'tick_volume']].apply(
        pd.to_numeric)
    D1['symbol'] = symbol
    D1['timeframe'] = 'D1'
    # D1['high%'] = D1['high'].pct_change(periods=1) * 1000
    # D1['low%'] = D1['low'].pct_change(periods=1) * 1000
    # df['high%'].sum() - df['low%'].sum()
    # pandas.concat(objs, *, axis=0, join='outer', ignore_index=False, keys=None, levels=None, names=None, verify_integrity=False, sort=False, copy=True)
    return D1


# best_profit = filter_forex_board.nlargest(250, 'dayli_%_atr', keep='all')
# from_high = filter_forex_board.nlargest(15, 'from_high',keep='all')
# from_low = filter_forex_board.nlargest(15, 'from_low',keep='all')
symbol_list_filtered = []
for x in filter_forex_board['symbol_name']:
    symbol_list_filtered.append(x)


# group by low spread ?
def get_candles(symbol):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    # rates = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_M1, 0, 500)
    timezone = pytz.timezone("Etc/UTC")
    # create 'datetime' objects in UTC time zone to avoid the implementation of a local time zone offset
    # utc_from = datetime(2023, 5, 8, tzinfo=timezone)
    # utc_to = datetime(2023, 5, 10, tzinfo=timezone)
    # rates = mt.copy_rates_range(symbol, mt.TIMEFRAME_M1, utc_from, utc_to)
    # rates = mt.copy_rates_from(symbol, mt.TIMEFRAME_M1, utc_from, 1000)
    rates = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_M1, 0, 200)
    # high_24 = mt.copy_rates_from_pos(symbol, mt.TIMEFRAME_M1, 0, 120)
    df = pd.DataFrame(rates, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume'])
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df[['open', 'high', 'low', 'close', 'tick_volume']] = df[['open', 'high', 'low', 'close', 'tick_volume']].apply(
        pd.to_numeric)
    df['symbol'] = symbol
    df['o-c'] = df['open'] - df['close']
    df['kierunek'] = ['donbar' if d >= 0 else 'upbar' for d in df['o-c']]
    df['max_vol_50'] = df['tick_volume'] > df['tick_volume'].rolling(window=50, min_periods=30).max().shift()
    df['zmiana_kier_up'] = (df['kierunek'].shift() == 'donbar') & (df['kierunek'] == 'upbar')
    # df['zmiana_kier'] = ['up' if (df['kierunek'].shift() == 'donbar') & (df['kierunek'] == 'upbar') else 'dn' for d in df['kierunek']]
    df['zmiana_kier_down'] = (df['kierunek'].shift() == 'upbar') & (df['kierunek'] == 'donbar')
    df['vol50_zm'] = (df['max_vol_50'].shift() == True) & (
            (df['zmiana_kier_up'] == True) | (df['zmiana_kier_down'] == True))
    df['consecutive'] = (df['kierunek'] == df['kierunek'].shift())
    df['spread'] = abs(df['high'] - df['low'])
    df['ewm_vol_20'] = df['tick_volume'].ewm(span=60, ignore_na=True, adjust=False).mean()
    df['spr_ewm_20'] = df['spread'].ewm(span=60, ignore_na=True, adjust=False).mean()
    df['vol_ch'] = df['tick_volume'].pct_change()
    df['spdr_ch_20'] = (df['spread'] - df['spr_ewm_20']) / df['spr_ewm_20'] * 100
    df['vol_ch_20'] = (df['tick_volume'] - df['ewm_vol_20']) / df['ewm_vol_20'] * 100
    # df['spdr_ch_high'] = df['spdr_ch_20'] > 1.9 * df['spr_ewm_20']
    df['v_ch_high'] = df['vol_ch_20'] > 1.9 * df['ewm_vol_20']
    df['spread_anomaly'] = df['spdr_ch_20'] > 1.9 * df['spr_ewm_20']

    high_vol = df['tick_volume'] > 1.9 * df['ewm_vol_20']
    df['high_vol'] = high_vol
    lower_sprd = df['spread'] > df['spr_ewm_20']
    higher_sread = df['spread'] > df['spr_ewm_20']

    df['lower_sprd'] = lower_sprd
    df['low_sprd'] = high_vol & lower_sprd
    df['cum_max_high'] = df['high'].cummax()
    df['high_is_higher'] = df['high'] > df['cum_max_high'].shift()
    # df['hhigh'] = df['high'] > df['cum_max_high'].shift()
    df['rowl_high_max'] = (df['high'].rolling(window=30, min_periods=2).max() > df['high'].rolling(window=20,
                                                                                                   min_periods=2).max().shift())
    # df['cum_min_low'] = df['low'].min()
    # df['lower_low'] = df['cum_min_low'] < df['cum_min_low'].shift()
    df['cum_min_low'] = df['low'].rolling(window=60, min_periods=10).min()
    df['lower_low'] = df['low'] < df['cum_min_low']
    df['cumm_high_vol'] = df['tick_volume'].cummax()
    df['vol_roll'] = df['tick_volume'] > df['tick_volume'].rolling(window=25, min_periods=5).max().shift()
    df['spr_roll'] = df['spread'] > df['spread'].rolling(window=25, min_periods=5).max()
    df['vol_h_25'] = (
            df['tick_volume'].rolling(window=30, min_periods=2).max().shift() > df['tick_volume'].rolling(window=25,
                                                                                                          min_periods=2).max().shift())
    # df.rolling(window=5).mean()
    # df['low'].rolling(window=100, min_periods=10).min()

    df['cumm_low_vol'] = df['tick_volume'].cummin()

    df['vol_is_lower'] = df['tick_volume'] < df['tick_volume'].shift()
    wfo_na_spadki = (df.high_is_higher == True) & (df.vol_h_25 == True)
    df['wfo_na_spadki'] = wfo_na_spadki
    wfo_na_wzrosty = (df.lower_low == True) & (df.vol_is_lower == True) & (high_vol == True)
    df['wfo_na_wzrosty'] = wfo_na_wzrosty
    wfospd = df.loc[wfo_na_spadki, ['time', 'open', 'high', 'low', 'close', 'tick_volume', ]]
    # df['wfospd'] = wfospd
    wfowzr = df.loc[wfo_na_wzrosty, ['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    upbar = df['kierunek'] == 'upbar'
    donbar = df['kierunek'] == 'donbar'
    filtr_up_bar = df.loc[upbar, ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'kierunek']]
    filtr_don_bar = df.loc[donbar, ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'kierunek']]

    dnvm7 = filtr_don_bar['tick_volume'].ewm(span=7, ignore_na=True, adjust=False).mean()
    upvm7 = filtr_up_bar['tick_volume'].ewm(span=7, ignore_na=True, adjust=False).mean()
    df['upvm7'] = upvm7
    df['upvm7'].fillna(method="ffill", inplace=True)
    df['dnvm7'] = dnvm7
    df['dnvm7'].fillna(method="ffill", inplace=True)
    # df['dnvm7'][0] = df['tick_volume'][0]
    df['vol_trend7'] = (df['upvm7'] - df['dnvm7'])
    df['vol_trend7'].astype('float')
    dnvm4 = filtr_don_bar['tick_volume'].ewm(span=4, ignore_na=True, adjust=False).mean()
    upvm4 = filtr_up_bar['tick_volume'].ewm(span=4, ignore_na=True, adjust=False).mean()
    df['upvm4'] = upvm4
    df['upvm4'].fillna(method="ffill", inplace=True)
    df['dnvm4'] = dnvm4
    df['dnvm4'].fillna(method="ffill", inplace=True)
    # df['dnvm4'][0] = df['tick_volume'][0]
    df['vol_trend4'] = (df['upvm4'] - df['dnvm4'])
    df['vol_trend4'].astype('float')
    df['vol_trend4'] = pd.to_numeric(df['vol_trend4'], errors='ignore')
    df['vol_trend7'] = pd.to_numeric(df['vol_trend4'], errors='ignore')

    dnvm15 = filtr_don_bar['tick_volume'].ewm(span=15, ignore_na=True, adjust=False).mean()
    upvm15 = filtr_up_bar['tick_volume'].ewm(span=15, ignore_na=True, adjust=False).mean()
    dnvm30 = filtr_don_bar['tick_volume'].ewm(span=30, ignore_na=True, adjust=False).mean()
    upvm30 = filtr_up_bar['tick_volume'].ewm(span=30, ignore_na=True, adjust=False).mean()
    df['upvm15'] = upvm15
    df['upvm15'].fillna(method="ffill", inplace=True)
    df['dnvm15'] = dnvm15
    df['dnvm15'].fillna(method="ffill", inplace=True)
    # df['dnvm15'][0] = df['tick_volume'][0]
    df['upvm30'] = upvm30
    df['upvm30'].fillna(method="ffill", inplace=True)
    df['dnvm30'] = dnvm30
    df['dnvm30'].fillna(method="ffill", inplace=True)
    # df['dnvm30'][0] = df['tick_volume'][0]
    df['vol_trend15'] = (df['upvm15'] - df['dnvm15'])
    df['vol_trend15'].fillna(method="ffill", inplace=True)
    df['vol_trend15'].astype('float')
    df['vol_trend15'] = pd.to_numeric(df['vol_trend15'], errors='ignore')
    # df['vol_trend30'].fillna(method="ffill", inplace=True)
    df['vol_trend30'] = (df['upvm30'] - df['dnvm30'])
    df['vol_trend30'] = pd.to_numeric(df['vol_trend30'], errors='ignore')
    # df['vol_trend30_m'] = abs(df['vol_trend30'].ewm(span=30, ignore_na=True, adjust=False).mean())
    # df['vol_trend15_m'] = abs(df['vol_trend15'].ewm(span=15, ignore_na=True, adjust=False).mean())
    # df['vol_trend4_m'] = abs(df['vol_trend4'].ewm(span=4, ignore_na=True, adjust=False).mean())
    # df['vol_trend7_m'] = abs(df['vol_trend7'].ewm(span=7, ignore_na=True, adjust=False).mean())
    df['up_trend_30'] = ((df['upvm30'] - df['dnvm30']) > 0)
    df['up_trend_30'].fillna(method="ffill", inplace=True)
    df['dn_trend_30'] = ((df['dnvm30'] - df['upvm30']) > 0)
    df['dn_trend_30'].fillna(method="ffill", inplace=True)
    df['up_trend_15'] = ((df['upvm15'] - df['dnvm15']) > 0)
    df['up_trend_15'].fillna(method="ffill", inplace=True)
    df['dn_trend_15'] = ((df['dnvm15'] - df['upvm15']) > 0)
    df['dn_trend_15'].fillna(method="ffill", inplace=True)
    df['up_trend_4'] = ((df['upvm4'] - df['dnvm4']) > 0)
    df['up_trend_4'].fillna(method="ffill", inplace=True)
    df['dn_trend_4'] = ((df['dnvm4'] - df['upvm4']) > 0)
    df['dn_trend_4'].fillna(method="ffill", inplace=True)
    df['up_trend_7'] = ((df['upvm7'] - df['dnvm7']) > 0)
    df['up_trend_7'].fillna(method="ffill", inplace=True)
    df['dn_trend_7'] = ((df['dnvm7'] - df['upvm7']) > 0)
    df['dn_trend_7'].fillna(method="ffill", inplace=True)
    # df['up_dn_15'] = (df['dnvm15']/df['upvm15'])
    # df['strenght_15'] = (df['up_dn_15'] > (df['up_dn_15'].mean() * 0.9))

    # ['uptrend' if x > 0 & (df['vol_trend15'] > 1.7 * df['vol_trend30_m']) else if  in df['vol_trend15']]
    # df['vol_trend30'].astype('float')
    # df['vol_trend30_dn'] = pd.to_numeric(df['vol_trend30'], errors='coerce')
    # df['vol_trend30_dn']= pd.to_numeric(df['vol_trend30dn'], errors='coerce')
    # df['vol_trend30_dn'] = [x for d in df['vol_trend30'] if x <= 0]
    # df['vol_trend30n'] = ['mniejszy' if x >= 0 else 'wiekszy' for d in df['vol_trend30'].astype('float')]

    # HIGHER HIGH LOWER LOW
    df['ll'] = df['low'] < df['low'].shift()
    df['ll'].astype('bool')
    df['lh'] = df['high'] < df['high'].shift()
    df['lh'].astype('bool')
    df['hh'] = df['high'] > df['high'].shift()
    df['hh'].astype('bool')
    df['hl'] = df['low'] > df['low'].shift()
    df['hl'].astype('bool')
    # WFO NA WZROSTY
    df['cummax_vol'] = df['tick_volume'].cummax()
    df['lower_vol'] = df['tick_volume'] < df['cummax_vol']
    df['l3d'] = df['low'] - df['low'].shift()
    na_wzrosty = (df['l3d'] < 0) & df['lower_vol'] == True
    df['na_wzrosty'] = na_wzrosty
    # Wfo na spadki
    df['h3d'] = df['high'] - df['high'].shift()
    na_spadki = ((df['h3d'] > 0) & df['lower_vol'] == True)
    df['na_spadki'] = na_spadki
    uptest = ((df['tick_volume'] > df['tick_volume'].shift()) & (df['kierunek'] == 'upbar') & (
            df['tick_volume'].shift() < df['tick_volume'].shift(2)) & (df['kierunek'].shift() == 'donbar') & (
                      df['kierunek'].shift(2) == 'donbar'))
    df['up_test'] = uptest
    down_test = ((df['tick_volume'] > df['tick_volume'].shift()) & (df['kierunek'] == 'donbar') & (
            df['kierunek'].shift() == 'upbar') & (df['kierunek'].shift(2) == 'upbar') & (
                         df['tick_volume'].shift() < df['tick_volume'].shift(2)))
    df['down_test'] = down_test
    # rolling vol
    rv5 = df['tick_volume'].rolling(window=5, min_periods=1, center=False).max()
    rv10 = df['tick_volume'].rolling(window=10, min_periods=1, center=False).max()
    rv15 = df['tick_volume'].rolling(window=15, min_periods=1, center=False).max()
    rv20 = df['tick_volume'].rolling(window=20, min_periods=1, center=False).max()
    rv30 = df['tick_volume'].rolling(window=30, min_periods=1, center=False).max()
    rv60 = df['tick_volume'].rolling(window=60, min_periods=1, center=False).max()
    rv90 = df['tick_volume'].rolling(window=90, min_periods=1, center=False).max()
    rv120 = df['tick_volume'].rolling(window=120, min_periods=1, center=False).max()
    rv180 = df['tick_volume'].rolling(window=180, min_periods=1, center=False).max()
    # rolling high
    rolh5 = df['high'].rolling(window=5, min_periods=1, center=False).max()
    rolh10 = df['high'].rolling(window=10, min_periods=1, center=False).max()
    rolh15 = df['high'].rolling(window=15, min_periods=1, center=False).max()
    rolh20 = df['high'].rolling(window=20, min_periods=1, center=False).max()
    rolh30 = df['high'].rolling(window=30, min_periods=1, center=False).max()
    rolh60 = df['high'].rolling(window=60, min_periods=1, center=False).max()
    rolh90 = df['high'].rolling(window=90, min_periods=1, center=False).max()
    rolh120 = df['high'].rolling(window=120, min_periods=120, center=False).max()
    rolh180 = df['high'].rolling(window=180, min_periods=1, center=False).max()
    rolh240 = df['high'].rolling(window=240, min_periods=1, center=False).max()
    rolh480 = df['high'].rolling(window=480, min_periods=1, center=False).max()
    rolh1000 = df['high'].rolling(window=1000, min_periods=1, center=False).max()
    # rolling_low
    roll5 = df['low'].rolling(window=5, min_periods=1, center=False).min()
    roll10 = df['low'].rolling(window=10, min_periods=1, center=False).min()
    roll15 = df['low'].rolling(window=15, min_periods=1, center=False).min()
    roll20 = df['low'].rolling(window=20, min_periods=1, center=False).min()
    roll30 = df['low'].rolling(window=30, min_periods=1, center=False).min()
    roll60 = df['low'].rolling(window=60, min_periods=1, center=False).min()
    roll90 = df['low'].rolling(window=90, min_periods=1, center=False).min()
    roll120 = df['low'].rolling(window=120, min_periods=1, center=False).min()
    roll180 = df['low'].rolling(window=180, min_periods=1, center=False).min()
    roll240 = df['low'].rolling(window=240, min_periods=1, center=False).min()
    roll480 = df['low'].rolling(window=480, min_periods=1, center=False).min()
    roll1000 = df['low'].rolling(window=1000, min_periods=1, center=False).min()

    df['rv5'] = rv5
    df['rv10'] = rv10
    df['rv15'] = rv15
    df['rv20'] = rv20
    df['rv30'] = rv30
    df['rv60'] = rv60
    df['rv90'] = rv90
    df['rv120'] = rv120
    df['rv180'] = rv180
    vol_10 = df['tick_volume'] > rv10.shift()
    vol_15 = df['tick_volume'] > rv15.shift()
    vol_20 = df['tick_volume'] > rv20.shift()
    vol_30 = df['tick_volume'] > rv30.shift()
    vol_60 = df['tick_volume'] > rv60.shift()
    vol_90 = df['tick_volume'] > rv90.shift()
    vol_120 = df['tick_volume'] > rv120.shift()
    vol_180 = df['tick_volume'] > rv180.shift()
    df['vol_10'] = vol_10
    df['vol_15'] = vol_15
    df['vol_20'] = vol_20
    df['vol_30'] = vol_30
    df['vol_60'] = vol_60
    df['vol_90'] = vol_90
    df['vol_120'] = vol_120
    df['vol_180'] = vol_180
    # Rolling high bars
    h10 = df['high'] > rolh10.shift()
    h15 = df['high'] > rolh15.shift()
    h20 = df['high'] > rolh20.shift()
    h30 = df['high'] > rolh30.shift()
    h60 = df['high'] > rolh60.shift()
    h90 = df['high'] > rolh90.shift()
    h120 = df['high'] > rolh120.shift()
    h180 = df['high'] > rolh180.shift()
    h240 = df['high'] > rolh240.shift()
    h480 = df['high'] > rolh480.shift()
    h1000 = df['high'] > rolh1000.shift()

    df['h10'] = h10
    df['h15'] = h15
    df['h20'] = h20
    df['h30'] = h30
    df['h60'] = h60
    df['h90'] = h90
    df['h120'] = h120
    df['h180'] = h180
    df['h240'] = h240
    df['h480'] = h480
    df['h100'] = h1000
    # Rolling low bars
    l10 = df['low'] < roll10.shift()
    l15 = df['low'] < roll15.shift()
    l20 = df['low'] < roll20.shift()
    l30 = df['low'] < roll30.shift()
    l60 = df['low'] < roll60.shift()
    l90 = df['low'] < roll90.shift()
    l120 = df['low'] < roll120.shift()
    l180 = df['low'] < roll180.shift()
    l240 = df['low'] < roll240.shift()
    l480 = df['low'] < roll480.shift()
    l1000 = df['low'] < roll1000.shift()
    df['l10'] = l10
    df['l15'] = l15
    df['l20'] = l20
    df['l30'] = l30
    df['l60'] = l60
    df['l90'] = l90
    df['l120'] = l120
    df['l180'] = l180
    df['l240'] = l240
    df['l480'] = l480
    df['l1000'] = l1000
    # df['impuls_1_sp'] = df['high'].shift() - df['low']
    impuls_up = (df['close'].shift(5) - df['close']) >= 0
    impuls_dn = (df['close'].shift(5) - df['close']) < 0

    # df['h_l'] = hl
    filter_up = df.loc[impuls_up]
    filter_dn = df.loc[impuls_dn]
    filter_up = (filter_up['high'] - filter_up['low']) * 10000
    # filter_up['hlc'] = filter_up['h_l'] - filter_up['h_l'].shift()
    filter_dn = (filter_dn['high'] - filter_dn['low']) * 10000
    uhl5 = filter_up.ewm(span=5, ignore_na=True, adjust=False).mean()
    uhl10 = filter_up.ewm(span=10, ignore_na=True, adjust=False).mean()
    uhl15 = filter_up.ewm(span=15, ignore_na=True, adjust=False).mean()
    dhl5 = filter_dn.ewm(span=5, ignore_na=True, adjust=False).mean()
    dhl10 = filter_dn.ewm(span=10, ignore_na=True, adjust=False).mean()
    dhl15 = filter_dn.ewm(span=15, ignore_na=True, adjust=False).mean()

    # df['impuls_up'] = impuls_up
    # df['impuls_dn'] = impuls_dn
    # df['impuls_up_5'] = filter_up.rolling(window=5, min_periods=1, center=False).mean()
    df['uhl5'] = uhl5
    df['uhl5'].fillna(method="bfill", inplace=True)
    df['uhl10'] = uhl10
    df['uhl10'].fillna(method="bfill", inplace=True)
    df['uhl15'] = uhl15
    df['uhl15'].fillna(method="bfill", inplace=True)
    df['dhl5'] = dhl5
    df['dhl5'].fillna(method="bfill", inplace=True)
    df['dhl10'] = dhl10
    df['uhl10'].fillna(method="bfill", inplace=True)
    df['dhl15'] = dhl15
    df['dhl15'].fillna(method="bfill", inplace=True)
    df['imp5'] = uhl5 - dhl5
    # df[['uhl5','uhl10','uhl15','dhl5','dhl10','dhl15']].fillna(method="ffill", inplace=True)
    df['imp5'].fillna(method="bfill", inplace=True)
    df['imp5'] = df['uhl5'] - df['dhl5']

    df['imp10'] = df['uhl10'] - df['dhl10']
    df['imp10'].fillna(method="bfill", inplace=True)
    df['imp15'] = df['uhl15'] - df['dhl15']
    df['imp15'].fillna(method="bfill", inplace=True)
    imp10_5 = df['imp10'].ewm(span=5, ignore_na=True, adjust=False).mean()
    imp10_5_a = df['imp10'] / imp10_5 * 100
    df['imp10_5_a'] = imp10_5_a
    df['ultra_vol'] = df['tick_volume'].rolling(window=90, min_periods=10, center=False).max()
    df['ultra_vol'] = df['tick_volume'] > df['ultra_vol'].shift()
    vol = df['ultra_vol'] == True
    upper_wick = abs(df['high'] - df['close'])
    lower_wick = abs(df['open'] - df['low'])
    body = abs(df['open'] - df['close'])
    spread = abs(df['high'] - df['close'])
    sc_upper_whole_ratio = upper_wick / body < 0.12
    sc_lower_sprd = lower_wick > 0.1 * body
    sc_warunki = (sc_upper_whole_ratio == True) & (sc_lower_sprd == True) & (df['l60'] == True) & (df['vol_60'] == True)
    sc_60 = (sc_upper_whole_ratio == True) & (sc_lower_sprd == True) & (df['l60'] == True) & (df['vol_60'] == True)
    sc_90 = (sc_upper_whole_ratio == True) & (sc_lower_sprd == True) & (df['l90'] == True) & (df['vol_90'] == True)
    sc_120 = (sc_upper_whole_ratio == True) & (sc_lower_sprd == True) & (df['l120'] == True) & (df['vol_120'] == True)
    sc_180 = (sc_upper_whole_ratio == True) & (sc_lower_sprd == True) & (df['l180'] == True) & (df['vol_180'] == True)
    # sc_240 = (sc_upper_whole_ratio == True) & (sc_lower_sprd == True) & (df['l240'] == True) & (df['vol_240'] == True)
    # Buying Climax #1
    bc_upper_whole_ratio = upper_wick / body > 0.12
    bc_lower_sprd = lower_wick < 0.1 * spread
    bc_warunki = (vol == True) & (bc_upper_whole_ratio == True) & (bc_lower_sprd == True) & (df['h60'] == True)
    bc_60 = (bc_upper_whole_ratio == True) & (bc_lower_sprd == True) & (df['h60'] == True) & (df['vol_60'] == True)
    bc_90 = (bc_upper_whole_ratio == True) & (bc_lower_sprd == True) & (df['h90'] == True) & (df['vol_90'] == True)
    bc_120 = (bc_upper_whole_ratio == True) & (bc_lower_sprd == True) & (df['h120'] == True) & (df['vol_120'] == True)
    bc_180 = (bc_upper_whole_ratio == True) & (bc_lower_sprd == True) & (df['h180'] == True) & (df['vol_180'] == True)

    return df


def filt_candles(symbol):
    df = get_candles(symbol)
    warunek_vol = df['tick_volume'] > df['ewm_vol_20'] * 1.7
    warunki_wfo_spd = (df['high_is_higher'] == True) & (df['vol_is_lower'] == True) & warunek_vol
    warunki_wfo_wzr = (df['lower_low'] == True) & (df['vol_is_lower'] == True) & warunek_vol
    spr_to_vol = df['low_sprd'] == True
    wfo = (warunki_wfo_spd | warunki_wfo_wzr)
    kontynuacja = (df['vol_roll'] & df['vol_roll'])
    kontynuacja_filt = df.loc[
        kontynuacja, ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'vol_trend20', 'vol_trend7',
                      'vol_trend4']]
    filtr_spr_vol_anomaly = df.loc[
        spr_to_vol, ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'high_is_higher', 'rowl_high_max',
                     'vol_trend20', 'vol_trend7', 'vol_trend4']]
    filtr_wfo = df.loc[
        wfo, ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'ewm_vol_20', 'vol_trend20',
              'vol_trend7', 'vol_trend4', 'vol_roll', 'wfo_na_spadki', 'wfo_na_wzrosty']]
    return kontynuacja_filt


def high_vol(symbol):
    df = get_candles(symbol)
    # df['zmiana_kier']
    # warunek_vol = (df['max_vol_50'].shift() == True) & (df['zmiana_kier_down'] == True | df['zmiana_kier_up'] == True)
    warunek_vol = (df['high_vol'] == True) & (df['vol_trend4'] < 0)
    warunki_wfo_spd = (df['vol_h_25'] == True) & (df['vol_is_lower'] == True) & warunek_vol
    warunki_wfo_wzr = (df['lower_low'] == True) & (df['vol_is_lower'] == True) & warunek_vol
    spr_to_vol = df['low_sprd'] == True
    wfo = (warunki_wfo_spd | warunki_wfo_wzr)
    kontynuacja = (df['vol_roll'] & df['vol_roll'])
    kontynuacja_filt = df.loc[
        kontynuacja, ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'vol_trend20', 'vol_trend7',
                      'vol_trend4']]
    filtr_spr_vol_anomaly = df.loc[
        spr_to_vol, ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'high_is_higher', 'rowl_high_max',
                     'vol_trend20', 'vol_trend7', 'vol_trend4']]
    filtr_wfo = df.loc[
        wfo, ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'ewm_vol_20', 'vol_trend20',
              'vol_trend7', 'vol_trend4', 'vol_roll', 'wfo_na_spadki', 'wfo_na_wzrosty']]
    hig_vol = df.loc[
        warunek_vol, ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'vol_trend20', 'vol_trend7',
                      'vol_trend4']]
    return hig_vol


def high_vol_list():
    high_vol_df = pd.DataFrame()
    symbol_list_filtered = []
    for x in filter_forex_board['symbol_name']:
        symbol_list_filtered.append(x)
    for x in symbol_list_filtered:
        vol_output = high_vol(x)
        high_vol_df = pd.concat([high_vol_df, vol_output])
    return high_vol_df


def symbol_list(symbol):
    high_vol_df = pd.DataFrame()
    if symbol == 'all':
        symbol_list_filtered = []
        for x in filter_forex_board['symbol_name']:
            symbol_list_filtered.append(x)
        for x in symbol_list_filtered:
            vol_output = get_candles(x)
            high_vol_df = pd.concat([high_vol_df, vol_output])
    else:
        vol_output = get_candles(symbol)
        high_vol_df = pd.concat([high_vol_df, vol_output])
    return high_vol_df


# print(range(len(high_vol_list().index)))
def reactions():
    # pd.Series([str(symbol) for x in range(len(df.index))])
    df = get_candles("AUDUSD")
    poczatek = (df['vol_30'] == True)  # df['vol50_zm'] == True df.loc[(df['vol50_zm'] == True)] #df.loc[41:46,'open']]
    start_idx = list(poczatek.index)
    end_idx = df.loc[(df['consecutive'] == False)]
    end_idx = end_idx.index
    joined_list = []
    for x in end_idx:
        for y in start_idx:
            if x > y:
                joined_list.append(x)

    koniec = []
    d = []
    joined_list = [koniec.append(x) for x in joined_list if x not in koniec]
    # array = [np.array(range(x, y)) for x, y in zip_longest(start_idx, joined_list)]
    for previous, current in zip_longest(start_idx, joined_list[0:]):
        d.append((list(range(previous, current))))
    return koniec


def excel_writer(scenariusz1):
    symbols = scenariusz1['symbol']
    joined_list1 = list(dict.fromkeys(symbols))
    for x in joined_list1:
        filter = scenariusz1['symbol'] == x
        df2 = scenariusz1.loc[filter]
        with pd.ExcelWriter('output.xlsx', mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            df2.to_excel(writer, sheet_name=x)


def wzrosty_with_test(symbol):
    wzrosty_with_test = pd.DataFrame()
    df = symbol_list(symbol)
    # warunek_vol = (df['high_vol']==True) & (df['vol_trend4']<0)#df['vol50_zm'] == True
    # warunki_wfo_spd = (df['l30']==True) & (df['vol_h_25'] == True) & (df['vol_is_lower'] == True)
    warunki = ((df['h60'] == True) & (df['vol_60'] == True) & (df['na_wzrosty'] == True) & (df['up_trend_30'] == True))
    df1 = df.loc[warunki]

    wzrosty_with_test = pd.concat([df, df1], ignore_index=True)

    wzrosty_with_test.set_index(['time'])
    wzrosty_with_test.sort_values(by=['time'], ascending=False, inplace=True)
    # wzrosty_with_test.sort_index(inplace=True)
    war1 = (wzrosty_with_test['na_wzrosty'].shift() == True)
    war2 = (wzrosty_with_test['up_test'] == True)  # & (df['up_trend_30'] == True)
    filt_nawzr = wzrosty_with_test.loc[(war2 & war1)]
    # SCENARIUSZ 1
    # WARUNEK 1 high 120 oraz dn_trend
    warunek1 = (df['l120'] == True) & (df['up_trend_30'] == True)
    warunek1 = df.loc[warunek1]
    warunek2 = (df['up_test'] == True) & (df['up_trend_30'] == True)
    warunek2 = df.loc[warunek2]
    scenariusz1 = pd.DataFrame()
    scenariusz1 = pd.concat([warunek1, warunek2], ignore_index=True)
    scenariusz1.set_index(['time'])
    scenariusz1.sort_values(by=['time'], ascending=False, inplace=True)
    # excel_writer(scenariusz1)
    # ['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'vol_trend20', 'vol_trend7','vol_trend4']]
    # ['time','tick_volume','symbol','up_trend_30','dn_trend_30','up_trend_15','dn_trend_15','up_trend_4','dn_trend_4','up_trend_7','dn_trend_7','up_dn_15','na_wzrosty','na_spadki']]
    scenariusz1.to_excel(date_time + "_" + "wzrosty_scen1" + " " + symbol + " " + ".xlsx")
    # df.to_excel(date_time +"df" + "15_05" + ".xlsx")
    return filt_nawzr


def spadki_with_test(symbol):
    spadki_with_test = pd.DataFrame()
    df = symbol_list(symbol)

    # df = df.loc[(df['down_test'] == True)]
    warunki = ((df['h30'] == True) & (df['vol_30'] == True) & (df['na_spadki'] == True) & (df['dn_trend_30'] == True))
    ultra_vol = (df['ultra_vol'] == True) & (df['h120'] == True)
    df1 = (df.loc[warunki])
    # df2 = (df.loc['down_test'] == True)
    spadki_with_test = pd.concat([df, df1], ignore_index=True)
    # wzrosty_with_test = pd.DataFrame(index=range(len(wzrosty_with_test)))
    # wzrosty_with_test.reset_index()
    spadki_with_test.set_index(['time'])
    spadki_with_test.sort_values(by=['time'], ascending=False, inplace=True)
    war1 = (spadki_with_test['na_spadki'].shift() == True)
    war2 = (spadki_with_test['down_test'] == True)  # & (wzrosty_with_test['dn_trend_30'] == True)
    spadki_with_test_filter = spadki_with_test.loc[(war1 & war2)]
    # SCENARIUSZ 1
    # WARUNEK 1 high 120 oraz dn_trend
    warunek_impl = (df['imp5'] < 0) & (df['imp10'] < 0) & (df['imp15'] < 0) & (df['imp10_5_a'] > 70) & (
            df['ultra_vol'] == True) & (df['h30'] == True)
    warunek_impl_2 = (df['imp5'] < 0) & (df['imp10'] < 0) & (df['imp15'] < 0) & (df['imp10_5_a'] > 70)
    warunek_vol_h60 = (df['ultra_vol'] == True) & (df['h60'] == True)
    warunek_trend = warunek_impl  # (df['h120']==True)
    warunek1 = (df['dn_trend_30'] == True) & warunek_trend
    warunek1 = df.loc[warunek1]
    # df['warunek1'] = warunek1
    warunek2 = (df['down_test'] == True) & (df['dn_trend_30'] == True) & warunek_impl_2
    warunek2 = df.loc[warunek2]
    warunek_1 = (df['h120'] == True) & (df['dn_trend_30'] == True)
    warunek_1 = df.loc[warunek_1]
    warunek_2 = (df['down_test'] == True) & (df['dn_trend_30'] == True)
    warunek_2 = df.loc[warunek_2]
    scenariusz1 = pd.DataFrame()
    scenariusz1 = pd.concat([warunek_1, warunek_2], ignore_index=True)

    # scenariusz1 = scenariusz1.loc[]
    scenariusz1.set_index(['time'])
    scenariusz1.sort_values(by=['time'], ascending=False, inplace=True)
    warunek3 = (scenariusz1['down_test'] == True)
    scenariusz1 = scenariusz1.loc[warunek3]
    scenariusz2 = df.loc[ultra_vol]
    scenariusz2.set_index(['time'])
    scenariusz2.sort_values(by=['time'], ascending=False, inplace=True)
    scenariusz1.to_excel(date_time + "_" + "spadki_scen1" + " " + symbol + " " + ".xlsx")
    # symbols = scenariusz1['symbol']
    '''joined_list1 = list(dict.fromkeys(symbols))
    for x in joined_list1:
        filter = scenariusz1['symbol'] == x
        df2 = scenariusz1.loc[filter]
        with pd.ExcelWriter('output_spd.xlsx',mode='a',engine='openpyxl',if_sheet_exists='overlay') as writer:
            df2.to_excel(writer, sheet_name=x)'''

    # scenariusz1.reset_index()
    # scenariusz1_start_idx = scenariusz1['down_test'].index
    # liczymy dla 5,15,30,60 swiec max,min dla ohcl , suma wolumenow
    # wol na rollingu, reszta z funkcji
    # anomalia - ponad przecietny wzrost spreadu, spadek wolumenu oraz odwrotnie oznaki sily i slabosci
    # upbar - spread maleje ,wolumen przyrasta = opor, oczekiwane odwrocenie
    # ['time','tick_volume','symbol','up_trend_30','dn_trend_30','up_trend_15','dn_trend_15','up_trend_4','dn_trend_4','up_trend_7','dn_trend_7','na_wzrosty','na_spadki']['symbol', 'time', 'open', 'high', 'low', 'close', 'tick_volume', 'vol_trend20', 'vol_trend7''vol_trend4']]
    # df.to_excel(date_time +"df"+ "15_05" + ".xlsx")
    # os.system('TASKKILL /F /IM terminal64.exe')
    add_volumes_to_zig_zag_dictionary(df)
    return scenariusz1


path = r'C:/forex'
keyword = 'all'


class pd_xls:
    def __init__(self, path):
        self.path = path
        # self.keyword = keyword

    # self.wykres = wykres
    # self.df = df
    def read_wzrosty(self):
        lst_of_files = glob.glob(self.path + '/*.xlsx')

        df = pd.read_excel(lst_of_files[-1])
        return df

    def read_spadki(self):
        lst_of_files = glob.glob(self.path + '/*.xlsx')

        df = pd.read_excel(lst_of_files[-2])
        return df


def buying_climax(symbol):
    df = symbol_list(symbol)
    bc = (df['bc_60'] == True) | (df['bc_90'] == True) | (df['bc_120'] == True) | (df['bc_180'] == True)
    bc = df.loc[bc]
    df.set_index(['time'])
    df.sort_values(by=['time'], ascending=False, inplace=True)
    testy = (df['down_test'] == True) & (df['dn_trend_30'] == True)
    test = df.loc[testy]
    testing = pd.concat([df, test], ignore_index=True)
    testing.set_index(['time'])
    testing.sort_values(by=['time'], ascending=False, inplace=True)
    testing = testing.loc[(testing['down_test'] == True) & (testing['dn_trend_30'] == True)]

    return bc


def selling_climax(symbol):
    sc = symbol_list(symbol)
    sc1 = (df['sc_60'] == True) | (df['sc_90'] == True) | (df['sc_120'] == True) | (df['sc_180'] == True)
    df = sc.loc[sc1]
    sc.set_index(['time'])
    sc.sort_values(by=['time'], ascending=False, inplace=True)
    return df


##################### ZIG ZAG SWINGS POINTS AND VOLUMES ################################

zig_zag_result = None


def read_log_file_and_calculate_zig_zag_points_to_dictionary(df):
    result_dict = {}
    zig_zag_df = pd.read_csv(logFilePath, delim_whitespace=True, encoding='utf-16',
                             names=['TRASH1', 'symbol', 'SWING', 'VALUE', 'DAY', 'TIME'],
                             header=None).reset_index().sort_index()
    zig_zag_df.drop(['TRASH1', 'level_0', 'level_1', 'level_2'], axis='columns', inplace=True)
    zig_zag_df['symbol'] = zig_zag_df['symbol'].str.replace('(', '').str.replace(')', '').str.replace(',M1', '')
    zig_zag_df['time'] = zig_zag_df['DAY'] + ' ' + zig_zag_df['TIME']
    zig_zag_df['time'] = pd.to_datetime(zig_zag_df['time'])
    zig_zag_df.drop(['TIME', 'DAY'], axis='columns', inplace=True)
    uniqueNames = zig_zag_df['symbol'].unique()
    result_dict = {elem: pd.DataFrame() for elem in uniqueNames}
    for key in result_dict.keys():
        df_by_key = zig_zag_df[:][zig_zag_df['symbol'] == key]
        df_by_key.drop_duplicates(inplace=True)
        df_by_key = df_by_key.sort_values(by=['time'])
        df_high = df_by_key.loc[(df_by_key['SWING'] == 'H')]
        df_by_key['up_swing_diff'] = df_high['VALUE'] - df_high['VALUE'].shift()
        df_by_key = add_zig_zag_volumes(df, df_by_key, df_high)
        df_low = df_by_key.loc[(df_by_key['SWING'] == 'L')]
        df_by_key['down_swing_diff'] = df_low['VALUE'] - df_low['VALUE'].shift()
        df_by_key = add_zig_zag_volumes(df, df_by_key, df_low)
        df_by_key['volume_diff'] = df_by_key['volume'] - df_by_key['volume'].shift(2)
        result_dict[key] = df_by_key
    return result_dict


def add_zig_zag_volumes(df, df_by_key, df_pick_or_valley):
    firstRun = True
    previousRow = None
    for index, row in df_pick_or_valley.iterrows():
        if firstRun:
            previousRow = row
            firstRun = False
            df_by_key.loc[(df_by_key['symbol'] == row['symbol']) & (
                    df_by_key['time'] == row['time']), 'volume'] = 0
            df_by_key.loc[
                (df_by_key['symbol'] == row['symbol']) & (df_by_key['time'] == row['time']), 'candles'] = 0
            continue
        dfRange = df[(df['symbol'] == row['symbol']) & (df['time'] <= row['time']) & (
                df['time'] >= previousRow['time'])]
        volumeForRange = dfRange['tick_volume'].sum()
        candleCount = len(dfRange.index)
        df_by_key.loc[(df_by_key['symbol'] == row['symbol']) & (
                df_by_key['time'] == row['time']), 'volume'] = volumeForRange
        df_by_key.loc[
            (df_by_key['symbol'] == row['symbol']) & (df_by_key['time'] == row['time']), 'candles'] = candleCount
        previousRow = row
    return df_by_key


def add_volumes_to_zig_zag_dictionary(df):
    result_dictionary = read_log_file_and_calculate_zig_zag_points_to_dictionary(df)
    previous_swing_in_df = None
    for symbolKey in result_dictionary:
        for timeKey in result_dictionary[symbolKey]:
            current_swing_in_df = df.loc[(df['symbol'] == symbolKey) & (df['time'] == timeKey)]
            if current_swing_in_df is None or current_swing_in_df.empty:
                continue
            if previous_swing_in_df is None or previous_swing_in_df.empty:
                current_swing_in_df['swing_candle_count'] = 0
                current_swing_in_df['up_swing_vol'] = 0
                current_swing_in_df['up_swing_vol_diff'] = 0
                current_swing_in_df['down_swing_vol'] = 0
                current_swing_in_df['down_swing_vol_diff'] = 0
                current_swing_in_df['swing_candle_count'] = 0
                previous_swing_in_df = current_swing_in_df
                continue
            dfRange = df[(df['symbol'] == symbolKey) & (df['time'] <= timeKey) & (
                        df['time'] >= previous_swing_in_df['time'].values[0])]
            volumeForRange = dfRange['tick_volume'].sum()
            candleCount = len(dfRange.index)
            result_dictionary[symbolKey][timeKey]['candleCount'] = candleCount
            if result_dictionary[symbolKey][timeKey]['swing'] == 'upswing':
                result_dictionary[symbolKey][timeKey]['up_swing_vol'] = volumeForRange
                result_dictionary[symbolKey][timeKey]['down_swing_vol'] = 0
                current_swing_in_df['up_swing_vol'] = volumeForRange
                current_swing_in_df['down_swing_vol'] = 0
                if previous_swing_in_df is None or previous_swing_in_df.empty:
                    previous_swing_in_df = current_swing_in_df
                    continue
                result_dictionary[symbolKey][timeKey]['up_swing_vol_diff'] = abs(
                    volumeForRange - previous_swing_in_df['up_swing_vol'].values[0])
                result_dictionary[symbolKey][timeKey]['down_swing_vol_diff'] = 0
            else:
                result_dictionary[symbolKey][timeKey]['down_swing_vol'] = volumeForRange
                result_dictionary[symbolKey][timeKey]['up_swing_vol'] = 0
                current_swing_in_df['down_swing_vol'] = volumeForRange
                current_swing_in_df['up_swing_vol'] = 0
                if previous_swing_in_df is None or previous_swing_in_df.empty:
                    previous_swing_in_df = current_swing_in_df
                    continue
                result_dictionary[symbolKey][timeKey]['down_swing_vol_diff'] = abs(
                    volumeForRange - previous_swing_in_df['down_swing_vol'].values[0])
                result_dictionary[symbolKey][timeKey]['up_swing_vol_diff'] = 0
            previous_swing_in_df = current_swing_in_df
    zig_zag_result = result_dictionary
    zigzag_df = pd.concat({k: pd.DataFrame(v).T for k, v in zig_zag_result.items()}, axis=0).reset_index().sort_index()
    # zig_zag_df = pd.concat({k: pd.DataFrame.from_dict(v, 'index') for k, v in zig_zag_result.items()},axis=0)
    # zig_zag_df = pd.DataFrame.from_dict(zig_zag_result, orient='columns')
    print("Zig zag finished, ")


def zig_zag_to_df():
    zig_dict = add_volumes_to_zig_zag_dictionary(symbol_list('all'))
    for x in zig_dict:
        pd.DataFrame.from_dict(zig_zag_result)


# wzrosty = pd_xls(path).read_wzrosty().head(20)
# spadki = pd_xls(path).read_spadki().head(20)
# print(buying_climax('all'))
# print(selling_climax('all'))
print(spadki_with_test('all').head(5))
# print(wzrosty_with_test('all').head(5))
# print(filter_forex_board)
# p = 0.0000002  # 20%
'''
    masked_v = df_valleys['zigzag_y_valleys']
    masked_p = df_peaks['zigzag_y_peaks']
    m = np.abs(masked_v - masked_v.shift()) / masked_v.shift()
    n = np.abs(masked_p - masked_p.shift()) / masked_p.shift()
    df_valleys.where(m>p,inplace=True)
    df_valleys.dropna()
    df_peaks.where(n > p, inplace=True)
    df_peaks.dropna()
    #filter_mask = filter(df_valleys.zigzag_y_valleys, p)
    #df_valleys = df_valleys[filter_mask]
    #filter_mask = filter(df_peaks.zigzag_y_peaks, p)
    #df_peaks = df_peaks[filter_mask]
'''
