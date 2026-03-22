"""
MIDAS ANALYSIS V2 - PRODUCTION READY
=====================================

Improvements over V1:
1. ✅ Data leakage FIXED (prepare_ml_features excludes last swing)
2. ✅ Comprehensive forex features integrated (VSA/Wyckoff)
3. ✅ Spread analysis & effort-result divergences
4. ✅ Multi-tier feature selection system
5. ✅ Enhanced validation & testing utilities

Author: Midas Trading System
Version: 2.0
Date: 2026-01-11
"""

import numpy as np
import pandas as pd
from scipy.spatial import distance
import scipy.stats as stats
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Silence TF
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.offline as pyo
import datetime
from tqdm import tqdm


class ForexFeatures:
    """
    Comprehensive VSA/Wyckoff feature engineering
    Extracted from forex.py and enhanced
    """
    
    @staticmethod
    def calculate_all(df):
        """
        Master function - calculates ALL forex features
        
        Categories:
        1. Volume Trends (buying/selling pressure)
        2. Structural Levels (support/resistance)
        3. Volume Extremes (spikes, anomalies)
        4. Impulse/Momentum
        5. Spread Analysis
        6. Effort-Result Divergences
        7. Wyckoff Patterns
        8. Climax Detection
        9. Composite Indicators
        """
        df = df.copy()
        
        # 1. Volume Trends
        df = ForexFeatures._volume_trends(df)
        
        # 2. Structural Levels
        df = ForexFeatures._structural_levels(df)
        
        # 3. Volume Extremes
        df = ForexFeatures._volume_extremes(df)
        
        # 4. Impulse
        df = ForexFeatures._impulse(df)
        
        # 5. Spread Analysis
        df = ForexFeatures._spread_analysis(df)
        
        # 6. Effort-Result Divergences
        df = ForexFeatures._effort_result_divergences(df)
        
        # 7. Wyckoff Patterns
        df = ForexFeatures._wyckoff_patterns(df)
        
        # 8. Climax Detection
        df = ForexFeatures._climax_detection(df)
        
        # 9. Composite Indicators
        df = ForexFeatures._composite_indicators(df)
        

        return df
    
    @staticmethod
    def _volume_trends(df):
        """Volume trends - buying vs selling pressure"""
        
        upv = df['tick_volume'].where(df['close'] >= df['open'], 0)
        dnv = df['tick_volume'].where(df['close'] < df['open'], 0)
        
        for span in [4, 7, 15, 30]:
            upvm = upv.ewm(span=span, adjust=False).mean().ffill()
            dnvm = dnv.ewm(span=span, adjust=False).mean().ffill()
            
            df[f'upvm{span}'] = upvm
            df[f'dnvm{span}'] = dnvm
            df[f'vol_trend{span}'] = upvm - dnvm
            df[f'vol_trend{span}_norm'] = df[f'vol_trend{span}'] / (df['tick_volume'] + 1e-6)
        
        df['vol_trend_accel'] = df['vol_trend7'] - df['vol_trend30']
        
        return df
    
    @staticmethod
    def _structural_levels(df):
        """Rolling extremes for support/resistance - Matching forex (1).py logic"""
        
        # Original forex.py windows: 5, 10, 15, 20, 30, 60, 90, 120, 180, 240, 480, 1000
        windows = [5, 10, 15, 20, 30, 60, 90, 120, 180, 240, 480, 1000]
        
        for w in windows:
            # Rolling Highs
            df[f'rh{w}'] = df['high'].rolling(window=w).max().shift()
            df[f'h{w}'] = df['high'] > df[f'rh{w}']
            
            # Rolling Lows
            df[f'rl{w}'] = df['low'].rolling(window=w).min().shift()
            df[f'l{w}'] = df['low'] < df[f'rl{w}']
            
            # Rolling Volumes
            df[f'rv{w}'] = df['tick_volume'].rolling(window=w).max().shift()
            df[f'vol_{w}'] = df['tick_volume'] > df[f'rv{w}']
            
            # Distances (Keep for ML)
            df[f'dist_from_high_{w}'] = (df[f'rh{w}'] - df['close']) / (df[f'rh{w}'] - df[f'rl{w}'] + 1e-6)
            df[f'dist_from_low_{w}'] = (df['close'] - df[f'rl{w}']) / (df[f'rh{w}'] - df[f'rl{w}'] + 1e-6)
        
        return df
    
    @staticmethod
    def _volume_extremes(df):
        """Volume spikes and anomalies - Matching forex (1).py logic"""
        
        # High Volume Anomaly: Volume > 1.9 * EMA20
        df['ewm_vol_20'] = df['tick_volume'].ewm(span=60, adjust=False).mean() # Original uses 60 span for 'ewm_vol_20' in some places
        df['high_vol_anomaly'] = df['tick_volume'] > (1.9 * df['ewm_vol_20'])
        
        # Ultra Volume (from scenario logic)
        df['ultra_vol'] = df['tick_volume'] > df['tick_volume'].rolling(window=90).max().shift()
        
        for w in [20, 60, 180]:
            df[f'vol_ratio_{w}'] = df['tick_volume'] / (df[f'rv{w}'] + 1e-6)
            df[f'vol_percentile_{w}'] = df['tick_volume'].rolling(w).rank(pct=True).shift()
        
        for w in [20, 60]:
            vol_mean = df['tick_volume'].rolling(w).mean().shift()
            vol_std = df['tick_volume'].rolling(w).std().shift()
            df[f'vol_zscore_{w}'] = (df['tick_volume'] - vol_mean) / (vol_std + 1e-6)
        
        return df
    
    @staticmethod
    def _impulse(df):
        """Momentum and impulse indicators"""
        
        hl_range = (df['high'] - df['low']) * 10000
        uhl = hl_range.where(df['close'] > df['close'].shift(5), 0)
        dhl = hl_range.where(df['close'] < df['close'].shift(5), 0)
        
        for span in [5, 10, 15]:
            uhl_ema = uhl.ewm(span=span, adjust=False).mean().bfill()
            dhl_ema = dhl.ewm(span=span, adjust=False).mean().bfill()
            
            df[f'imp{span}'] = uhl_ema - dhl_ema
            df[f'imp{span}_norm'] = df[f'imp{span}'] / (abs(df[f'imp{span}']).rolling(20).mean().shift() + 1e-6)
        
        df['imp_divergence_5_15'] = df['imp5'] - df['imp15']
        df['imp_divergence_5_10'] = df['imp5'] - df['imp10']
        df['imp_accel'] = df['imp5'].diff(3)
        
        return df
    
    @staticmethod
    def _spread_analysis(df):
        """Spread (high-low range) analysis"""
        
        df['spread'] = df['high'] - df['low']
        
        for w in [10, 20, 60]:
            df[f'spread_avg_{w}'] = df['spread'].rolling(w).mean().shift()
            df[f'spread_ratio_{w}'] = df['spread'] / (df[f'spread_avg_{w}'] + 1e-6)
            df[f'spread_percentile_{w}'] = df['spread'].rolling(w).rank(pct=True).shift()
        
        spread_mean_20 = df['spread'].rolling(20).mean().shift()
        spread_std_20 = df['spread'].rolling(20).std().shift()
        df['spread_zscore_20'] = (df['spread'] - spread_mean_20) / (spread_std_20 + 1e-6)
        
        df['spread_ema_5'] = df['spread'].ewm(span=5).mean()
        df['spread_ema_20'] = df['spread'].ewm(span=20).mean()
        df['spread_trend'] = df['spread_ema_5'] - df['spread_ema_20']
        
        df['close_position'] = (df['close'] - df['low']) / (df['spread'] + 1e-6)
        
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        
        df['body_ratio'] = df['body'] / (df['spread'] + 1e-6)
        df['upper_wick_ratio'] = df['upper_wick'] / (df['spread'] + 1e-6)
        df['lower_wick_ratio'] = df['lower_wick'] / (df['spread'] + 1e-6)
        
        return df
    
    @staticmethod
    def _effort_result_divergences(df):
        """VSA effort vs result analysis"""
        
        df['vsr'] = df['tick_volume'] / (df['spread'] + 1e-6)
        df['vsr_avg_20'] = df['vsr'].rolling(20).mean().shift()
        df['vsr_ratio'] = df['vsr'] / (df['vsr_avg_20'] + 1e-6)
        
        # Type 1: Absorption (high vol + narrow spread)
        df['absorption_signal'] = (
            (df['vol_ratio_60'] > 1.5) &
            (df['spread_ratio_20'] < 0.7)
        ).astype(int)
        
        # Type 2: No demand (low vol + wide spread)
        df['no_demand_signal'] = (
            (df['vol_ratio_60'] < 0.7) &
            (df['spread_ratio_20'] > 1.3)
        ).astype(int)
        
        # Type 3: Exhaustion (rising spread + falling volume)
        spread_rising = df['spread'] > df['spread'].shift(1)
        vol_falling = df['tick_volume'] < df['tick_volume'].shift(1)
        df['exhaustion_signal'] = (spread_rising & vol_falling).astype(int)
        
        df['exhaustion_streak'] = 0
        for i in range(1, len(df)):
            if df['exhaustion_signal'].iloc[i]:
                df.iloc[i, df.columns.get_loc('exhaustion_streak')] = df['exhaustion_streak'].iloc[i-1] + 1
            else:
                df.iloc[i, df.columns.get_loc('exhaustion_streak')] = 0
        
        # Type 4: Compression (falling spread + rising volume)
        spread_falling = df['spread'] < df['spread'].shift(1)
        vol_rising = df['tick_volume'] > df['tick_volume'].shift(1)
        df['compression_signal'] = (spread_falling & vol_rising).astype(int)
        
        df['vsa_effort_score'] = (
            df['vol_ratio_60'] * 0.4 +
            df['vsr_ratio'] * 0.3 +
            df['spread_zscore_20'].abs() * 0.3
        ).clip(0, 10)
        
        return df
    
    @staticmethod
    def _wyckoff_patterns(df):
        """Wyckoff test patterns"""
        
        up_test = (
            (df['tick_volume'] > df['tick_volume'].shift(1)) &
            (df['close'] > df['open']) &
            (df['tick_volume'].shift(1) < df['tick_volume'].shift(2)) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'].shift(2) < df['open'].shift(2))
        )
        
        down_test = (
            (df['tick_volume'] > df['tick_volume'].shift(1)) &
            (df['close'] < df['open']) &
            (df['tick_volume'].shift(1) < df['tick_volume'].shift(2)) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'].shift(2) > df['open'].shift(2))
        )
        
        df['up_test'] = up_test & (df['vol_trend30'] > 0)
        df['down_test'] = down_test & (df['vol_trend30'] < 0)
        
        # Spring and Upthrust (False Breakouts)
        # Spring: Price dips below support (rl20) then closes above it
        df['is_spring'] = (df['low'] < df['rl20']) & (df['close'] > df['rl20'])
        # Upthrust: Price pokes above resistance (rh20) then closes below it
        df['is_upthrust'] = (df['high'] > df['rh20']) & (df['close'] < df['rh20'])
        
        # Quality Filter: Spring/Upthrust are better on high volume or after exhaustion
        df['spring_quality'] = ((df['is_spring']) & ((df['vol_ratio_20'] > 1.2) | (df['exhaustion_signal'] == 1))).astype(int)
        df['upthrust_quality'] = ((df['is_upthrust']) & ((df['vol_ratio_20'] > 1.2) | (df['exhaustion_signal'] == 1))).astype(int)
        
        df['bars_since_up_test'] = 0
        df['bars_since_down_test'] = 0
        
        counter_up = 0
        counter_dn = 0
        for i in range(len(df)):
            if df['up_test'].iloc[i]:
                counter_up = 0
            else:
                counter_up += 1
            
            if df['down_test'].iloc[i]:
                counter_dn = 0
            else:
                counter_dn += 1
            
            df.iloc[i, df.columns.get_loc('bars_since_up_test')] = min(counter_up, 100)
            df.iloc[i, df.columns.get_loc('bars_since_down_test')] = min(counter_dn, 100)
        
        df['up_test_count_20'] = df['up_test'].rolling(20).sum().shift()
        df['down_test_count_20'] = df['down_test'].rolling(20).sum().shift()
        
        return df
    
    @staticmethod
    def _climax_detection(df):
        """Buying/Selling climax detection"""
        
        for w in [60, 120, 180]:
            bc = (
                (df[f'vol_{w}']) &
                (df['spread_ratio_20'] > 1.5) &
                (df['close'] > df['close'].shift(5)) &
                (df['upper_wick_ratio'] > 0.3)
            )
            
            sc = (
                (df[f'vol_{w}']) &
                (df['spread_ratio_20'] > 1.5) &
                (df['close'] < df['close'].shift(5)) &
                (df['lower_wick_ratio'] > 0.3)
            )
            
            df[f'bc_{w}'] = bc
            df[f'sc_{w}'] = sc
        
        vol_component = df['vol_ratio_60'].clip(0, 3) / 3
        spread_component = df['spread_ratio_20'].clip(0, 3) / 3
        wick_component = (df['upper_wick_ratio'] + df['lower_wick_ratio']).clip(0, 1)
        
        df['climax_score'] = ((vol_component + spread_component + wick_component) / 3 * 100).clip(0, 100)
        df['climax_score'] = df['climax_score'].rolling(3).mean().shift()
        
        return df
    
    @staticmethod
    def _composite_indicators(df):
        """High-level composite indicators"""
        
        # Trend Strength
        trend_vol = (df['vol_trend30_norm'] + 1) / 2
        trend_imp = (df['imp15_norm'] + 2) / 4
        trend_struct = 1 - df['dist_from_high_180']
        
        df['trend_strength'] = ((trend_vol + trend_imp + trend_struct) / 3 * 100).clip(0, 100)
        
        # Reversal Probability
        rev_climax = df['climax_score'] / 100
        rev_exhaustion = (df['exhaustion_streak'] / 5).clip(0, 1)
        rev_absorption = df['absorption_signal']
        
        df['reversal_probability'] = ((rev_climax + rev_exhaustion + rev_absorption) / 3 * 100).clip(0, 100)
        
        # Volatility Regime
        df['volatility_regime'] = df['spread_zscore_20'].abs().clip(0, 3) / 3
        
        return df
    
    @staticmethod
    def get_feature_names_by_tier(tier='all'):
        """
        Returns feature names grouped by importance
        
        Args:
            tier: 'critical', 'important', 'useful', 'experimental', 'all'
        """
        features = {
            'critical': [
                'vol_trend7',
                'vol_trend30',
                'vol_trend30_norm',
                'vol_ratio_60',
                'dist_from_high_60',
                'dist_from_high_180',
                'spread_ratio_20',
                'close_position',
                'imp15',
                'climax_score',
            ],
            
            'important': [
                'vol_trend_accel',
                'vol_percentile_60',
                'break_strength_high_60',
                'break_strength_low_60',
                'spread_zscore_20',
                'vsr_ratio',
                'absorption_signal',
                'exhaustion_signal',
                'imp5',
                'imp_divergence_5_15',
                'body_ratio',
                'upper_wick_ratio',
                'lower_wick_ratio',
            ],
            
            'useful': [
                'bars_since_up_test',
                'bars_since_down_test',
                'vol_zscore_20',
                'vol_roc_10',
                'spread_trend',
                'no_demand_signal',
                'compression_signal',
                'trend_strength',
                'reversal_probability',
                'volatility_regime',
                'vsa_effort_score',
            ],
            
            'experimental': [
                'vol_up_streak',
                'vol_dn_streak',
                'up_test_count_20',
                'down_test_count_20',
                'exhaustion_streak',
                'imp_accel',
                'spread_percentile_20',
            ]
        }
        
        if tier == 'all':
            all_features = []
            for tier_features in features.values():
                all_features.extend(tier_features)
            return all_features
        else:
            return features.get(tier, [])


