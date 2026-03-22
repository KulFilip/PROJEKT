
import pandas as pd
import plotly.graph_objects as go
from database import DatabaseManager
from analysis import Analyzer
import config

def run_vis(symbol='XAGUSD'):
    db = DatabaseManager()
    df = db.load_candles(symbol, limit=2000)
    
    if df.empty:
        print(f"No data for {symbol}")
        return

    # Calculate ZigZag and Swings
    df['zigzag'] = Analyzer.calculate_zigzag(df)
    swings = Analyzer.analyze_swings(df)
    
    if swings.empty:
        print(f"No swings found for {symbol}")
        return

    # Run Backtest
    print(f"Running backtest for {symbol}...")
    backtest_results = Analyzer.backtest_nn(swings, k=5)
    
    if backtest_results.empty:
        print("Not enough data for backtesting.")
        return

    # Metrics
    avg_error = backtest_results['price_error'].mean()
    print(f"Average Price Error: {avg_error:.4f}")

    # Visualization
    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df['time'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name='Price',
        opacity=0.4
    ))

    # ZigZag (Blue Line)
    zz_pts = df[df['zigzag'] != 0]
    fig.add_trace(go.Scatter(
        x=zz_pts['time'], y=zz_pts['zigzag'],
        mode='lines+markers',
        line=dict(color='blue', width=2),
        name='Actual ZigZag'
    ))

    # Historical Predictions (Yellow Lines)
    # We plot each prediction as a line from its start point to its predicted target
    for _, res in backtest_results.iterrows():
        fig.add_trace(go.Scatter(
            x=[res['start_time'], res['target_time']],
            y=[res['start_price'], res['target_price']],
            mode='lines+markers',
            line=dict(color='yellow', width=1, dash='dot'),
            showlegend=False
        ))

    # Add a dummy entry for the legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color='yellow', width=2, dash='dot'),
        name='NN Predictions (Yellow)'
    ))

    fig.update_layout(
        title=f'NN Backtest: {symbol} (Avg Error: {avg_error:.4f})',
        template='plotly_dark',
        xaxis_rangeslider_visible=False
    )
    
    output_file = f"nn_backtest_{symbol}.html"
    fig.write_html(output_file)
    print(f"Visualization saved to {output_file}")

if __name__ == "__main__":
    import sys
    sym = sys.argv[1] if len(sys.argv) > 1 else 'XAGUSD'
    run_vis(sym)
