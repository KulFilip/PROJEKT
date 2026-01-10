
# analysis.py
import numpy as np
import pandas as pd
from scipy.spatial import distance
import config

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
    def backtest_nn(swings_df, k=5, min_history=10):
        if len(swings_df) < min_history + 1:
            return pd.DataFrame()
            
        predictions = []
        # Walk forward backtest
        for i in range(min_history, len(swings_df)):
            current_history = swings_df.iloc[:i]
            # Try to predict the next swing (which is swings_df.iloc[i])
            pred = Analyzer.predict_next_swing_nn(current_history, k=k)
            
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
