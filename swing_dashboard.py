import pandas as pd
import MetaTrader5 as mt5
import numpy as np
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from datetime import datetime
import pytz
from swing_analytics import SwingAnalytics, SWING_TYPE, TREND_STATE, SwingMeasurement, PullbackMetrics
from typing import List

class SwingDashboard:
    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe
        self.console = Console()

    def render_all_tables(self, swings: List[SwingMeasurement], pullbacks: List[PullbackMetrics]):
        self.console.print(Panel(f"[bold white]SWING STRUCTURE ANALYSIS - {self.symbol} {self.timeframe}[/bold white]", box=box.DOUBLE))
        
        self.render_table_1(swings)
        self.render_table_2(pullbacks, swings)
        self.render_table_3(swings)
        self.render_table_4(swings)
        self.render_table_5(swings)

    def render_table_1(self, swings: List[SwingMeasurement]):
        table = Table(title="TABLE 1: SWING STRUCTURE OVERVIEW", box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("ID", justify="center", style="dim")
        table.add_column("Start", justify="center")
        table.add_column("Type")
        table.add_column("Trend #")
        table.add_column("Bars", justify="right")
        table.add_column("Pips", justify="right")
        table.add_column("Volume", justify="right")
        table.add_column("Comparison")
        table.add_column("HH/HL")

        for s in swings[-15:]: 
            hh_hl = ""
            if "UP" in s.swing_type.value:
                hh_hl = f"{'✓' if s.makes_higher_high else '✗'}{'✓' if s.makes_higher_low else '✗'}"
            elif "DN" in s.swing_type.value:
                hh_hl = f"{'✓' if s.makes_lower_low else '✗'}{'✓' if s.makes_lower_high else '✗'}"
            
            trend_num = str(s.position_in_trend) if s.position_in_trend > 0 else "-"
            
            # Comparison vs same type previous
            comp = "-"
            for ps in reversed(swings[:swings.index(s)]):
                if ps.swing_type == s.swing_type:
                    v_diff = (s.swing_volume_total / ps.swing_volume_total - 1) * 100 if ps.swing_volume_total > 0 else 0
                    comp = f"{v_diff:+.1f}% Vol"
                    break

            color = "green" if "UP" in s.swing_type.value else "red" if "DN" in s.swing_type.value else "yellow"
            table.add_row(
                f"#{s.swing_id}",
                s.swing_start_time.strftime("%H:%M"),
                f"[{color}]{s.swing_type.value}[/{color}]",
                trend_num,
                str(s.swing_length_bars),
                f"{s.swing_length_pips:.1f}",
                f"{s.swing_volume_total:,}",
                comp,
                hh_hl
            )

        self.console.print(table)
        last_s = swings[-1] if swings else None
        trend_color = "green" if last_s and last_s.current_trend == TREND_STATE.BULLISH else "red" if last_s and last_s.current_trend == TREND_STATE.BEARISH else "white"
        self.console.print(f"[{trend_color}]Current Trend: {last_s.current_trend.value if last_s else 'N/A'}[/{trend_color}]", justify="right")

    def render_table_2(self, pullbacks: List[PullbackMetrics], swings: List[SwingMeasurement]):
        table = Table(title="TABLE 2: PULLBACK ANALYSIS", box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("PB #")
        table.add_column("Foll. Swing Start")
        table.add_column("PB Bars")
        table.add_column("PB Pips")
        table.add_column("Depth %")
        table.add_column("Bars %")
        table.add_column("Fib/Status")

        # Map swing_id to start_time for quick lookup
        swing_times = {s.swing_id: s.swing_start_time.strftime("%H:%M") for s in swings}

        for pb in pullbacks[-10:]:
            color = "green" if pb.status_indicator == "✓" else "yellow" if pb.status_indicator == "⚠" else "red"
            foll_time = swing_times.get(pb.following_swing_id, "N/A")
            table.add_row(
                str(pb.pb_id),
                foll_time,
                str(pb.pullback_bars),
                f"{pb.pullback_pips:.1f}",
                f"{pb.pullback_percent:.1f}%",
                f"{pb.bars_vs_swing_percent:.1f}%",
                f"[{color}]{pb.fib_level_exceeded} {pb.status_indicator}[/{color}]"
            )

        self.console.print(table)

    def render_table_3(self, swings: List[SwingMeasurement]):
        table = Table(title="TABLE 3: SWING PROGRESSION METRICS", box=box.ROUNDED, show_header=True, header_style="bold blue")
        table.add_column("ID", justify="center", style="dim")
        table.add_column("Start")
        table.add_column("Type")
        table.add_column("Length Δ")
        table.add_column("Pips Δ")
        table.add_column("Volume Δ")
        table.add_column("Speed Δ")
        table.add_column("Health")

        main_swings = [s for s in swings if s.swing_type in [SWING_TYPE.UPSWING, SWING_TYPE.DOWNSWING]]
        for i in range(1, len(main_swings)):
            s, prev = main_swings[i], main_swings[i-1]
            l_delta = s.swing_length_bars - prev.swing_length_bars
            p_delta = abs(s.swing_length_pips) - abs(prev.swing_length_pips)
            v_delta = int(s.swing_volume_total) - int(prev.swing_volume_total)
            s_delta = s.pips_per_bar - prev.pips_per_bar
            
            health = "🟢 STR" if p_delta > 0 and v_delta > 0 else "🟡 WEA" if p_delta < 0 or v_delta < 0 else "🔴 EXH"
            
            table.add_row(
                f"#{s.swing_id}",
                s.swing_start_time.strftime("%H:%M"), s.swing_type.value,
                f"{l_delta:+d}", f"{p_delta:+.1f}", f"{v_delta:+,.0f}",
                f"{s_delta:+.2f}", health
            )
        self.console.print(table)

    def render_table_4(self, swings: List[SwingMeasurement]):
        table = Table(title="TABLE 4: VOLUME DISTRIBUTION", box=box.ROUNDED, show_header=True, header_style="bold yellow")
        table.add_column("ID", justify="center", style="dim")
        table.add_column("Start")
        table.add_column("Type")
        table.add_column("Total Vol")
        table.add_column("Avg/Bar")
        table.add_column("Pattern")

        for s in swings[-10:]:
            pattern = "NORM"
            if s.volume_per_bar > s.swing_volume_avg * 1.5: pattern = "CLIM"
            elif s.volume_per_bar < s.swing_volume_avg * 0.5: pattern = "EXHA"
            
            table.add_row(f"#{s.swing_id}", s.swing_start_time.strftime("%H:%M"), s.swing_type.value, f"{s.swing_volume_total:,}", f"{s.swing_volume_avg:,.0f}", pattern)
        self.console.print(table)

    def render_table_5(self, swings: List[SwingMeasurement]):
        table = Table(title="TABLE 5: TIME DURATION ANALYSIS", box=box.ROUNDED, show_header=True, header_style="bold green")
        table.add_column("ID", justify="center", style="dim")
        table.add_column("Start")
        table.add_column("Type")
        table.add_column("Duration (min)")
        table.add_column("Min/Pip")
        table.add_column("Rating")

        for s in swings[-10:]:
            mpp = s.swing_duration_minutes / abs(s.swing_length_pips) if s.swing_length_pips != 0 else 0
            rating = "FAST" if mpp < 1.3 else "MODERATE" if mpp < 2.0 else "SLOW"
            table.add_row(f"#{s.swing_id}", s.swing_start_time.strftime("%H:%M"), s.swing_type.value, str(s.swing_duration_minutes), f"{mpp:.2f}", rating)
        self.console.print(table)

if __name__ == "__main__":
    symbol = "XAUUSD"
    if not mt5.initialize():
        print("MT5 initialize failed"); quit()
        
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 5000)
    # Get proper point value for Gold
    sym_info = mt5.symbol_info(symbol)
    point = sym_info.point if sym_info else 0.01
    mt5.shutdown()
    
    if rates is None:
        print(f"Failed to get rates for {symbol}"); quit()
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    analytics = SwingAnalytics(point_value=point)
    zigzag = analytics.calculate_zigzag(df)
    swings = analytics.process_swings(df, zigzag)
    pullbacks = analytics.analyze_pullbacks(swings)
    
    dashboard = SwingDashboard(symbol, "M1")
    dashboard.render_all_tables(swings, pullbacks)
