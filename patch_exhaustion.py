import json
import re

notebook_path = r'c:\\Users\\donniebrasco\\Documents\\PROJEKT\\midas.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])

        # 1. Update Section 3 (Predictions & Anomalies)
        if "forex_scenarios = Analyzer.detect_forex_scenarios(df)" in source:
            cell['source'] = [
                "# Model Selection for Live Prediction\n",
                "MODEL_TYPE = 'LSTM'  # Options: 'NN', 'XGBoost', 'LSTM'\n",
                "prediction = None\n",
                "if not swings.empty:\n",
                "    print(f\"Making live prediction using {MODEL_TYPE}...\")\n",
                "    if MODEL_TYPE == 'NN':\n",
                "        prediction = Analyzer.predict_next_swing_nn(swings, k=5)\n",
                "    elif MODEL_TYPE == 'XGBoost':\n",
                "        prediction = Analyzer.predict_next_swing_xgboost(swings, window=50)\n",
                "    elif MODEL_TYPE == 'LSTM':\n",
                "        prediction = Analyzer.predict_next_swing_lstm(swings, window=6)\n",
                "\n",
                "    if prediction:\n",
                "        print(f\"\\n=== {MODEL_TYPE} PROGNOZA ===\")\n",
                "        print(f\"Kierunek: {prediction['direction']}\")\n",
                "        print(f\"Cel cenowy: {prediction['target_price']:.2f}\")\n",
                "        print(f\"Przewidywany czas: {prediction['target_time']}\")\n",
                "\n",
                "# Behavioral & Exhaustion Analysis\n",
                "print(\"Detecting anomalies and exhaustion...\")\n",
                "climax_signals = Analyzer.detect_climax(df)\n",
                "effort_signals = Analyzer.analyze_effort_vs_result(swings)\n",
                "forex_scenarios = Analyzer.detect_forex_scenarios(df)\n",
                "multi_extremes = Analyzer.detect_multi_extremes(swings)\n",
                "\n",
                "# Calculate Exhaustion Score (XGBoost logic internalized)\n",
                "df = Analyzer.calculate_exhaustion_score(df, swings)\n",
                "\n",
                "# Save behavioral signals to DB\n",
                "if not climax_signals.empty: db.save_behavioral_signals(climax_signals, symbol)\n",
                "if not effort_signals.empty: db.save_behavioral_signals(effort_signals, symbol)\n",
                "if not forex_scenarios.empty: db.save_behavioral_signals(forex_scenarios, symbol)\n",
                "if not multi_extremes.empty: db.save_behavioral_signals(multi_extremes, symbol)\n",
                "\n",
                "# Wave Logic Signals\n",
                "sot_signals = Analyzer.detect_sot(swings)\n",
                "hinge_signals = Analyzer.detect_hinge(swings)\n",
                "springboard_signals = Analyzer.detect_springboard(swings, hinge_signals) if not hinge_signals.empty else pd.DataFrame()"
            ]

        # 2. Update Section 5 (Visualization) - Use subplots for Exhaustion Score
        if "go.Figure()" in source and "Candlestick" in source:
            cell['source'] = [
                "from plotly.subplots import make_subplots\n",
                "if not df.empty:\n",
                "    df_v = df.iloc[max(0, len(df)-600):]\n",
                "    \n",
                "    # Create Subplots: Main Chart + Exhaustion Panel\n",
                "    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, \n",
                "                        vertical_spacing=0.03, row_heights=[0.7, 0.3])\n",
                "    \n",
                "    # Candle Chart\n",
                "    fig.add_trace(go.Candlestick(x=df_v['time'], open=df_v['open'], high=df_v['high'], low=df_v['low'], close=df_v['close'], name='Price', opacity=0.4), row=1, col=1)\n",
                "    \n",
                "    # ZigZag\n",
                "    zz_pts = df_v[df_v['zigzag'] != 0]\n",
                "    fig.add_trace(go.Scatter(x=zz_pts['time'], y=zz_pts['zigzag'], mode='lines+markers', line=dict(color='blue', width=2), name='ZigZag'), row=1, col=1)\n",
                "\n",
                "    # Exhaustion Score Panel\n",
                "    fig.add_trace(go.Scatter(x=df_v['time'], y=df_v['exhaustion_score'], fill='tozeroy', name='Exhaustion Score', line=dict(color='red', width=2)), row=2, col=1)\n",
                "    fig.add_hline(y=70, line_dash=\"dash\", line_color=\"orange\", row=2, col=1)\n",
                "    fig.update_yaxes(title_text=\"Exhaustion %\", range=[0, 100], row=2, col=1)\n",
                "\n",
                "    # Behavioral Signals Overlays\n",
                "    behavioral_cfg = [\n",
                "        (climax_signals, 'white', 'hexagram', 'Climax'),\n",
                "        (effort_signals, 'orange', 'diamond-tall', 'Effort-vs-Result'),\n",
                "        (forex_scenarios, 'coral', 'star-triangle-up', 'Wyckoff Test'),\n",
                "        (multi_extremes, 'yellow', 'triangle-up-dot', 'Multi-Extreme')\n",
                "    ]\n",
                "    for sigs, color, marker, name in behavioral_cfg:\n",
                "        if not sigs.empty:\n",
                "            vis = sigs[sigs['time'] >= df_v['time'].iloc[0]]\n",
                "            if not vis.empty:\n",
                "                fig.add_trace(go.Scatter(x=vis['time'], y=vis['price'], mode='markers', \n",
                "                                         marker=dict(color=color, size=12, symbol=marker), name=name), row=1, col=1)\n",
                "\n",
                "    # Wave Logic\n",
                "    for sigs, color, marker, name in [(sot_signals, 'red', 'triangle-down', 'SOT'), (hinge_signals, 'white', 'diamond', 'Hinge'), (springboard_signals, 'gold', 'star', 'Springboard')]:\n",
                "        if not sigs.empty:\n",
                "            vis = sigs[sigs['time'] >= df_v['time'].iloc[0]]\n",
                "            if not vis.empty:\n",
                "                fig.add_trace(go.Scatter(x=vis['time'], y=vis['price'], mode='markers', marker=dict(color=color, size=14, symbol=marker), name=name), row=1, col=1)\n",
                "\n",
                "    fig.update_layout(title=f'{symbol} Exhaustion & Behavioral Analysis', template='plotly_dark', \n",
                "                      xaxis_rangeslider_visible=False, height=900, showlegend=True)\n",
                "    fig.show()"
            ]

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