class Analyzer:
    """
    Main analysis class - enhanced with forex features
    """
    
    @staticmethod
    def calculate_zigzag(df, depth=12, deviation=5, backstep=3, point=0.00001):
        """
        ZigZag indicator calculation (unchanged from V1)
        """
        n = len(df)
        high = df['high'].values
        low = df['low'].values
        
        zigzag_buffer = np.zeros(n)
        high_buffer = np.zeros(n)
        low_buffer = np.zeros(n)
        
        # Step 1: Extremums
        for i in range(depth, n):
            window_low = low[i-depth+1 : i+1]
            minimum = np.min(window_low)
            if low[i] == minimum:
                low_buffer[i] = low[i]
                if i > backstep:
                    start_back = i - 1
                    end_back = i - backstep
                    if end_back < 0: end_back = 0
                    for b in range(start_back, end_back - 1, -1):
                        if low_buffer[b] != 0 and low_buffer[b] > low[i]:
                            low_buffer[b] = 0.0
            
            window_high = high[i-depth+1 : i+1]
            maximum = np.max(window_high)
            if high[i] == maximum:
                high_buffer[i] = high[i]
                if i > backstep:
                    start_back = i - 1
                    end_back = i - backstep
                    if end_back < 0: end_back = 0
                    for b in range(start_back, end_back - 1, -1):
                        if high_buffer[b] != 0 and high_buffer[b] < high[i]:
                            high_buffer[b] = 0.0
        
        # Step 2: ZigZag Logic
        whatlookfor = 0
        last_val = 0.0
        last_pos = 0
        
        for i in range(depth, n):
            if high_buffer[i] != 0:
                last_val = high_buffer[i]
                last_pos = i
                whatlookfor = -1
                zigzag_buffer[i] = last_val
                break
            if low_buffer[i] != 0:
                last_val = low_buffer[i]
                last_pos = i
                whatlookfor = 1
                zigzag_buffer[i] = last_val
                break
        
        start_i = last_pos + 1
        for i in range(start_i, n):
            if whatlookfor == 1:
                if high_buffer[i] != 0.0:
                    if (high_buffer[i] - last_val) >= (deviation * point):
                        zigzag_buffer[i] = high_buffer[i]
                        last_val = high_buffer[i]
                        last_pos = i
                        whatlookfor = -1
                    else:
                        high_buffer[i] = 0.0
                
                if low_buffer[i] != 0.0 and low_buffer[i] < last_val and whatlookfor == 1:
                    zigzag_buffer[last_pos] = 0.0
                    zigzag_buffer[i] = low_buffer[i]
                    last_val = low_buffer[i]
                    last_pos = i
            
            elif whatlookfor == -1:
                if low_buffer[i] != 0.0:
                    if (last_val - low_buffer[i]) >= (deviation * point):
                        zigzag_buffer[i] = low_buffer[i]
                        last_val = low_buffer[i]
                        last_pos = i
                        whatlookfor = 1
                    else:
                        low_buffer[i] = 0.0
                
                if high_buffer[i] != 0.0 and high_buffer[i] > last_val and whatlookfor == -1:
                    zigzag_buffer[last_pos] = 0.0
                    zigzag_buffer[i] = high_buffer[i]
                    last_val = high_buffer[i]
                    last_pos = i
        
        return zigzag_buffer
    
    @staticmethod
    def analyze_swings(df, zigzag_col='zigzag'):
        """
        Convert ZigZag points to swing metrics (unchanged from V1)
        """
        df['zigzag_val'] = df[zigzag_col].replace(0, np.nan)
        pivots = df[df['zigzag_val'].notna()].copy()
        pivots['prev_time'] = pivots['time'].shift(1)
        pivots['prev_val'] = pivots['zigzag_val'].shift(1)
        
        swings = []
        
        for idx, row in pivots.iterrows():
            if pd.isna(row['prev_val']): continue
            
            duration_mins = (row['time'] - row['prev_time']).total_seconds() / 60
            direction = 'Up' if row['zigzag_val'] > row['prev_val'] else 'Down'
            price_range = abs(row['zigzag_val'] - row['prev_val'])
            
            mask = (df['time'] >= row['prev_time']) & (df['time'] <= row['time'])
            total_volume = df.loc[mask, 'tick_volume'].sum()
            
            swings.append({
                'start_time': row['prev_time'],
                'end_time': row['time'],
                'direction': direction,
                'start_price': row['prev_val'],
                'end_price': row['zigzag_val'],
                'range': price_range,
                'volume': total_volume,
                'duration_mins': duration_mins,
                'velocity': price_range / (duration_mins + 1e-6),
                'intensity': total_volume / (duration_mins + 1e-6)
            })
        
        return pd.DataFrame(swings)
    
    @staticmethod
    def enrich_swings_with_forex_features(swings_df, df, feature_tier='critical'):
        """
        Adds forex bar-level features to swing-level data
        """
        
        # Get feature list
        feature_cols = ForexFeatures.get_feature_names_by_tier(feature_tier)
        
        # Verify features exist in df
        missing = [f for f in feature_cols if f not in df.columns]
        if missing:
            feature_cols = [f for f in feature_cols if f in df.columns]
        
        if not feature_cols:
            return swings_df
        
        enriched = []
        
        for idx, swing in swings_df.iterrows():
            # Find bars in this swing
            mask = (df['time'] >= swing['start_time']) & (df['time'] <= swing['end_time'])
            swing_bars = df[mask]
            
            swing_features = {}
            
            if swing_bars.empty:
                # Default values
                for col in feature_cols:
                    swing_features[f'forex_{col}_mean'] = 0
                    swing_features[f'forex_{col}_max'] = 0
            else:
                # Aggregate features based on type
                for col in feature_cols:
                    if col not in swing_bars.columns:
                        swing_features[f'forex_{col}_mean'] = 0
                        swing_features[f'forex_{col}_max'] = 0
                        continue
                    
                    # Volume/Impulse: mean + max
                    if any(x in col for x in ['vol_', 'imp', 'vsr']):
                        swing_features[f'forex_{col}_mean'] = swing_bars[col].mean()
                        swing_features[f'forex_{col}_max'] = swing_bars[col].max()
                    
                    # Distance/Position: end + avg
                    elif any(x in col for x in ['dist_', 'position', '_ratio']):
                        swing_features[f'forex_{col}_end'] = swing_bars[col].iloc[-1]
                        swing_features[f'forex_{col}_avg'] = swing_bars[col].mean()
                    
                    # Spread: max + avg
                    elif 'spread' in col:
                        swing_features[f'forex_{col}_max'] = swing_bars[col].max()
                        swing_features[f'forex_{col}_avg'] = swing_bars[col].mean()
                    
                    # Signals/Patterns: any + count
                    elif any(x in col for x in ['signal', 'test', 'climax', '_bc_', '_sc_']):
                        swing_features[f'forex_{col}_any'] = int(swing_bars[col].any())
                        swing_features[f'forex_{col}_count'] = int(swing_bars[col].sum())
                    
                    # Streaks: max
                    elif 'streak' in col:
                        swing_features[f'forex_{col}_max'] = swing_bars[col].max()
                    
                    # Scores: max + end
                    elif any(x in col for x in ['score', 'strength', 'probability']):
                        swing_features[f'forex_{col}_max'] = swing_bars[col].max()
                        swing_features[f'forex_{col}_end'] = swing_bars[col].iloc[-1]
                    
                    # Bars_since: min (closest)
                    elif 'bars_since' in col:
                        swing_features[f'forex_{col}_min'] = swing_bars[col].min()
                    
                    # Default: mean
                    else:
                        swing_features[f'forex_{col}_mean'] = swing_bars[col].mean()
            
            enriched.append({**swing.to_dict(), **swing_features})
        
        result_df = pd.DataFrame(enriched)
        
        forex_feature_count = len([c for c in result_df.columns if c.startswith('forex_')])
        
        return result_df
    
    @staticmethod
    def prepare_ml_features(swings_df, df=None, window=10, feature_tier='critical'):
        """
        ✅ FIXED VERSION - NO DATA LEAKAGE
        
        Prepares features for ML models with proper temporal separation
        
        Args:
            swings_df: Swing points DataFrame
            df: Optional OHLCV bars (for forex features)
            window: Lookback window
            feature_tier: 'critical'|'important'|'useful'|'experimental'|'all'
        
        Returns:
            X: Training features (excludes last swing)
            y: Training targets
            latest_X: Features for prediction (based on last `window` swings)
        """
        if len(swings_df) < window + 1:
            return None, None, None
        
        # Enrich swings with forex features if df provided
        if df is not None:
            swings_df = Analyzer.enrich_swings_with_forex_features(swings_df, df, feature_tier)
        
        features = []
        targets = []
        
        # ✅ CRITICAL FIX: Loop to len-1 (last swing EXCLUDED from training)
        for i in range(window, len(swings_df) - 1):
            subset = swings_df.iloc[i-window:i]
            target = swings_df.iloc[i]
            
            row = []
            
            # Swing-level features with LOG-Scaling for volume/intensity metrics
            for j in range(len(subset)):
                s = subset.iloc[j]
                
                row.extend([
                    s['range'],
                    s['duration_mins'],
                    np.log1p(s['volume']),
                    np.log1p(s['intensity']),
                    np.log1p(s['velocity']),
                ])
                
                if j > 0:
                    prev = subset.iloc[j-1]
                    row.extend([
                        s['range'] / (prev['range'] + 1e-6),
                        s['duration_mins'] / (prev['duration_mins'] + 1e-6),
                        np.log1p(s['intensity']) / (np.log1p(prev['intensity']) + 1e-6),
                    ])
                else:
                    row.extend([1.0, 1.0, 1.0])
                
                # Cumulative trend (not binary direction)
                trend = subset.iloc[:j+1].apply(
                    lambda x: 1 if x['direction'] == 'Up' else -1, axis=1
                ).sum()
                row.append(trend / (j + 1))
            
            # Forex features (aggregated from bars)
            if df is not None:
                forex_cols = [col for col in subset.columns if col.startswith('forex_')]
                
                if forex_cols:
                    for col in forex_cols:
                        row.append(subset[col].mean())
                        
                        if any(x in col for x in ['score', 'signal', 'ratio', 'climax']):
                            row.append(subset[col].max())
            
            features.append(row)
            
            # Targets (LOG-TRANSFORMED for stability)
            price_delta_pct = (target['end_price'] - subset.iloc[-1]['end_price']) / subset.iloc[-1]['end_price']
            targets.append([
                np.log1p(target['range']),
                np.log1p(target['duration_mins']),
                price_delta_pct
            ])
        
        # Latest features (for prediction)
        latest_subset = swings_df.iloc[-window:]
        latest_row = []
        
        for j in range(len(latest_subset)):
            s = latest_subset.iloc[j]
            
            latest_row.extend([
                s['range'],
                s['duration_mins'],
                np.log1p(s['volume']),
                np.log1p(s['intensity']),
                np.log1p(s['velocity']),
            ])
            
            if j > 0:
                prev = latest_subset.iloc[j-1]
                latest_row.extend([
                    s['range'] / (prev['range'] + 1e-6),
                    s['duration_mins'] / (prev['duration_mins'] + 1e-6),
                    np.log1p(s['intensity']) / (np.log1p(prev['intensity']) + 1e-6),
                ])
            else:
                latest_row.extend([1.0, 1.0, 1.0])
            
            trend = latest_subset.iloc[:j+1].apply(
                lambda x: 1 if x['direction'] == 'Up' else -1, axis=1
            ).sum()
            latest_row.append(trend / (j + 1))
        
        # Forex features for latest
        if df is not None:
            forex_cols = [col for col in latest_subset.columns if col.startswith('forex_')]
            
            if forex_cols:
                for col in forex_cols:
                    latest_row.append(latest_subset[col].mean())
                    
                    if any(x in col for x in ['score', 'signal', 'ratio', 'climax']):
                        latest_row.append(latest_subset[col].max())
        
        X = np.array(features)
        y = np.array(targets)
        latest_X = np.array(latest_row).reshape(1, -1)
        

        return X, y, latest_X
    
    @staticmethod
    def predict_next_swing_xgboost(swings_df, df=None, window=10, feature_tier='critical'):
        """
        XGBoost prediction with forex features support
        """
        X, y, latest_X = Analyzer.prepare_ml_features(swings_df, df, window, feature_tier)
        
        if X is None or len(X) < 20:
            return None
        
        # Train models with REGULARIZATION for Range/Duration
        model_range = xgb.XGBRegressor(
            n_estimators=50, max_depth=3, learning_rate=0.1,
            reg_alpha=0.1, reg_lambda=1.0  # Added regularization
        )
        model_range.fit(X, y[:, 0])
        pred_range_log = model_range.predict(latest_X)[0]
        pred_range = np.expm1(pred_range_log)  # Invert log transform
        
        model_dur = xgb.XGBRegressor(
            n_estimators=50, max_depth=3, learning_rate=0.1,
            reg_alpha=0.1, reg_lambda=1.0  # Added regularization
        )
        model_dur.fit(X, y[:, 1])
        pred_dur_log = model_dur.predict(latest_X)[0]
        pred_dur = np.expm1(pred_dur_log)  # Invert log transform
        
        model_price = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, subsample=0.8)
        model_price.fit(X, y[:, 2])
        pred_price_delta = model_price.predict(latest_X)[0]
        
        last_swing = swings_df.iloc[-1]
        next_dir = 'Down' if last_swing['direction'] == 'Up' else 'Up'
        
        pred_price = last_swing['end_price'] * (1 + pred_price_delta)
        target_time = pd.Timestamp(last_swing['end_time']) + pd.Timedelta(minutes=float(abs(pred_dur)))
        
        return {
            'direction': next_dir,
            'target_price': float(pred_price),
            'target_time': target_time,
            'predicted_range': float(abs(pred_range)),
            'predicted_duration': float(abs(pred_dur))
        }
    
    @staticmethod
    def predict_next_swing_lstm(swings_df, df=None, window=10, feature_tier='critical'):
        """
        LSTM prediction with forex features support
        """
        X, y, latest_X_raw = Analyzer.prepare_ml_features(swings_df, df, window, feature_tier)
        
        if X is None or len(X) < 40:
            return None
        
        # Scale data
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y)
        
        latest_X_scaled = scaler_X.transform(latest_X_raw)
        
        # Reshape for LSTM (samples, timesteps, features)
        features_per_timestep = X_scaled.shape[1] // window
        X_lstm = X_scaled.reshape(X_scaled.shape[0], window, features_per_timestep)
        latest_X = latest_X_scaled.reshape(1, window, features_per_timestep)
        
        # Build models
        model = Sequential([
            LSTM(64, input_shape=(window, features_per_timestep), return_sequences=True),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(2)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X_lstm, y_scaled[:, :2], epochs=30, batch_size=16, verbose=0)
        
        model_p = Sequential([
            LSTM(64, input_shape=(window, features_per_timestep), return_sequences=False),
            Dense(32, activation='relu'),
            Dense(1)
        ])
        model_p.compile(optimizer='adam', loss='mse')
        model_p.fit(X_lstm, y_scaled[:, 2], epochs=30, batch_size=16, verbose=0)
        
        # Predictions
        preds_scaled = model.predict(latest_X, verbose=0)
        preds_p_scaled = model_p.predict(latest_X, verbose=0)
        
        dummy_y = np.zeros((1, 3))
        dummy_y[0, :2] = preds_scaled[0]
        dummy_y[0, 2] = preds_p_scaled[0][0]
        
        final_preds = scaler_y.inverse_transform(dummy_y)[0]
        
        pred_range = np.expm1(float(final_preds[0]))
        pred_dur = np.expm1(float(final_preds[1]))
        pred_price_delta = float(final_preds[2])
        
        last_swing = swings_df.iloc[-1]
        next_dir = 'Down' if last_swing['direction'] == 'Up' else 'Up'
        
        pred_price = last_swing['end_price'] * (1 + pred_price_delta)
        target_time = pd.Timestamp(last_swing['end_time']) + pd.Timedelta(minutes=abs(float(pred_dur)))
        
        return {
            'direction': next_dir,
            'target_price': pred_price,
            'target_time': target_time,
            'predicted_range': abs(pred_range),
            'predicted_duration': abs(pred_dur)
        }
    
    @staticmethod
    def predict_next_swing_nn(swings_df, k=5):
        """
        Nearest Neighbors prediction (unchanged from V1)
        """
        if len(swings_df) < k + 2:
            return None
        
        df = swings_df.copy()
        epsilon = 1e-6
        df['velocity'] = df['range'] / (df['duration_mins'] + epsilon)
        df['vol_intensity'] = df['volume'] / (df['duration_mins'] + epsilon)
        
        features = ['range', 'duration_mins', 'velocity', 'vol_intensity']
        for col in features:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val - min_val == 0:
                df[f'{col}_norm'] = 0
            else:
                df[f'{col}_norm'] = (df[col] - min_val) / (max_val - min_val)
        
        norm_cols = [f'{c}_norm' for c in features]
        last_swing = df.iloc[-1]
        last_direction = last_swing['direction']
        
        history = df.iloc[:-1]
        same_dir_history = history[history['direction'] == last_direction].copy()
        
        if len(same_dir_history) < k:
            return None
        
        current_vec = last_swing[norm_cols].values.astype(float)
        hist_vecs = same_dir_history[norm_cols].values.astype(float)
        
        dists = []
        for i in range(len(hist_vecs)):
            d = distance.euclidean(current_vec, hist_vecs[i])
            dists.append(d)
        same_dir_history['distance'] = dists
        
        nearest = same_dir_history.sort_values('distance').head(k)
        
        next_indices = [df.index.get_loc(idx) + 1 for idx in nearest.index]
        valid_indices = [i for i in next_indices if i < len(df)]
        
        if not valid_indices:
            return None
        
        next_swings = df.iloc[valid_indices]
        
        weights = 1.0 / (nearest['distance'].iloc[:len(next_swings)] + 1e-6)
        
        predicted_range = np.average(next_swings['range'], weights=weights)
        predicted_duration = np.average(next_swings['duration_mins'], weights=weights)
        
        start_price = last_swing['end_price']
        start_time = last_swing['end_time']
        target_direction = 'Down' if last_direction == 'Up' else 'Up'
        
        target_price = start_price - predicted_range if target_direction == 'Down' else start_price + predicted_range
        target_time = start_time + pd.Timedelta(minutes=predicted_duration)
        
        return {
            'direction': target_direction,
            'target_price': target_price,
            'target_time': target_time,
            'predicted_range': predicted_range,
            'predicted_duration': predicted_duration
        }
    
    @staticmethod
    def backtest(swings_df, df=None, method='XGBoost', k=5, window=10, min_history=30, feature_tier='critical'):
        """
        Generic backtest with forex features support
        """
        if len(swings_df) < min_history + 1:
            return pd.DataFrame()
        
        predictions = []
        
        for i in range(min_history, len(swings_df)):
            current_history = swings_df.iloc[:i]
            
            pred = None
            if method == 'NN':
                pred = Analyzer.predict_next_swing_nn(current_history, k=k)
            elif method == 'XGBoost':
                pred = Analyzer.predict_next_swing_xgboost(current_history, df, window, feature_tier)
            elif method == 'LSTM':
                pred = Analyzer.predict_next_swing_lstm(current_history, df, window, feature_tier)
            
            if pred:
                actual = swings_df.iloc[i]
                pred['actual_end_price'] = actual['end_price']
                pred['actual_end_time'] = actual['end_time']
                pred['actual_direction'] = actual['direction']
                pred['actual_range'] = actual['range']
                pred['actual_duration'] = actual['duration_mins']
                
                pred['price_error'] = abs(pred['target_price'] - actual['end_price'])
                pred['price_error_pct'] = (pred['price_error'] / actual['end_price']) * 100 if actual['end_price'] != 0 else 0
                pred['range_error'] = abs(pred['predicted_range'] - actual['range'])
                pred['duration_error'] = abs(pred['predicted_duration'] - actual['duration_mins'])
                
                pred['start_time'] = actual['start_time']
                pred['start_price'] = actual['start_price']
                predictions.append(pred)
        
        return pd.DataFrame(predictions)
    
    @staticmethod
    def backtest_progressive(swings_df, df, method='XGBoost', window=10, 
                            min_history=30, feature_tier='critical',
                            recalc_interval=10):
        """
        FULLY REALISTIC BACKTEST with progressive ZigZag recalculation
        Fixes Lookahead Bias / Repainting issues.
        """
        if len(df) < 500:
            return pd.DataFrame()
        
        print("\n" + "="*80)
        print("PROGRESSIVE BACKTEST - No Lookahead Bias")
        print("="*80)
        print(f"Total bars: {len(df)}")
        print(f"Recalculation interval: {recalc_interval} bars")
        print(f"Method: {method}")
        print("="*80 + "\n")
        
        predictions = []
        start_bar = 500
        recalc_bars = list(range(start_bar, len(df), recalc_interval))
        
        for bar_idx in tqdm(recalc_bars, desc="Progressive Backtest"):
            # 1. Historical data only
            df_historical = df.iloc[:bar_idx].copy()
            
            # 2. Recalculate ZigZag (The core lookahead fix)
            df_historical['zigzag'] = Analyzer.calculate_zigzag(df_historical)
            
            # 3. Extract historical swings
            swings_historical = Analyzer.analyze_swings(df_historical, zigzag_col='zigzag')
            
            if len(swings_historical) < min_history:
                continue
            
            # 4. Features on historical data
            df_with_features = None
            if feature_tier != 'none':
                df_with_features = ForexFeatures.calculate_all(df_historical)
            
            # 5. Predict
            pred = None
            try:
                if method == 'NN':
                    pred = Analyzer.predict_next_swing_nn(swings_historical, k=5)
                elif method == 'XGBoost':
                    pred = Analyzer.predict_next_swing_xgboost(
                        swings_historical, df_with_features, window=window, feature_tier=feature_tier
                    )
                elif method == 'LSTM':
                    pred = Analyzer.predict_next_swing_lstm(
                        swings_historical, df_with_features, window=window, feature_tier=feature_tier
                    )
            except Exception as e:
                continue
            
            if not pred:
                continue
            
            # 6. Validate against ACTUAL future swing
            last_historical_time = swings_historical.iloc[-1]['end_time']
            future_swings = swings_df[swings_df['start_time'] > last_historical_time]
            
            if future_swings.empty:
                continue
            
            actual = future_swings.iloc[0]
            
            # 7. Metrics
            pred['actual_end_price'] = actual['end_price']
            pred['actual_end_time'] = actual['end_time']
            pred['actual_direction'] = actual['direction']
            pred['actual_range'] = actual['range']
            pred['actual_duration'] = actual['duration_mins']
            
            pred['price_error'] = abs(pred['target_price'] - actual['end_price'])
            pred['price_error_pct'] = (pred['price_error'] / actual['end_price']) * 100 if actual['end_price'] != 0 else 0
            pred['range_error'] = abs(pred['predicted_range'] - actual['range'])
            pred['duration_error'] = abs(pred['predicted_duration'] - actual['duration_mins'])
            
            pred['backtest_bar'] = bar_idx
            predictions.append(pred)
        
        results_df = pd.DataFrame(predictions)
        
        if not results_df.empty:
            scores = Analyzer.verify_performance(results_df)
            print(f"\nProgressive Metrics:")
            print(f"  Direction Accuracy: {scores.get('direction_accuracy', 0)*100:.2f}%")
            print(f"  Price MAPE: {scores.get('price_mape', 0)*100:.2f}%")
            
        return results_df

    @staticmethod
    def backtest_progressive_optimized(swings_df, df, method='XGBoost', window=10,
                                       min_history=30, feature_tier='critical',
                                       checkpoint_interval=50):
        """
        OPTIMIZED Progressive Backtest: Caches intermediate results for speed
        """
        predictions = []
        cache = {}
        start_bar = 500
        checkpoints = list(range(start_bar, len(df), checkpoint_interval))
        
        for bar_idx in tqdm(checkpoints, desc="Optimized Progressive"):
            if bar_idx not in cache:
                df_hist = df.iloc[:bar_idx].copy()
                df_hist['zigzag'] = Analyzer.calculate_zigzag(df_hist)
                swings_hist = Analyzer.analyze_swings(df_hist)
                
                if feature_tier != 'none':
                    df_hist = ForexFeatures.calculate_all(df_hist)
                
                cache[bar_idx] = {'df': df_hist, 'swings': swings_hist}
                if len(cache) > 10:
                    del cache[min(cache.keys())]
            
            cached = cache[bar_idx]
            swings_hist = cached['swings']
            df_hist = cached['df']
            
            if len(swings_hist) < min_history:
                continue
            
            pred = None
            if method == 'XGBoost':
                pred = Analyzer.predict_next_swing_xgboost(swings_hist, df_hist, window, feature_tier)
            
            if pred:
                last_time = swings_hist.iloc[-1]['end_time']
                future = swings_df[swings_df['start_time'] > last_time]
                
                if not future.empty:
                    actual = future.iloc[0]
                    pred['actual_end_price'] = actual['end_price']
                    pred['actual_end_time'] = actual['end_time']
                    pred['actual_direction'] = actual['direction']
                    pred['actual_range'] = actual['range']
                    pred['actual_duration'] = actual['duration_mins']
                    pred['price_error'] = abs(pred['target_price'] - actual['end_price'])
                    pred['price_error_pct'] = (pred['price_error'] / actual['end_price']) * 100 if actual['end_price'] != 0 else 0
                    predictions.append(pred)
        
        return pd.DataFrame(predictions)
    
    @staticmethod
    def verify_performance(backtest_results):
        """
        Calculates performance metrics
        """
        if backtest_results.empty:
            return {}
        
        results = {}
        
        def calculate_mape(actual, predicted):
            mask = actual != 0
            if not any(mask):
                return 1.0
            return (abs(actual[mask] - predicted[mask]) / abs(actual[mask])).mean()
        
        results['price_mape'] = calculate_mape(backtest_results['actual_end_price'], backtest_results['target_price'])
        results['range_mape'] = calculate_mape(backtest_results['actual_range'], backtest_results['predicted_range'])
        results['duration_mape'] = calculate_mape(backtest_results['actual_duration'], backtest_results['predicted_duration'])
        
        total = len(backtest_results)
        correct_dir = (backtest_results['direction'] == backtest_results['actual_direction']).sum()
        results['direction_accuracy'] = correct_dir / total if total > 0 else 0
        
        return results
    
    @staticmethod
    def save_backtest_report(backtest_results, scores, model_name, symbol='Unknown'):
        """
        Saves comprehensive backtest report
        """
        if not os.path.exists('reports'):
            os.makedirs('reports')
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/report_{model_name}_{symbol}_{timestamp}.csv"
        summary_file = f"reports/summary_{model_name}_{symbol}_{timestamp}.md"
        html_file = f"reports/{model_name.lower()}_backtest_{symbol}_{timestamp}.html"
        
        # CSV
        backtest_results.to_csv(report_file, index=False)
        
        # Markdown Summary
        with open(summary_file, 'w') as f:
            f.write(f"# Midas Backtest Summary: {model_name} ({symbol})\n")
            f.write(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Performance Scores\n")
            for k, v in scores.items():
                line = f"- **{k.replace('_', ' ').title()}**: {v*100:.2f}%\n" if 'mape' in k or 'accuracy' in k else f"- **{k}**: {v}\n"
                f.write(line)
            
            if not backtest_results.empty:
                last_bt = backtest_results.iloc[-1]
                f.write("\n## Latest Backtest Sample\n")
                f.write(f"- **Predicted Price**: {last_bt['target_price']:.5f}\n")
                f.write(f"- **Actual Price**: {last_bt['actual_end_price']:.5f}\n")
                f.write(f"- **Price Error**: {last_bt['price_error']:.5f} ({last_bt.get('price_error_pct', 0):.2f}%)\n")
                f.write(f"- **Direction**: {last_bt['direction']} (Actual: {last_bt['actual_direction']})\n")
            
            f.write(f"\nCSV Report: {report_file}\n")
            f.write(f"HTML Dashboard: {html_file}\n")
        
        # HTML Interactive Report
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           subplot_titles=(f'Predicted vs Actual ({symbol})', 'Price Error Distribution'),
                           vertical_spacing=0.1)
        
        vis_df = backtest_results.tail(100)
        fig.add_trace(go.Scatter(x=vis_df['actual_end_time'], y=vis_df['actual_end_price'],
                                mode='lines+markers', name='Actual Price', line=dict(color='lime')), row=1, col=1)
        fig.add_trace(go.Scatter(x=vis_df['target_time'], y=vis_df['target_price'],
                                mode='lines+markers', name='Predicted Target', line=dict(color='magenta', dash='dot')), row=1, col=1)
        
        fig.add_trace(go.Histogram(x=backtest_results['price_error'], name='Price Error Dist',
                                   nbinsx=30, marker_color='red'), row=2, col=1)
        
        fig.update_layout(title=f'Midas ML Report - {model_name} | {symbol}', template='plotly_dark', height=800)
        pyo.plot(fig, filename=html_file, auto_open=False)
        
        return report_file, summary_file, html_file
    
    # Pattern detection methods (unchanged from V1)
    @staticmethod
    def detect_sot(swings_df):
        """Detects Shortening of Thrust"""
        if len(swings_df) < 5:
            return pd.DataFrame()
        
        sot_signals = []
        
        for direction in ['Up', 'Down']:
            dir_swings = swings_df[swings_df['direction'] == direction].copy()
            if len(dir_swings) < 3:
                continue
            
            for i in range(2, len(dir_swings)):
                w1 = dir_swings.iloc[i-2]
                w2 = dir_swings.iloc[i-1]
                w3 = dir_swings.iloc[i]
                
                if w3['range'] < w2['range'] < w1['range']:
                    effort_vs_result = w3['intensity'] > w2['intensity']
                    
                    sot_signals.append({
                        'time': w3['end_time'],
                        'direction': direction,
                        'type': 'SOT',
                        'effort_anomalous': effort_vs_result,
                        'price': w3['end_price'],
                        'w1_range': w1['range'],
                        'w2_range': w2['range'],
                        'w3_range': w3['range']
                    })
        
        return pd.DataFrame(sot_signals)
    
    @staticmethod
    def detect_hinge(swings_df, window=4):
        """Detects Hinge/Apex patterns"""
        if len(swings_df) < window:
            return pd.DataFrame()
        
        hinge_signals = []
        
        for i in range(window - 1, len(swings_df)):
            subset = swings_df.iloc[i-(window-1) : i+1]
            
            ranges = subset['range'].values
            is_range_shrinking = all(ranges[j] < ranges[j-1] * 1.1 for j in range(1, len(ranges)))
            
            avg_range = swings_df['range'].rolling(20).mean().iloc[i]
            is_tight = subset['range'].iloc[-1] < avg_range * 0.5
            
            intensities = subset['intensity'].values
            is_dull = intensities[-1] < intensities[0]
            
            if is_range_shrinking and is_tight and is_dull:
                hinge_signals.append({
                    'time': subset['end_time'].iloc[-1],
                    'price': subset['end_price'].iloc[-1],
                    'type': 'Hinge',
                    'avg_range_at_time': avg_range,
                    'current_range': subset['range'].iloc[-1]
                })
        
        return pd.DataFrame(hinge_signals)
    
    @staticmethod
    def detect_multi_extremes(swings_df, tolerance=0.015):
        """Detects Double/Triple Tops and Bottoms"""
        if len(swings_df) < 5:
            return pd.DataFrame()
        
        highs = swings_df[swings_df['direction'] == 'Up'].copy()
        lows = swings_df[swings_df['direction'] == 'Down'].copy()
        signals = []
        
        for i in range(2, len(highs)):
            prices = [highs.iloc[i]['end_price'], highs.iloc[i-1]['end_price'], highs.iloc[i-2]['end_price']]
            base_p = prices[0]
            
            if all(abs(p - base_p) / base_p < tolerance for p in prices):
                signals.append({'time': highs.iloc[i]['end_time'], 'type': 'Triple Top', 'price': base_p})
            elif abs(prices[0] - prices[1]) / prices[1] < tolerance:
                signals.append({'time': highs.iloc[i]['end_time'], 'type': 'Double Top', 'price': base_p})
        
        for i in range(2, len(lows)):
            prices = [lows.iloc[i]['end_price'], lows.iloc[i-1]['end_price'], lows.iloc[i-2]['end_price']]
            base_p = prices[0]
            
            if all(abs(p - base_p) / base_p < tolerance for p in prices):
                signals.append({'time': lows.iloc[i]['end_time'], 'type': 'Triple Bottom', 'price': base_p})
            elif abs(prices[0] - prices[1]) / prices[1] < tolerance:
                signals.append({'time': lows.iloc[i]['end_time'], 'type': 'Double Bottom', 'price': base_p})
        
        return pd.DataFrame(signals)

    @staticmethod
    def detect_reversal_signatures(swings_df, df, tolerance=0.015):
        """
        Production logic: Correlates price extremes with VSA signatures
        Identifies 'High Quality' reversal zones including Takeover signals.
        """
        # 1. Detect price patterns
        extremes = Analyzer.detect_multi_extremes(swings_df, tolerance)
        if extremes.empty:
            return pd.DataFrame()
        
        # 2. Correlate with VSA features from df
        reversals = []
        
        for _, row in extremes.iterrows():
            # Find closest bar in df to correlate VSA
            idx = df[df['time'] <= row['time']].index[-1]
            if idx < 2: continue
            
            bar_data = df.iloc[idx]
            prev_1 = df.iloc[idx-1]
            prev_2 = df.iloc[idx-2]
            
            # Signature Identification
            is_climax = bar_data.get('climax_score', 0) > 70
            is_anomaly = bar_data.get('high_vol_anomaly', False)
            is_test = bar_data.get('up_test', False) or bar_data.get('down_test', False)
            is_spring = bar_data.get('is_spring', False)
            is_upthrust = bar_data.get('is_upthrust', False)
            
            # Takeover Logic (Enhanced)
            is_low_takeover = False
            is_high_takeover = False
            
            # Bullish Takeover (Low Takeover) at Bottoms
            if 'Bottom' in row['type']:
                vol_condition = bar_data['tick_volume'] > max(prev_1['tick_volume'], prev_2['tick_volume'])
                engulf_condition = (prev_1['close'] < prev_1['open']) and \
                                   (bar_data['close'] > max(prev_1['open'], prev_1['close']))
                is_low_takeover = vol_condition and engulf_condition

            # Bearish Takeover (High Takeover) at Tops
            if 'Top' in row['type']:
                vol_condition = bar_data['tick_volume'] > max(prev_1['tick_volume'], prev_2['tick_volume'])
                engulf_condition = (prev_1['close'] > prev_1['open']) and \
                                   (bar_data['close'] < min(prev_1['open'], prev_1['close']))
                is_high_takeover = vol_condition and engulf_condition
            
            strength = 0
            if is_climax: strength += 40
            if is_anomaly: strength += 30
            if is_test: strength += 30
            if is_spring or is_upthrust: strength += 50
            if is_low_takeover or is_high_takeover: strength += 20 
            
            # Build descriptive signal string
            signals = []
            if is_climax: signals.append("Climax")
            if is_anomaly: signals.append("Anomaly")
            if is_test: signals.append("Test")
            if is_spring: signals.append("Spring")
            if is_upthrust: signals.append("Upthrust")
            if is_low_takeover: signals.append("LowTakeover")
            if is_high_takeover: signals.append("HighTakeover")
            
            vsa_sig = "+".join(signals) if signals else "None"

            reversals.append({
                'time': row['time'],
                'type': row['type'],
                'price': row['price'],
                'strength': min(strength, 100),
                'climax_score': bar_data.get('climax_score', 0),
                'vsa_signal': vsa_sig,
                'is_takeover': is_low_takeover or is_high_takeover,
                'is_spring': is_spring,
                'is_upthrust': is_upthrust,
                'exhaustion': bar_data.get('exhaustion_signal', 0)
            })
            
        return pd.DataFrame(reversals)


class DashboardBuilder:
    """
    Dedicated class for V3 Reversal Dashboard
    """
    @staticmethod
    def plot_reversal_analytics(df, reversals, symbol='Unknown'):
        """
        Generates the Reversal Analytics Dashboard
        """
        # Use only latest 300 bars for visibility
        vis_df = df.tail(300).copy()
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           subplot_titles=(f'Price & Reversal Signatures ({symbol})', 'Volume & Analysis'),
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])

        # Candlestick
        fig.add_trace(go.Candlestick(x=vis_df['time'],
                                    open=vis_df['open'], high=vis_df['high'],
                                    low=vis_df['low'], close=vis_df['close'],
                                    name='Price'), row=1, col=1)

        # Plot reversals markers
        if not reversals.empty:
            # Filter reversals within vis_df range
            vis_revs = reversals[reversals['time'] >= vis_df['time'].iloc[0]]
            
            # Dynamic nudge based on price range
            y_range = vis_df['high'].max() - vis_df['low'].min()
            nudge = y_range * 0.05
            
            # Tops
            tops = vis_revs[vis_revs['type'].str.contains('Top')]
            if not tops.empty:
                # Main reversal arrow
                fig.add_trace(go.Scatter(x=tops['time'], y=tops['price'] + nudge,
                                        mode='markers+text', name='Resistance Cluster',
                                        marker=dict(symbol='triangle-down', size=12, color='red'),
                                        text=tops['vsa_signal'], textposition='top center'), row=1, col=1)
                
                # Takeover Dot (Red Dot Above)
                to_tops = tops[tops['is_takeover']]
                if not to_tops.empty:
                    fig.add_trace(go.Scatter(x=to_tops['time'], y=to_tops['price'] + (nudge * 0.4),
                                            mode='markers', name='High Takeover',
                                            marker=dict(symbol='circle', size=6, color='red')), row=1, col=1)

                # Upthrust Diamond (Red Diamond Above)
                ut_tops = tops[tops['is_upthrust']]
                if not ut_tops.empty:
                    fig.add_trace(go.Scatter(x=ut_tops['time'], y=ut_tops['price'] + (nudge * 0.7),
                                            mode='markers', name='Upthrust',
                                            marker=dict(symbol='diamond', size=8, color='orange')), row=1, col=1)
            
            # Bottoms
            bots = vis_revs[vis_revs['type'].str.contains('Bottom')]
            if not bots.empty:
                # Main reversal arrow
                fig.add_trace(go.Scatter(x=bots['time'], y=bots['price'] - nudge,
                                        mode='markers+text', name='Support Cluster',
                                        marker=dict(symbol='triangle-up', size=12, color='lime'),
                                        text=bots['vsa_signal'], textposition='bottom center'), row=1, col=1)
                
                # Takeover Dot (Green Dot Below)
                to_bots = bots[bots['is_takeover']]
                if not to_bots.empty:
                    fig.add_trace(go.Scatter(x=to_bots['time'], y=to_bots['price'] - (nudge * 0.4),
                                            mode='markers', name='Low Takeover',
                                            marker=dict(symbol='circle', size=6, color='lime')), row=1, col=1)

                # Spring Diamond (Green Diamond Below)
                sp_bots = bots[bots['is_spring']]
                if not sp_bots.empty:
                    fig.add_trace(go.Scatter(x=sp_bots['time'], y=sp_bots['price'] - (nudge * 0.7),
                                            mode='markers', name='Spring',
                                            marker=dict(symbol='diamond', size=8, color='cyan')), row=1, col=1)

        # Volume
        colors = ['red' if row['close'] < row['open'] else 'lime' for _, row in vis_df.iterrows()]
        fig.add_trace(go.Bar(x=vis_df['time'], y=vis_df['tick_volume'], 
                            marker_color=colors, name='Volume', opacity=0.5), row=2, col=1)
        
        # High Vol Anomaly line
        if 'ewm_vol_20' in vis_df.columns:
            fig.add_trace(go.Scatter(x=vis_df['time'], y=vis_df['ewm_vol_20'] * 1.9,
                                    line=dict(color='yellow', dash='dot'), name='Anomaly Threshold'), row=2, col=1)

        fig.update_layout(height=1000, template='plotly_dark', title_text=f"MIDAS V3 - {symbol} Reversal Dashboard",
                          xaxis_rangeslider_visible=False)
        
        return fig


