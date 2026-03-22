import pandas as pd
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict

class SWING_TYPE(Enum):
    UPSWING = "UP"
    DOWNSWING = "DN"
    PULLBACK_UP = "PB↑"  # Retracement in downtrend
    PULLBACK_DOWN = "PB↓" # Retracement in uptrend

class TREND_STATE(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NO_TREND = "NO_TREND"

@dataclass
class SwingMeasurement:
    swing_id: int
    swing_type: SWING_TYPE
    swing_length_bars: int
    swing_length_pips: float
    swing_volume_total: int
    swing_volume_avg: float
    swing_start_time: datetime
    swing_end_time: datetime
    swing_duration_minutes: int
    pips_per_bar: float
    volume_per_bar: float
    position_in_trend: int
    current_trend: TREND_STATE
    
    # Relationships
    makes_higher_high: bool = False
    makes_higher_low: bool = False
    makes_lower_high: bool = False
    makes_lower_low: bool = False
    
    # Values for comparisons
    high_price: float = 0.0
    low_price: float = 0.0
    start_price: float = 0.0
    end_price: float = 0.0

@dataclass
class PullbackMetrics:
    pb_id: int
    following_swing_id: int
    pullback_bars: int
    pullback_pips: float
    pullback_percent: float
    bars_vs_swing_percent: float
    fib_level_exceeded: str
    status_indicator: str  # ✓, ⚠, ✗

class SwingAnalytics:
    def __init__(self, point_value: float = 0.00001):
        self.point_value = point_value

    def calculate_zigzag(self, df: pd.DataFrame, depth: int = 12, deviation: int = 5, backstep: int = 3) -> np.ndarray:
        """Standard ZigZag algorithm implementation."""
        n = len(df)
        high = df['high'].values
        low = df['low'].values
        
        zigzag_buffer = np.zeros(n)
        high_buffer = np.zeros(n)
        low_buffer = np.zeros(n)
        
        for i in range(depth, n):
            window_low = low[i-depth+1 : i+1]
            minimum = np.min(window_low)
            if low[i] == minimum:
                low_buffer[i] = low[i]
                if i > backstep:
                    for b in range(i - 1, i - backstep, -1):
                        if b < 0: break
                        if low_buffer[b] != 0 and low_buffer[b] > low[i]:
                            low_buffer[b] = 0.0
            
            window_high = high[i-depth+1 : i+1]
            maximum = np.max(window_high)
            if high[i] == maximum:
                high_buffer[i] = high[i]
                if i > backstep:
                    for b in range(i - 1, i - backstep, -1):
                        if b < 0: break
                        if high_buffer[b] != 0 and high_buffer[b] < high[i]:
                            high_buffer[b] = 0.0
        
        whatlookfor, last_val, last_pos = 0, 0.0, 0
        for i in range(depth, n):
            if high_buffer[i] != 0:
                last_val, last_pos, whatlookfor = high_buffer[i], i, -1
                zigzag_buffer[i] = last_val
                break
            if low_buffer[i] != 0:
                last_val, last_pos, whatlookfor = low_buffer[i], i, 1
                zigzag_buffer[i] = last_val
                break
        
        if last_pos == 0: return zigzag_buffer

        for i in range(last_pos + 1, n):
            if whatlookfor == 1: # Looking for Low
                if high_buffer[i] != 0.0:
                    if (high_buffer[i] - last_val) >= (deviation * self.point_value):
                        zigzag_buffer[i], last_val, last_pos, whatlookfor = high_buffer[i], high_buffer[i], i, -1
                    else: high_buffer[i] = 0.0
                if low_buffer[i] != 0.0 and low_buffer[i] < last_val:
                    zigzag_buffer[last_pos], zigzag_buffer[i], last_val, last_pos = 0.0, low_buffer[i], low_buffer[i], i
            elif whatlookfor == -1: # Looking for High
                if low_buffer[i] != 0.0:
                    if (last_val - low_buffer[i]) >= (deviation * self.point_value):
                        zigzag_buffer[i], last_val, last_pos, whatlookfor = low_buffer[i], low_buffer[i], i, 1
                    else: low_buffer[i] = 0.0
                if high_buffer[i] != 0.0 and high_buffer[i] > last_val:
                    zigzag_buffer[last_pos], zigzag_buffer[i], last_val, last_pos = 0.0, high_buffer[i], high_buffer[i], i
        
        return zigzag_buffer

    def process_swings(self, df: pd.DataFrame, zigzag_buffer: np.ndarray) -> List[SwingMeasurement]:
        df['zigzag'] = zigzag_buffer
        pivot_indices = df[df['zigzag'] > 0].index.tolist()
        
        swings = []
        current_trend = TREND_STATE.NO_TREND
        trend_counter = 0
        
        for i in range(1, len(pivot_indices)):
            start_idx, end_idx = pivot_indices[i-1], pivot_indices[i]
            start_price, end_price = df.loc[start_idx, 'zigzag'], df.loc[end_idx, 'zigzag']
            direction = SWING_TYPE.UPSWING if end_price > start_price else SWING_TYPE.DOWNSWING
            
            bars = end_idx - start_idx
            pips = abs(end_price - start_price) / self.point_value
            # NON-OVERLAPPING VOLUME SUM: Start from pivot+1 to next pivot (inclusive)
            # This ensures each bar is counted once. The first bar of the very first swing 
            # is pivot_indices[0], we'll include it in the sum for the first swing.
            if i == 1:
                total_vol = int(df.loc[start_idx:end_idx, 'tick_volume'].sum())
            else:
                total_vol = int(df.loc[start_idx+1:end_idx, 'tick_volume'].sum())
            
            avg_vol = total_vol / bars if bars > 0 else 0
            
            start_time, end_time = df.loc[start_idx, 'time'], df.loc[end_idx, 'time']
            duration = int((end_time - start_time).total_seconds() / 60)
            
            # Identify HL/HH/LL/LH vs previous of SAME direction
            hh, hl, lh, ll = False, False, False, False
            if len(swings) >= 2:
                prev_same = swings[-2]
                if direction == SWING_TYPE.UPSWING:
                    hh = end_price > prev_same.end_price
                    hl = start_price > prev_same.start_price
                else:
                    ll = end_price < prev_same.end_price
                    lh = start_price < prev_same.start_price
            
            # Classification Logic
            # UP: Trend-aligned move in Bullish trend OR Change to Bullish (HH+HL)
            # DN: Trend-aligned move in Bearish trend OR Change to Bearish (LL+LH)
            # PB: Counter-trend move or failed trend continuation
            
            final_type = direction
            if direction == SWING_TYPE.UPSWING:
                if hh and hl:
                    final_type = SWING_TYPE.UPSWING
                    if current_trend != TREND_STATE.BULLISH:
                        current_trend, trend_counter = TREND_STATE.BULLISH, 1
                    else: trend_counter += 1
                elif current_trend == TREND_STATE.BEARISH:
                    final_type = SWING_TYPE.PULLBACK_UP
                    trend_counter = 0 # Pullbacks don't increment trend counter
                else:
                    final_type = SWING_TYPE.PULLBACK_UP
            else: # direction == DOWNSWING
                if ll and lh:
                    final_type = SWING_TYPE.DOWNSWING
                    if current_trend != TREND_STATE.BEARISH:
                        current_trend, trend_counter = TREND_STATE.BEARISH, 1
                    else: trend_counter += 1
                elif current_trend == TREND_STATE.BULLISH:
                    final_type = SWING_TYPE.PULLBACK_DOWN
                    trend_counter = 0
                else:
                    final_type = SWING_TYPE.PULLBACK_DOWN
            
            swings.append(SwingMeasurement(
                swing_id=i, swing_type=final_type, swing_length_bars=bars,
                swing_length_pips=pips if direction == SWING_TYPE.UPSWING else -pips,
                swing_volume_total=total_vol, swing_volume_avg=avg_vol,
                swing_start_time=start_time, swing_end_time=end_time,
                swing_duration_minutes=duration, pips_per_bar=pips/bars if bars>0 else 0,
                volume_per_bar=avg_vol, 
                position_in_trend=trend_counter,
                current_trend=current_trend, makes_higher_high=hh, makes_higher_low=hl,
                makes_lower_high=lh, makes_lower_low=ll,
                high_price=max(start_price, end_price), low_price=min(start_price, end_price),
                start_price=start_price, end_price=end_price
            ))
        return swings

    def analyze_pullbacks(self, swings: List[SwingMeasurement]) -> List[PullbackMetrics]:
        pullbacks = []
        pb_count = 1
        for i in range(1, len(swings)):
            curr, prev = swings[i], swings[i-1]
            if "PB" in curr.swing_type.value:
                pb_pips = abs(curr.swing_length_pips)
                prev_pips = abs(prev.swing_length_pips)
                pb_pct = (pb_pips / prev_pips * 100.0) if prev_pips > 0 else 0
                bars_pct = (curr.swing_length_bars / prev.swing_length_bars * 100.0) if prev.swing_length_bars > 0 else 0
                
                fib = "< 50%"
                status = "✓"
                if pb_pct > 61.8: fib, status = "> 61.8%", "✗"
                elif pb_pct > 50.0: fib, status = "= 50%", "⚠"
                
                pullbacks.append(PullbackMetrics(
                    pb_id=pb_count, following_swing_id=prev.position_in_trend,
                    pullback_bars=curr.swing_length_bars, pullback_pips=-pb_pips,
                    pullback_percent=pb_pct, bars_vs_swing_percent=bars_pct,
                    fib_level_exceeded=fib, status_indicator=status
                ))
                pb_count += 1
        return pullbacks

    def plot_swings(self, df: pd.DataFrame, swings: List[SwingMeasurement], prediction: Optional[Dict] = None, title: str = "Swing Analytics Dashboard"):
        """Generates an enhanced Plotly visualization with color-coded swings and predictions."""
        import plotly.graph_objects as go
        fig = go.Figure()
        
        # 1. Price Candles
        fig.add_trace(go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Price', opacity=0.4))
        
        # 2. Main Swing Lines
        zx, zy = [], []
        if swings:
            zx.append(swings[0].swing_start_time); zy.append(swings[0].start_price)
            for s in swings:
                zx.append(s.swing_end_time); zy.append(s.end_price)
        fig.add_trace(go.Scatter(x=zx, y=zy, mode='lines+markers', name='Swings', line=dict(color='yellow', width=2), marker=dict(size=6, color='yellow')))
        
        # 3. Annotations (Stickers) with High Opacity and Color Coding
        for s in swings:
            text = f"#{s.swing_id}<br>V:{s.swing_volume_total:,}<br>L:{s.swing_length_bars}b<br>T:{s.swing_duration_minutes}m"
            
            # Color Mapping: Green (UP), Red (DN), Grey (PB)
            if "PB" in s.swing_type.value:
                bg_color = "gray"
            elif "UP" in s.swing_type.value:
                bg_color = "green"
            else:
                bg_color = "red"
                
            fig.add_annotation(
                x=s.swing_end_time, y=s.end_price, text=text, 
                showarrow=True, arrowhead=1, 
                bgcolor=bg_color, opacity=0.95, 
                font=dict(color="white", size=10),
                bordercolor="white", borderwidth=1
            )
        
        # 4. Prediction Visualization
        if prediction and swings:
            last_swing = swings[-1]
            p_time = prediction.get('target_time')
            p_price = prediction.get('target_price')
            p_dir = prediction.get('direction', 'Unknown')
            
            if p_time and p_price:
                # Prediction line
                fig.add_trace(go.Scatter(
                    x=[last_swing.swing_end_time, p_time], 
                    y=[last_swing.end_price, p_price],
                    mode='lines+markers',
                    name=f'PROGNOZA ({p_dir})',
                    line=dict(color='cyan', width=3, dash='dash'),
                    marker=dict(size=10, symbol='star', color='cyan')
                ))
                
                # Prediction label
                fig.add_annotation(
                    x=p_time, y=p_price, 
                    text=f"CEL: {p_price:.2f}<br>({p_dir})",
                    showarrow=False, yshift=20,
                    bgcolor="cyan", font=dict(color="black", bold=True),
                    opacity=1.0
                )
        
        fig.update_layout(title=title, xaxis_rangeslider_visible=False, template="plotly_dark", height=850, showlegend=True)
        return fig
