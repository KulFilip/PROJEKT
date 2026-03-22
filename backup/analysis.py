import numpy as np
import pandas as pd
from scipy.spatial import distance
import config
import scipy.stats as stats
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Silence TF
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Analyzer:
    @staticmethod
    def calculate_zigzag(df, depth=config.ZIGZAG_DEPTH, deviation=config.ZIGZAG_DEVIATION, backstep=config.ZIGZAG_BACKSTEP, point=config.POINT):
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
        
        # Find first point
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
            if whatlookfor == 1: # Looking for High
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
                     
            elif whatlookfor == -1: # Looking for Low
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
        df['zigzag_val'] = df[zigzag_col].replace(0, np.nan)
        pivots = df[df['zigzag_val'].notna()].copy()
        pivots['prev_time'] = pivots['time'].shift(1)
        pivots['prev_val'] = pivots['zigzag_val'].shift(1)
        
        swings = []
        
        for idx, row in pivots.iterrows():
            if pd.isna(row['prev_val']): continue
            
            # Simple duration in minutes
            duration_mins = (row['time'] - row['prev_time']).total_seconds() / 60
            direction = 'Up' if row['zigzag_val'] > row['prev_val'] else 'Down'
            price_range = abs(row['zigzag_val'] - row['prev_val'])
            
            # Volume finding (requires index alignment, using time filter is safer)
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
    def predict_next_swing_nn(swings_df, k=5):
        if len(swings_df) < k + 2:
            return None
            
        # Preparation
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
        
        # Search history for SAME direction swings (to find what happened AFTER them)
        # Actually logic: We want to match the LAST COMPLETED swing (e.g. DOWN) to historical DOWN swings
        # And see what the NEXT swing (UP) looked like.
        
        history = df.iloc[:-1] # Exclude current
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
        
        # Get NEXT swings
        next_indices = [df.index.get_loc(idx) + 1 for idx in nearest.index]
        valid_indices = [i for i in next_indices if i < len(df)]
        
        if not valid_indices:
            return None
            
        next_swings = df.iloc[valid_indices]
        
        # Weights
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
    def backtest(swings_df, method='NN', k=5, window=10, min_history=30):
        """
        Generic backtest. Retrains model at each step to strictly prevent lookahead.
        """
        if len(swings_df) < min_history + 1:
            return pd.DataFrame()

        predictions = []
        for i in range(min_history, len(swings_df)):
            # History is strictly BEFORE the swing we want to predict
            current_history = swings_df.iloc[:i] 
            
            pred = None
            if method == 'NN':
                pred = Analyzer.predict_next_swing_nn(current_history, k=k)
            elif method == 'XGBoost':
                pred = Analyzer.predict_next_swing_xgboost(current_history, window=window)
            elif method == 'LSTM':
                pred = Analyzer.predict_next_swing_lstm(current_history, window=window)
                
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
    def backtest_walk_forward(swings_df, method='XGBoost', window=10, train_size=100, test_size=20):
        """
        Walk-forward backtest: Retrains on sliding window blocks to evaluate stability.
        """
        if len(swings_df) < train_size + test_size + window:
            return pd.DataFrame()
            
        predictions = []
        for start_idx in range(0, len(swings_df) - train_size - test_size, test_size):
            train_data = swings_df.iloc[start_idx : start_idx + train_size]
            test_data = swings_df.iloc[start_idx + train_size : start_idx + train_size + test_size]
            
            # Predict each swing in the test block using ONLY cumulative history
            for i in range(len(test_data)):
                cumulative_history = pd.concat([train_data, test_data.iloc[:i]])
                
                pred = None
                if method == 'XGBoost':
                    pred = Analyzer.predict_next_swing_xgboost(cumulative_history, window=window)
                elif method == 'LSTM':
                    pred = Analyzer.predict_next_swing_lstm(cumulative_history, window=window)
                    
                if pred:
                    actual = test_data.iloc[i]
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
    def detect_sot(swings_df):
        """
        Detects 'Shortening of the Thrust' (SOT) in swings.
        Requires at least 3 consecutive swings in the SAME direction.
        SOT occurs when each consecutive swing covers less distance than the previous one.
        """
        if len(swings_df) < 5: # Need at least 5 swings to see alternating patterns clearly, though we look at 3 same-dir
            return pd.DataFrame()

        sot_signals = []
        
        # We need to look at swings of the same direction
        for direction in ['Up', 'Down']:
            dir_swings = swings_df[swings_df['direction'] == direction].copy()
            if len(dir_swings) < 3: continue
            
            # Check 3 consecutive waves in same direction
            for i in range(2, len(dir_swings)):
                w1 = dir_swings.iloc[i-2] # Oldest
                w2 = dir_swings.iloc[i-1]
                w3 = dir_swings.iloc[i]   # Newest
                
                # Logic: w3 range < w2 range < w1 range
                if w3['range'] < w2['range'] < w1['range']:
                    # SOT Detected
                    # Effort vs Result check: If w3 volume is high relative to its range
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
        """
        Detects 'Hinge' or 'Apex' (Dullness).
        Occurs when volatility (range) and volume/intensity are shrinking.
        Indicates the market is coiling before a 'Springboard' move.
        """
        if len(swings_df) < window:
            return pd.DataFrame()

        hinge_signals = []
        
        # Check the last 'window' swings
        for i in range(window - 1, len(swings_df)):
            subset = swings_df.iloc[i-(window-1) : i+1]
            
            # 1. Check if ranges are generally decreasing
            ranges = subset['range'].values
            is_range_shrinking = all(ranges[j] < ranges[j-1] * 1.1 for j in range(1, len(ranges))) # Soft decrease
            
            # 2. Check if absolute range is small compared to recent average
            avg_range = swings_df['range'].rolling(20).mean().iloc[i]
            is_tight = subset['range'].iloc[-1] < avg_range * 0.5
            
            # 3. Check for declining volume or intensity
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
    def detect_springboard(swings_df, hinge_df):
        """
        Detects 'Springboard' - an intentional breakout from a Hinge/Apex.
        A springboard is a fast, aggressive swing that breaks the range of a recent Hinge.
        """
        if hinge_df.empty or swings_df.empty:
            return pd.DataFrame()

        # Get the latest hinge
        latest_hinge = hinge_df.iloc[-1]
        
        # Look for the next swing after the hinge
        breakout_swings = swings_df[swings_df['start_time'] >= latest_hinge['time']]
        
        if breakout_swings.empty:
            return pd.DataFrame()
            
        springboards = []
        for _, swing in breakout_swings.iterrows():
            # Logic: If swing velocity and intensity are high compared to the hinge
            if swing['velocity'] > (latest_hinge['current_range'] / 1.0) and swing['intensity'] > 0:
                springboards.append({
                    'time': swing['end_time'],
                    'direction': swing['direction'],
                    'type': 'Springboard',
                    'price': swing['end_price']
                })
        
        return pd.DataFrame(springboards)

    @staticmethod
    def verify_performance(backtest_results):
        """
        Scores model performance using MAPE and financial metrics.
        """
        if backtest_results.empty: 
            return {'direction_accuracy': 0, 'price_mape': 1}
            
        def calculate_mape(actual, predicted):
            mask = actual != 0
            if not any(mask): return 1.0
            return (abs(actual[mask] - predicted[mask]) / abs(actual[mask])).mean()

        results = {}
        results['price_mape'] = calculate_mape(backtest_results['actual_end_price'], backtest_results['target_price'])
        results['range_mape'] = calculate_mape(backtest_results['actual_range'], backtest_results['predicted_range'])
        results['duration_mape'] = calculate_mape(backtest_results['actual_duration'], backtest_results['predicted_duration'])
        
        # Direction Accuracy
        correct_dir = (backtest_results['direction'] == backtest_results['actual_direction']).sum()
        results['direction_accuracy'] = correct_dir / len(backtest_results)
        
        # Financial Metrics
        # Returns based on predicted direction and actual price move
        if 'start_price' in backtest_results.columns:
            actual_move = (backtest_results['actual_end_price'] - backtest_results['start_price']) / backtest_results['start_price']
            # If we predicted Up (1) and move is positive, win. If Down (-1) and move is negative, win.
            p_dir = backtest_results['direction'].apply(lambda x: 1 if x == 'Up' else -1)
            strat_returns = p_dir * actual_move
            
            results['win_rate'] = (strat_returns > 0).sum() / len(strat_returns)
            
            if len(strat_returns) > 1:
                results['sharpe_ratio'] = (strat_returns.mean() / strat_returns.std()) * np.sqrt(252) if strat_returns.std() != 0 else 0
            else:
                results['sharpe_ratio'] = 0
                
            cum_returns = (1 + strat_returns).cumprod()
            running_max = cum_returns.cummax()
            drawdown = (cum_returns - running_max) / running_max if not running_max.empty else pd.Series(0)
            results['max_drawdown'] = drawdown.min()
        
        results['avg_duration'] = backtest_results['actual_duration'].mean()
        
        return results

    @staticmethod
    def extract_swing_features(subset):
        """
        Extracts a flat feature vector from a subset of swings.
        Used for XGBoost and as a component for LSTM sequences.
        """
        row = []
        for j in range(len(subset)):
            s = subset.iloc[j]
            # Core behavioral features
            row.extend([
                1 if s['direction'] == 'Up' else 0,
                s['range'],
                s['duration_mins'],
                s['volume'],
                s['intensity'],
                s['range'] / s['duration_mins'] if s['duration_mins'] != 0 else 0 # Velocity
            ])
            # Relative features (Wyckoff Ratios)
            if j > 0:
                prev_s = subset.iloc[j-1]
                row.extend([
                    s['range'] / prev_s['range'] if prev_s['range'] != 0 else 1.0,
                    s['duration_mins'] / prev_s['duration_mins'] if prev_s['duration_mins'] != 0 else 1.0
                ])
            else:
                row.extend([1.0, 1.0])
        return row

    @staticmethod
    def prepare_ml_features(swings_df, window=10):
        """
        Prepares features (X) and targets (y) with strict lookahead prevention.
        - For XGBoost: X is (samples, window * 8)
        - For LSTM: X is (samples, window, 8)
        - Targets y include: [range, duration, price_delta_pct]
        """
        if len(swings_df) < window + 1:
            return None, None, None

        features = []
        targets = []
        
        # Training data: Each target i depends strictly on swings [i-window : i]
        for i in range(window, len(swings_df)):
            subset = swings_df.iloc[i-window:i]
            target = swings_df.iloc[i]
            
            # Extract features for this window
            row = Analyzer.extract_swing_features(subset)
            features.append(row)
            
            # Target is the NEXT swing
            price_delta_pct = (target['end_price'] - subset.iloc[-1]['end_price']) / subset.iloc[-1]['end_price']
            targets.append([target['range'], target['duration_mins'], price_delta_pct])
            
        X = np.array(features)
        y = np.array(targets)
        
        # Features for the FUTURE prediction (very latest window)
        latest_subset = swings_df.iloc[-window:]
        latest_X = np.array(Analyzer.extract_swing_features(latest_subset)).reshape(1, -1)
        
        return X, y, latest_X

    @staticmethod
    def predict_next_swing_xgboost(swings_df, window=10):
        """
        Predicts next swing using XGBoost. Correctly handles future prediction.
        """
        X, y, latest_X = Analyzer.prepare_ml_features(swings_df, window=window)
        if X is None or len(X) < 20: 
            return None

        # Train on all available history
        model_range = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
        model_range.fit(X, y[:, 0])
        pred_range = model_range.predict(latest_X)[0]
        
        model_dur = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
        model_dur.fit(X, y[:, 1])
        pred_dur = model_dur.predict(latest_X)[0]

        model_price = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, subsample=0.8)
        model_price.fit(X, y[:, 2])
        pred_price_delta = model_price.predict(latest_X)[0]
        
        last_swing = swings_df.iloc[-1]
        next_dir = 'Down' if last_swing['direction'] == 'Up' else 'Up'
        
        # Absolute price derived from relative delta
        pred_price = last_swing['end_price'] * (1 + pred_price_delta)
        
        # Price calculated from range for comparison
        calc_price = last_swing['end_price'] + (pred_range if next_dir == 'Up' else -pred_range)
        target_time = pd.Timestamp(last_swing['end_time']) + pd.Timedelta(minutes=float(abs(pred_dur)))
        
        return {
            'direction': next_dir,
            'target_price': float(pred_price), # Absolute prediction
            'calc_target_price': float(calc_price), # Based on range
            'target_time': target_time,
            'predicted_range': float(pred_range),
            'predicted_duration': float(pred_dur)
        }

    @staticmethod
    def predict_next_swing_lstm(swings_df, window=10):
        """
        Predicts next swing using an LSTM model. Correctly handles future prediction and sequencing.
        """
        X, y, latest_X_raw = Analyzer.prepare_ml_features(swings_df, window=window)
        if X is None or len(X) < 40: 
            return None

        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        
        X_scaled = scaler_X.fit_transform(X)
        y_scaled = scaler_y.fit_transform(y)
        
        # Reshape to (samples, window, features_per_swing)
        # features_per_swing is 8 (direction, range, dur, vol, intent, vel, range_ratio, dur_ratio)
        features_per_swing = 8 
        X_lstm = X_scaled.reshape(X_scaled.shape[0], window, features_per_swing)
        
        latest_X_scaled = scaler_X.transform(latest_X_raw)
        latest_X = latest_X_scaled.reshape(1, window, features_per_swing)
        
        # Models
        model = Sequential([
            LSTM(64, input_shape=(window, features_per_swing), return_sequences=True),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(2)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X_lstm, y_scaled[:, :2], epochs=30, batch_size=16, verbose=0)
        
        model_p = Sequential([
            LSTM(64, input_shape=(window, features_per_swing), return_sequences=False),
            Dense(32, activation='relu'),
            Dense(1)
        ])
        model_p.compile(optimizer='adam', loss='mse')
        model_p.fit(X_lstm, y_scaled[:, 2], epochs=30, batch_size=16, verbose=0)

        # Predict
        preds_scaled = model.predict(latest_X, verbose=0)
        preds_p_scaled = model_p.predict(latest_X, verbose=0)
        
        dummy_y = np.zeros((1, 3))
        dummy_y[0, :2] = preds_scaled[0]
        dummy_y[0, 2] = preds_p_scaled[0][0]
        
        final_preds = scaler_y.inverse_transform(dummy_y)[0]
        
        pred_range = float(final_preds[0])
        pred_dur = float(final_preds[1])
        pred_price_delta = float(final_preds[2])
        
        last_swing = swings_df.iloc[-1]
        next_dir = 'Down' if last_swing['direction'] == 'Up' else 'Up'
        pred_price = last_swing['end_price'] * (1 + pred_price_delta)
        calc_price = last_swing['end_price'] + (pred_range if next_dir == 'Up' else -pred_range)
        target_time = pd.Timestamp(last_swing['end_time']) + pd.Timedelta(minutes=abs(float(pred_dur)))
        
        return {
            'direction': next_dir,
            'target_price': pred_price,
            'calc_target_price': calc_price,
            'target_time': target_time,
            'predicted_range': pred_range,
            'predicted_duration': pred_dur
        }

    @staticmethod
    def detect_climax(df, volume_col='tick_volume', threshold=1.9):
        """
        Detects Buying/Selling Climax (Kulminacja).
        Trend acceleration with ultra-high volume and wide spread, followed by stagnation.
        """
        if df.empty: return pd.DataFrame()
        
        # Calculate volume average/std
        vol_avg = df[volume_col].rolling(window=50).mean()
        vol_std = df[volume_col].rolling(window=50).std()
        
        df['spread'] = abs(df['high'] - df['low'])
        spread_avg = df['spread'].rolling(window=50).mean()
        
        # ultra high volume and wide spread
        is_vol_climax = df[volume_col] > (vol_avg + 3 * vol_std)
        is_spread_climax = df['spread'] > (2.0 * spread_avg)
        
        climax_signals = []
        for i in range(1, len(df)):
            if is_vol_climax.iloc[i] and is_spread_climax.iloc[i]:
                # Buying Climax: Up trend, wide spread, high volume, but close < high
                if df['close'].iloc[i] > df['open'].iloc[i]:
                    wick_top = df['high'].iloc[i] - df['close'].iloc[i]
                    if wick_top > (df['spread'].iloc[i] * 0.3): # Significant upper wick
                        climax_signals.append({'time': df['time'].iloc[i], 'type': 'Buying Climax', 'price': df['high'].iloc[i]})
                # Selling Climax: Down trend, wide spread, high volume, but close > low
                elif df['close'].iloc[i] < df['open'].iloc[i]:
                    wick_bottom = df['close'].iloc[i] - df['low'].iloc[i]
                    if wick_bottom > (df['spread'].iloc[i] * 0.3): # Significant lower wick
                        climax_signals.append({'time': df['time'].iloc[i], 'type': 'Selling Climax', 'price': df['low'].iloc[i]})
                        
        return pd.DataFrame(climax_signals)

    @staticmethod
    def analyze_effort_vs_result(swings_df):
        """
        Detects Effort vs Result anomalies (Wyckoff).
        High volume (effort) but low price progress (result) at swing points.
        """
        if len(swings_df) < 2: return pd.DataFrame()
        
        anomalies = []
        vol_avg = swings_df['volume'].mean()
        range_avg = swings_df['range'].mean()
        
        for i in range(len(swings_df)):
            row = swings_df.iloc[i]
            # sfor: high volume but range is small relative to volume
            effort = row['volume'] / vol_avg
            result = row['range'] / range_avg
            
            if effort > 1.5 and result < 0.7:
                anomalies.append({
                    'time': row['end_time'],
                    'type': 'Effort-Result Divergence',
                    'price': row['end_price'],
                    'direction': row['direction']
                })
        
        return pd.DataFrame(anomalies)

    @staticmethod
    def save_backtest_report(backtest_results, scores, model_name, db_manager=None, symbol='Unknown'):
        """
        Saves the backtest results to CSV, Markdown, and fully interactive HTML.
        Includes an equity-like chart showing predicted vs actual performance.
        Now includes latest prediction summary.
        """
        import datetime
        import plotly.offline as pyo
        from plotly.subplots import make_subplots
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/report_{model_name}_{symbol}_{timestamp}.csv"
        summary_file = f"reports/summary_{model_name}_{symbol}_{timestamp}.md"
        html_file = f"reports/{model_name.lower()}_backtest_{symbol}_{timestamp}.html"
        
        # 1. Save results to CSV
        backtest_results.to_csv(report_file, index=False)
        
        # 2. Save summary to Markdown
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

        # 3. Create interactive HTML Report
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            subplot_titles=(f'Predicted Targets vs Actual Ends ({symbol})', 'Prediction Error Distribution'),
                            vertical_spacing=0.1)
        
        # Plot Actuals vs Predictions
        vis_df = backtest_results.tail(100) # Last 100 predictions for clarity
        fig.add_trace(go.Scatter(x=vis_df['actual_end_time'], y=vis_df['actual_end_price'], 
                                 mode='lines+markers', name='Actual Price', line=dict(color='lime')), row=1, col=1)
        fig.add_trace(go.Scatter(x=vis_df['target_time'], y=vis_df['target_price'], 
                                 mode='lines+markers', name='Predicted Target', line=dict(color='magenta', dash='dot')), row=1, col=1)
        
        # Error Bars / Distribution
        fig.add_trace(go.Histogram(x=backtest_results['price_error'], name='Price Error Dist', nbinsx=30, marker_color='red'), row=2, col=1)
        
        fig.update_layout(title=f'Midas ML Report - {model_name} | {symbol}', template='plotly_dark', height=800)
        pyo.plot(fig, filename=html_file, auto_open=False)
        
        # Log to Database
        if db_manager:
            db_manager.save_performance_metrics(model_name, symbol, scores)
            
        print(f"Interactive HTML report generated: {html_file}")
        return report_file, summary_file

    @staticmethod
    def calculate_volume_profile(df, n_bins=20):
        """
        Calculates basic Volume Profile (VAH, VAL, VPOC).
        """
        if df.empty: return None
        
        # Determine price range
        min_p = df['low'].min()
        max_p = df['high'].max()
        
        # Create bins
        bins = np.linspace(min_p, max_p, n_bins + 1)
        labels = (bins[:-1] + bins[1:]) / 2
        
        # Distribute volume into bins
        df['price_bin'] = pd.cut((df['high'] + df['low']) / 2, bins=bins, labels=labels)
        profile = df.groupby('price_bin')['tick_volume'].sum()
        
        total_vol = profile.sum()
        vpoc = float(profile.idxmax())
        
        # Value Area (approx 70% of volume around VPOC)
        profile_sorted = profile.sort_values(ascending=False)
        cum_vol = 0
        va_prices = []
        for price, vol in profile_sorted.items():
            cum_vol += vol
            va_prices.append(float(price))
            if cum_vol >= 0.7 * total_vol:
                break
        
        vah = max(va_prices)
        val = min(va_prices)
        
        return {'vah': vah, 'val': val, 'vpoc': vpoc}

    @staticmethod
    def detect_absorption_initiative(df, window=5):
        """
        Identifies signs of takeover (absorption) and momentum starts (initiative).
        Absorption: Aggressive price movement meets huge volume but stalls.
        Initiative: Large volume accompanies a breakout.
        """
        if len(df) < 10: return pd.DataFrame()
        
        signals = []
        vol_avg = df['tick_volume'].rolling(window=20).mean()
        
        for i in range(1, len(df)):
            if df['tick_volume'].iloc[i] > (1.5 * vol_avg.iloc[i]):
                spread = abs(df['close'].iloc[i] - df['open'].iloc[i])
                total_range = df['high'].iloc[i] - df['low'].iloc[i]
                
                # Initiative (Springboard like): Large spread, high volume, breakout
                if spread > (0.7 * total_range):
                    signals.append({'time': df['time'].iloc[i], 'type': 'Initiative', 'price': df['close'].iloc[i]})
                
                # Absorption: Large volume, tiny spread, near recent extremes (stalling)
                elif spread < (0.2 * total_range):
                    signals.append({'time': df['time'].iloc[i], 'type': 'Absorption', 'price': df['close'].iloc[i]})
                    
        return pd.DataFrame(signals)

    @staticmethod
    def calculate_forex_stats(df):
        """
        Calculates comprehensive statistical indicators migrated from forex.py.
        Includes volume trends, rolling extremes, and impulse strength.
        """
        if df.empty: return df
        df = df.copy()
        
        # 1. Volume Trends (Up vs Down Volume EMA)
        df['body_dir'] = np.where(df['close'] >= df['open'], 'up', 'down')
        for span in [4, 7, 15, 30]:
            upvol = df['tick_volume'].where(df['body_dir'] == 'up')
            dnvol = df['tick_volume'].where(df['body_dir'] == 'down')
            df[f'upvm{span}'] = upvol.ewm(span=span, adjust=False).mean().ffill()
            df[f'dnvm{span}'] = dnvol.ewm(span=span, adjust=False).mean().ffill()
            df[f'vol_trend{span}'] = df[f'upvm{span}'] - df[f'dnvm{span}']
            
        # 2. Rolling Extremes (Windows: 10, 20, 30, 60, 120, 180)
        for w in [10, 20, 30, 60, 120, 180]:
            df[f'rv{w}'] = df['tick_volume'].rolling(window=w).max().shift()
            df[f'rh{w}'] = df['high'].rolling(window=w).max().shift()
            df[f'rl{w}'] = df['low'].rolling(window=w).min().shift()
            
            # Boolean Flags
            df[f'vol_high_{w}'] = df['tick_volume'] > df[f'rv{w}']
            df[f'high_break_{w}'] = df['high'] > df[f'rh{w}']
            df[f'low_break_{w}'] = df['low'] < df[f'rl{w}']

        # 3. Impulse & Strength (EMA of H-L range for Up/Dn moves)
        for span in [5, 10, 15]:
            # Simple impulse: diff of EMA between up and down candles
            hl_range = (df['high'] - df['low']) * 10000 # scaling factor
            uhl = hl_range.where(df['close'] > df['close'].shift(5)).ewm(span=span, adjust=False).mean().bfill()
            dhl = hl_range.where(df['close'] < df['close'].shift(5)).ewm(span=span, adjust=False).mean().bfill()
            df[f'imp{span}'] = uhl - dhl

        return df

    @staticmethod
    def detect_forex_scenarios(df):
        """
        Implements Wyckoff-style Scenarios from forex.py.
        Detects 'up_test' and 'down_test' continuation signals.
        """
        if df.empty or len(df) < 5: return pd.DataFrame()
        
        signals = []
        for i in range(2, len(df)):
            # Up Test: Volume increase on upbar after two downbars with shrinking volume
            # Simplified version of forex.py logic
            uptest = (df['tick_volume'].iloc[i] > df['tick_volume'].iloc[i-1]) and \
                     (df['close'].iloc[i] > df['open'].iloc[i]) and \
                     (df['tick_volume'].iloc[i-1] < df['tick_volume'].iloc[i-2]) and \
                     (df['close'].iloc[i-1] < df['open'].iloc[i-1]) and \
                     (df['close'].iloc[i-2] < df['open'].iloc[i-2])
            
            if uptest:
                signals.append({'time': df['time'].iloc[i], 'type': 'Up Test (Wzrosty)', 'price': df['low'].iloc[i]})
                
            # Down Test: Volume increase on downbar after two upbars with shrinking volume
            downtest = (df['tick_volume'].iloc[i] > df['tick_volume'].iloc[i-1]) and \
                       (df['close'].iloc[i] < df['open'].iloc[i]) and \
                       (df['close'].iloc[i-1] > df['open'].iloc[i-1]) and \
                       (df['close'].iloc[i-2] > df['open'].iloc[i-2]) and \
                       (df['tick_volume'].iloc[i-1] < df['tick_volume'].iloc[i-2])
                       
            if downtest:
                signals.append({'time': df['time'].iloc[i], 'type': 'Down Test (Spadki)', 'price': df['high'].iloc[i]})
                
        return pd.DataFrame(signals)

    @staticmethod
    def detect_smt_divergence(df1, df2, length=5):
        merged = pd.merge(df1, df2, on='time', suffixes=('_1', '_2'), how='inner')
        window = 2 * length + 1
        
        merged['ph1'] = merged['high_1'].rolling(window=window, center=True).max() == merged['high_1']
        merged['pl1'] = merged['low_1'].rolling(window=window, center=True).min() == merged['low_1']
        merged['ph2'] = merged['high_2'].rolling(window=window, center=True).max() == merged['high_2']
        merged['pl2'] = merged['low_2'].rolling(window=window, center=True).min() == merged['low_2']
        
        smt_signals = []
        pivots_high = merged[merged['ph1'] & merged['ph2']].copy()
        pivots_low = merged[merged['pl1'] & merged['pl2']].copy()
        
        if not pivots_high.empty:
            pivots_high['prev_high_1'] = pivots_high['high_1'].shift(1)
            pivots_high['prev_high_2'] = pivots_high['high_2'].shift(1)
            for _, row in pivots_high.iterrows():
                if pd.isna(row['prev_high_1']): continue
                h1_c, h1_p = row['high_1'], row['prev_high_1']
                h2_c, h2_p = row['high_2'], row['prev_high_2']
                if (h1_c > h1_p and h2_c < h2_p) or (h1_c < h1_p and h2_c > h2_p):
                    smt_signals.append({'time': row['time'], 'type': 'Bearish SMT', 'price_1': h1_c})

        if not pivots_low.empty:
            pivots_low['prev_low_1'] = pivots_low['low_1'].shift(1)
            pivots_low['prev_low_2'] = pivots_low['low_2'].shift(1)
            for _, row in pivots_low.iterrows():
                if pd.isna(row['prev_low_1']): continue
                l1_c, l1_p = row['low_1'], row['prev_low_1']
                l2_c, l2_p = row['low_2'], row['prev_low_2']
                if (l1_c < l1_p and l2_c > l2_p) or (l1_c > l1_p and l2_c < l2_p):
                    smt_signals.append({'time': row['time'], 'type': 'Bullish SMT', 'price_1': l1_c})
                    
        return pd.DataFrame(smt_signals), merged
    @staticmethod
    def detect_multi_extremes(swings_df, tolerance=0.015):
        """
        Detects Double/Triple Tops and Bottoms from swing data.
        Tolerance: % relative price difference between peaks/valleys.
        """
        if len(swings_df) < 5: return pd.DataFrame()
        
        highs = swings_df[swings_df['direction'] == 'Up'].copy()
        lows = swings_df[swings_df['direction'] == 'Down'].copy()
        signals = []
        
        # Double/Triple Tops
        for i in range(2, len(highs)):
            prices = [highs.iloc[i]['end_price'], highs.iloc[i-1]['end_price'], highs.iloc[i-2]['end_price']]
            base_p = prices[0]
            
            # Triple Top
            if all(abs(p - base_p) / base_p < tolerance for p in prices):
                signals.append({'time': highs.iloc[i]['end_time'], 'type': 'Triple Top', 'price': base_p})
            # Double Top (only if triple failed)
            elif abs(prices[0] - prices[1]) / prices[1] < tolerance:
                signals.append({'time': highs.iloc[i]['end_time'], 'type': 'Double Top', 'price': base_p})

        # Double/Triple Bottoms
        for i in range(2, len(lows)):
            prices = [lows.iloc[i]['end_price'], lows.iloc[i-1]['end_price'], lows.iloc[i-2]['end_price']]
            base_p = prices[0]
            
            # Triple Bottom
            if all(abs(p - base_p) / base_p < tolerance for p in prices):
                signals.append({'time': lows.iloc[i]['end_time'], 'type': 'Triple Bottom', 'price': base_p})
            # Double Bottom
            elif abs(prices[0] - prices[1]) / prices[1] < tolerance:
                signals.append({'time': lows.iloc[i]['end_time'], 'type': 'Double Bottom', 'price': base_p})
                
        return pd.DataFrame(signals)

    @staticmethod
    def calculate_daily_stats(df):
        """
        Calculates daily % changes and volatility Z-scores.
        Helps identify overextended price moves.
        """
        if df.empty: return df
        df = df.copy()
        
        # Daily Return using 1440 mins if minute data, or just shift(1) if already D1
        # Here we assume minute data (midas.ipynb usually loads M1/M5)
        # 1440 mins = 1 day
        df['prev_day_close'] = df['close'].shift(1440).ffill()
        df['daily_pct_change'] = (df['close'] - df['prev_day_close']) / df['prev_day_close'] * 100
        
        # Z-score of changes (20-day window)
        window = 20 * 1440 
        avg = df['daily_pct_change'].rolling(window=window).mean()
        std = df['daily_pct_change'].rolling(window=window).std()
        df['daily_zscore'] = (df['daily_pct_change'] - avg) / std
        
        # Flag for overextension (> 2 SD)
        df['is_overextended'] = abs(df['daily_zscore']) > 2.0
        
        return df

    @staticmethod
    def calculate_exhaustion_score(df, swings_df, df_corr=None, config=None):
        """
        Calculates an Exhaustion Score (0-100) using an XGBoost classifier.
        Configurable features: 'volume', 'daily_stats', 'structural', 'impulse', 'smt'.
        """
        df = df.copy()
        df['exhaustion_score'] = 0.0 # Initialize to prevent KeyError in visualization

        # Default settings if none provided
        if config is None:
            config = {
                'volume': True,
                'daily_stats': True,
                'structural': True,
                'impulse': True,
                'smt': True
            }

        if df.empty or len(swings_df) < 50: 
            return df
        
        # 1. Conditionally Engineering Features
        active_features = []
        
        # Volume features
        if config.get('volume', True):
            if 'vol_trend30' not in df.columns: df = Analyzer.calculate_forex_stats(df)
            active_features.extend(['vol_trend7', 'vol_trend30', 'vol_high_60'])
            
        # Daily Stats
        if config.get('daily_stats', True):
            if 'daily_zscore' not in df.columns: df = Analyzer.calculate_daily_stats(df)
            active_features.append('daily_zscore')
            
        # Structural Breaks (Rolling High/Low)
        if config.get('structural', True):
            if 'high_break_180' not in df.columns: df = Analyzer.calculate_forex_stats(df)
            active_features.extend(['high_break_180', 'low_break_180'])
            
        # Momentum Impulse
        if config.get('impulse', True):
            if 'imp5' not in df.columns: df = Analyzer.calculate_forex_stats(df)
            active_features.extend(['imp5', 'imp15'])

        # SMT Feature
        df['smt_active'] = 0
        if config.get('smt', True) and df_corr is not None and not df_corr.empty:
            smt_signals, _ = Analyzer.detect_smt_divergence(df, df_corr)
            if not smt_signals.empty:
                for _, sig in smt_signals.iterrows():
                    time_diff = (df['time'] - pd.to_datetime(sig['time'])).dt.total_seconds() / 60
                    mask = (time_diff >= 0) & (time_diff < 30)
                    df.loc[mask, 'smt_active'] = 1
            active_features.append('smt_active')

        # Binary Targets for Reversal Points (LAGGED labeling to prevent lookahead)
        df['is_turning_point'] = 0
        for _, swing in swings_df.iterrows():
            # Find the index where the swing ended
            end_indices = df[df['time'] == swing['end_time']].index
            if not end_indices.empty:
                end_idx = end_indices[0]
                # Label the turn shifted by 5 bars (confirmation lag)
                # This ensures the model only learns from turns that would have been identifiable
                label_idx = min(len(df)-1, end_idx + 5)
                df.loc[label_idx, 'is_turning_point'] = 1
                
        # 2. Train and Predict with Selected Features
        data = df[active_features + ['is_turning_point']].dropna()
        if len(data) < 100 or not active_features: return df 
        
        X = data[active_features]
        y = data['is_turning_point']
        
        scale_pos = (len(y) - sum(y)) / sum(y) if sum(y) > 0 else 1
        clf = xgb.XGBClassifier(
            n_estimators=50,
            max_depth=4,
            learning_rate=0.1,
            scale_pos_weight=scale_pos,
            use_label_encoder=False,
            eval_metric='logloss'
        )
        clf.fit(X, y)
        
        X_all = df[active_features].fillna(0)
        probs = clf.predict_proba(X_all)[:, 1]
        probs_series = pd.Series(probs, index=df.index).rolling(window=5, min_periods=1).mean()
        df['exhaustion_score'] = (probs_series * 100).clip(0, 100)
        
        #Structural Pattern Boost (Multi-Extremes)
        if config.get('structural', True):
            multi = Analyzer.detect_multi_extremes(swings_df)
            if not multi.empty:
                for _, sig in multi.iterrows():
                    time_diff = (df['time'] - pd.to_datetime(sig['time'])).dt.total_seconds() / 60
                    mask = (time_diff >= 0) & (time_diff < 120)
                    df.loc[mask, 'exhaustion_score'] += 20 * np.exp(-time_diff[mask] / 30)
        
        df['exhaustion_score'] = df['exhaustion_score'].clip(0, 100)
        return df
    @staticmethod
    def plot_smt_divergence(df1, df2, symbol1='Asset 1', symbol2='Asset 2', limit=500):
        """
        Creates a dual-axis interactive chart to visualize SMT Divergences.
        """
        if df1.empty or df2.empty: return None
        
        # Merge and limit
        merged = pd.merge(df1, df2, on='time', suffixes=('_1', '_2'), how='inner')
        merged = merged.iloc[-limit:]
        
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Asset 1
        fig.add_trace(
            go.Scatter(x=merged['time'], y=merged['close_1'], name=symbol1, line=dict(color='orange')),
            secondary_y=False,
        )
        
        # Asset 2
        fig.add_trace(
            go.Scatter(x=merged['time'], y=merged['close_2'], name=symbol2, line=dict(color='cyan')),
            secondary_y=True,
        )
        
        # Detect SMT Divergences specifically for this view
        smt_signals, _ = Analyzer.detect_smt_divergence(df1, df2)
        if not smt_signals.empty:
            vis_smt = smt_signals[smt_signals['time'] >= merged['time'].iloc[0]]
            if not vis_smt.empty:
                # We plot them on Asset 1's axis
                fig.add_trace(
                    go.Scatter(x=vis_smt['time'], y=vis_smt['price_1'], mode='markers',
                               marker=dict(color='white', size=15, symbol='star-diamond', line=dict(width=2, color='red')),
                               name='SMT Divergence'),
                    secondary_y=False
                )
        
        fig.update_layout(
            title=f'SMT Divergence Analysis: {symbol1} vs {symbol2}',
            template='plotly_dark',
            xaxis_title='Time',
            height=600
        )
        
        fig.update_yaxes(title_text=f"Price {symbol1}", secondary_y=False)
        fig.update_yaxes(title_text=f"Price {symbol2}", secondary_y=True)
        
        return fig