class ValidationTools:
    """
    Testing and validation utilities
    """
    
    @staticmethod
    def test_data_leakage(swings_df, df=None, window=10):
        """
        Comprehensive data leakage test
        """
        test_swings = swings_df.iloc[:100].copy() if len(swings_df) > 100 else swings_df.copy()
        X, y, latest_X = Analyzer.prepare_ml_features(test_swings, df, window=window)
        
        if X is None:
            return False
        
        last_target_range = y[-1][0]
        swing_98_range = test_swings.iloc[-2]['range']
        swing_99_range = test_swings.iloc[-1]['range']
        
        match_98 = abs(last_target_range - swing_98_range) < 0.0001
        match_99 = abs(last_target_range - swing_99_range) < 0.0001
        
        return match_98 and not match_99
    
    @staticmethod
    def compare_feature_tiers(swings_df, df):
        """
        A/B test: Compare performance across feature tiers
        """
        print("\n" + "="*80)
        print("A/B TEST: Feature Tier Comparison")
        print("="*80)
        
        from sklearn.model_selection import train_test_split
        
        results = {}
        
        for tier in ['critical', 'important', 'useful', 'all']:
            print(f"\n[Testing tier: {tier}]")
            
            X, y, _ = Analyzer.prepare_ml_features(swings_df, df, window=10, feature_tier=tier)
            
            if X is None or len(X) < 50:
                print(f"  ⚠️  Skipping {tier} - insufficient data")
                continue
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            model = xgb.XGBRegressor(n_estimators=50, max_depth=3)
            model.fit(X_train, y_train[:, 0])
            
            pred = model.predict(X_test)
            mape = np.mean(np.abs(pred - y_test[:, 0]) / y_test[:, 0]) * 100
            
            results[tier] = mape
            print(f"  ✓ Range MAPE: {mape:.2f}%")
        
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)
        
        baseline = results.get('critical', 0)
        for tier, mape in results.items():
            improvement = ((baseline - mape) / baseline * 100) if baseline > 0 else 0
            print(f"{tier:12s}: {mape:6.2f}% MAPE ({improvement:+.1f}% vs critical)")
        
        print("="*80)
        
        return results


# Example usage and main workflow
if __name__ == "__main__":
    pass
