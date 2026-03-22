import pandas as pd
import numpy as np
from swing_analytics import SwingAnalytics, SWING_TYPE, TREND_STATE

def test_logic():
    # Synthetic data for Bullish Market
    # P1: 100, P2: 150, P3: 120, P4: 170
    # Swing 1: 100-150 (UP)
    # Swing 2: 150-120 (PB-DOWN/DN)
    # Swing 3: 120-170 (UP)
    
    data = {
        'time': pd.to_datetime(['2023-01-01 00:00', '2023-01-01 00:01', '2023-01-01 00:02', '2023-01-01 00:03']),
        'high': [100, 150, 120, 170],
        'low': [100, 150, 120, 170],
        'open': [100, 150, 120, 170],
        'close': [100, 150, 120, 170],
        'tick_volume': [100, 100, 100, 100]
    }
    df = pd.DataFrame(data)
    zigzag = np.zeros(len(df))
    zigzag[0] = 100
    zigzag[1] = 150
    zigzag[2] = 120
    zigzag[3] = 170
    
    analytics = SwingAnalytics(point_value=1.0)
    swings = analytics.process_swings(df, zigzag)
    
    for s in swings:
        print(f"Swing {s.swing_id}: {s.swing_type.value}, Pips: {s.swing_length_pips}, HH:{s.makes_higher_high}, HL:{s.makes_higher_low}")
        
    # Expectations:
    # Swing 1: UP (HH/HL checked vs prev?) len is 1, so no prev_same
    # Swing 2: DN or PB? 150 -> 120. Prev same (DOWN) doesn't exist.
    # Swing 3: UP. Compares with Swing 1. 170 > 150 (HH), 120 > 100 (HL). HH=T, HL=T. Type=UPSWING.
    
    # Let's add more: P5: 140 (Higher Low)
    zigzag_long = np.zeros(6)
    zigzag_long[0] = 100
    zigzag_long[1] = 150
    zigzag_long[2] = 120
    zigzag_long[3] = 170
    zigzag_long[4] = 140
    zigzag_long[5] = 200
    
    df_long = pd.DataFrame({
        'time': pd.to_datetime([f"2023-01-01 00:0{i}" for i in range(6)]),
        'high': [100, 150, 120, 170, 140, 200],
        'low': [100, 150, 120, 170, 140, 200],
        'open': [100, 150, 120, 170, 140, 200],
        'close': [100, 150, 120, 170, 140, 200],
        'tick_volume': [100]*6
    })
    
    print("\nLong Sequence:")
    swings_long = analytics.process_swings(df_long, zigzag_long)
    for s in swings_long:
        print(f"Swing {s.swing_id}: {s.swing_type.value}, Range: {s.start_price}-{s.end_price}, HH:{s.makes_higher_high}, HL:{s.makes_higher_low}")

if __name__ == "__main__":
    test_logic()
