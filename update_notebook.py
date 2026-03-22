import nbformat as nbf
import os

nb_path = 'midas.ipynb'
if os.path.exists(nb_path):
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbf.read(f, as_version=4)
    
    # Target existing cell source prefix
    target_prefix = "from swing_analytics import SwingAnalytics, SWING_TYPE, TREND_STATE"
    
    # 1. Global Initialization (Top Cell)
    import pandas as pd
    init_code = [
        "import plotly.graph_objects as go",
        "import pandas as pd",
        "import config",
        "from data_connector import MT5Connector",
        "from database import DatabaseManager",
        "from analysis import Analyzer",
        "",
        "# Global Signal Initialization to prevent NameError",
        "climax_signals = effort_signals = forex_scenarios = pd.DataFrame()",
        "multi_extremes = sot_signals = hinge_signals = storyboard_signals = pd.DataFrame()",
        "springboard_signals = pd.DataFrame()",
        "prediction = None",
        "",
        "# Settings",
        "pd.set_option('display.max_columns', None)"
    ]
    nb.cells[1].source = "\n".join(init_code)

    # 2. Section 9 Code (Swing Dashboard)
    code_lines = [
        "from swing_analytics import SwingAnalytics, SWING_TYPE, TREND_STATE",
        "from swing_dashboard import SwingDashboard",
        "import pandas as pd",
        "",
        "if not df.empty:",
        "    # 1. Analytics Setup",
        "    point = 0.01 if symbol == 'XAUUSD' else 0.00001",
        "    analytics = SwingAnalytics(point_value=point)",
        "    ",
        "    # 2. Process Data",
        "    zigzag = analytics.calculate_zigzag(df)",
        "    swings_v2 = analytics.process_swings(df, zigzag)",
        "    pullbacks_v2 = analytics.analyze_pullbacks(swings_v2)",
        "    ",
        "    # 3. Interactive Plotly chart with Predictions",
        "    pred = locals().get('prediction')",
        "    fig_swings = analytics.plot_swings(df.iloc[-500:], swings_v2[-25:], prediction=pred, title=f'Interactive Swing Map - {symbol}')",
        "    fig_swings.show()",
        "    ",
        "    # 4. Rich Analytical Tables",
        "    dashboard = SwingDashboard(symbol, 'M1')",
        "    dashboard.render_all_tables(swings_v2, pullbacks_v2)"
    ]
    new_source = "\n".join(code_lines)
    
    # Robustness Fixes for existing cells
    for cell in nb.cells:
        # Fix Section 5 (Visualization) - prevent NameError and KeyError
        if cell.cell_type == 'code' and "behavioral_cfg = [" in cell.source:
             # Make signal access defensive using locals().get()
             replacements = {
                 "climax_signals": "locals().get('climax_signals', pd.DataFrame())",
                 "effort_signals": "locals().get('effort_signals', pd.DataFrame())",
                 "forex_scenarios": "locals().get('forex_scenarios', pd.DataFrame())",
                 "multi_extremes": "locals().get('multi_extremes', pd.DataFrame())",
                 "sot_signals": "locals().get('sot_signals', pd.DataFrame())",
                 "hinge_signals": "locals().get('hinge_signals', pd.DataFrame())",
                 "springboard_signals": "locals().get('springboard_signals', pd.DataFrame())"
             }
             for old, new in replacements.items():
                 cell.source = cell.source.replace(old, new)
        
        # Fix Section 5 (Visualization) - prevent KeyError on exhaustion_score
        if cell.cell_type == 'code' and "y=df_v['exhaustion_score']" in cell.source:
            cell.source = cell.source.replace("y=df_v['exhaustion_score']", "y=df_v.get('exhaustion_score', pd.Series(0, index=df_v.index))")

        # Fix Section 7 (Dashboard) - KeyError: 'exhaustion_score'
        if cell.cell_type == 'code' and "last_row['exhaustion_score']" in cell.source:
            cell.source = cell.source.replace("last_row['exhaustion_score']", "last_row.get('exhaustion_score', 0)")

    cell_found = False
    for cell in nb.cells:
        if cell.cell_type == 'code' and target_prefix in cell.source:
            cell.source = new_source
            cell_found = True
            break
            
    if not cell_found:
        # If not found, add a new cell with markdown header
        md_cell = nbf.v4.new_markdown_cell("## 9. Swing Analytics Dashboard (V2.2)\n\nInteractive charts and detailed structural analysis.")
        code_cell = nbf.v4.new_code_cell(new_source)
        nb.cells.extend([md_cell, code_cell])
        print("Integrated new section.")
    else:
        print("Updated existing section.")
        
    with open(nb_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
    print("midas.ipynb updated successfully.")
else:
    print("midas.ipynb not found.")
