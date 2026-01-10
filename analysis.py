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
        Generic backtest for different models (NN, XGBoost, LSTM).
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
        Programmatically scores the performance of the model using backtest results.
        Calculates MAPE (Mean Absolute Percentage Error) for Price, Range, and Duration.
        """
        if backtest_results.empty:
            return {}

        results = {}
        
        # Helper for MAPE
        def calculate_mape(actual, predicted):
            mask = actual != 0
            if not any(mask): return 1.0 # 100% error if all actuals are 0
            return (abs(actual[mask] - predicted[mask]) / abs(actual[mask])).mean()

        # 1. Price Accuracy
        results['price_mape'] = calculate_mape(backtest_results['actual_end_price'], backtest_results['target_price'])
        
        # 2. Range Accuracy
        results['range_mape'] = calculate_mape(backtest_results['actual_range'], backtest_results['predicted_range'])
        
        # 3. Duration Accuracy
        results['duration_mape'] = calculate_mape(backtest_results['actual_duration'], backtest_results['predicted_duration'])
        
        # 4. Success Direction Rate
        total = len(backtest_results)
        correct_dir = (backtest_results['direction'] == backtest_results['actual_direction']).sum()
        results['direction_accuracy'] = correct_dir / total if total > 0 else 0
        
        return results

    @staticmethod
    def prepare_ml_features(swings_df, window=10):
        """
        Prepares a feature matrix (X) and targets (y) for ML models.
        Features include lags of range, duration, volume, and intensity.
        """
        if len(swings_df) < window + 1:
            return None, None

        features = []
        targets = []
        
        # We look at 'window' previous swings (of alternating directions)
        for i in range(window, len(swings_df)):
            subset = swings_df.iloc[i-window:i]
            target = swings_df.iloc[i]
            
            # Feature vector: range, duration, volume, intensity for each swing in window
            # Also include direction as a binary feature (1 for Up, 0 for Down)
            row = []
            for _, s in subset.iterrows():
                row.extend([
                    1 if s['direction'] == 'Up' else 0,
                    s['range'],
                    s['duration_mins'],
                    s['volume'],
                    s['intensity']
                ])
            
            features.append(row)
            # Targets: range and duration_mins (we'll predict these)
            targets.append([target['range'], target['duration_mins']])
            
        return np.array(features), np.array(targets)

    @staticmethod
    def predict_next_swing_xgboost(swings_df, window=10):
        """
        Predicts next swing using XGBoost.
        """
        X, y = Analyzer.prepare_ml_features(swings_df, window=window)
        if X is None or len(X) < 20: # Need some training data
            return None

        # Features for the prediction (the latest window)
        latest_X = X[-1].reshape(1, -1)
        
        # Training a simple model on the fly (for demonstration, usually pre-trained is better)
        # We'll predict range first
        model_range = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
        model_range.fit(X[:-1], y[:-1, 0])
        pred_range = model_range.predict(latest_X)[0]
        
        # Predict duration
        model_dur = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
        model_dur.fit(X[:-1], y[:-1, 1])
        pred_dur = model_dur.predict(latest_X)[0]
        
        last_swing = swings_df.iloc[-1]
        next_dir = 'Down' if last_swing['direction'] == 'Up' else 'Up'
        
        target_price = last_swing['end_price'] + pred_range if next_dir == 'Up' else last_swing['end_price'] - pred_range
        target_time = pd.Timestamp(last_swing['end_time']) + pd.Timedelta(minutes=float(pred_dur))
        
        return {
            'direction': next_dir,
            'target_price': target_price,
            'target_time': target_time,
            'predicted_range': pred_range,
            'predicted_duration': pred_dur
        }

    @staticmethod
    def predict_next_swing_lstm(swings_df, window=10):
        """
        Predicts next swing using a simple LSTM model.
        """
        X, y = Analyzer.prepare_ml_features(swings_df, window=window)
        if X is None or len(X) < 30: # Need more data for LSTM
            return None

        # Reshape for LSTM: (samples, time_steps, features)
        # In our case, features per step is 5 (dir, range, dur, vol, intensity)
        # X is already flattened (window * 5), let's reshape it
        X_lstm = X.reshape(X.shape[0], window, 5)
        latest_X = X_lstm[-1].reshape(1, window, 5)
        
        # Build a small LSTM model
        model = Sequential([
            LSTM(32, input_shape=(window, 5), return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(2) # Output: range, duration
        ])
        
        model.compile(optimizer='adam', loss='mse')
        # Train briefly (usually would be pre-trained)
        model.fit(X_lstm[:-1], y[:-1], epochs=10, batch_size=8, verbose=0)
        
        preds = model.predict(latest_X, verbose=0)[0]
        pred_range = float(preds[0])
        pred_dur = float(preds[1])
        
        last_swing = swings_df.iloc[-1]
        next_dir = 'Down' if last_swing['direction'] == 'Up' else 'Up'
        
        target_price = last_swing['end_price'] + pred_range if next_dir == 'Up' else last_swing['end_price'] - pred_range
        target_time = pd.Timestamp(last_swing['end_time']) + pd.Timedelta(minutes=float(pred_dur))
        
        return {
            'direction': next_dir,
            'target_price': target_price,
            'target_time': target_time,
            'predicted_range': pred_range,
            'predicted_duration': pred_dur
        }

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
