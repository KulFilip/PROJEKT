
import pandas as pd
import numpy as np
import datetime
from analysis_v2 import Analyzer, ForexFeatures

def verify_optimizations():
    print("Verifying Optimized Analysis V2...")
    
    # 1. Create dummy data - generate more swings
    data = []
    start_time = datetime.datetime.now()
    for i in range(1000):
        # Create oscillations
        price = 1.1000 + np.sin(i * 0.5) * 0.0050
        data.append({
            'time': start_time + datetime.timedelta(minutes=i),
            'open': price - 0.0001,
            'high': price + 0.0005,
            'low': price - 0.0005,
            'close': price,
            'tick_volume': 100 + (i % 10) * 10
        })
    df = pd.DataFrame(data)
    
    # 2. Run initial analysis
    print("  -> Calculating ZigZag...")
    # Use smaller depth to get more swings
    df['zigzag'] = Analyzer.calculate_zigzag(df, depth=5)
    
    print("  -> Analyzing Swings...")
    swings_df = Analyzer.analyze_swings(df)
    
    print("  -> Calculating Forex Features...")
    df = ForexFeatures.calculate_all(df)
    
    # 3. Test prepare_ml_features
    print("  -> Testing prepare_ml_features (Log-Transforms)...")
    X, y, latest_X = Analyzer.prepare_ml_features(swings_df, df, window=5)
    
    if X is not None:
        print(f"     X shape: {X.shape}")
        print(f"     y shape: {y.shape}")
        # Verify y contains log values (should be small for small ranges)
        print(f"     Sample target [log(range), log(dur)]: {y[0, :2]}")
    else:
        print("     ❌ X is None (insufficient data?)")
        
    # 4. Test predictions
    print("  -> Testing XGBoost Prediction...")
    pred = Analyzer.predict_next_swing_xgboost(swings_df, df, window=5)
    if pred:
        print(f"     Success: Predicted Range: {pred['predicted_range']:.5f}, Duration: {pred['predicted_duration']:.2f}")
    else:
        print("     ❌ XGBoost Prediction failed (insufficient data?)")

    print("\n✅ Verification complete.")

if __name__ == "__main__":
    verify_optimizations()
