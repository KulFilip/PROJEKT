import json
import os

path = r'c:\Users\donniebrasco\Documents\PROJEKT\midas.ipynb'
if not os.path.exists(path):
    print(f"Error: {path} not found")
    exit(1)

with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Add Markdown Header
nb['cells'].append({
    'cell_type': 'markdown',
    'metadata': {},
    'source': [
        '# 9. Reversal Analytics Dashboard (V3)\n',
        '---\n',
        'This compartment visualizes high-probability reversal zones by correlating price multi-extremes with VSA/Wyckoff signatures.'
    ]
})

# Add Code Cell
code_source = [
    'from analysis_v2 import Analyzer, ForexFeatures, DashboardBuilder\n',
    'import pandas as pd\n',
    'from IPython.display import display\n',
    '\n',
    '# 1. Detect Reversals using the new V3 logic\n',
    'print("Detecting reversal signatures (Price + VSA)...")\n',
    'reversals_df = Analyzer.detect_reversal_signatures(swings_v2, df_v2, tolerance=0.015)\n',
    '\n',
    '# 2. Display the Reversal Dashboard\n',
    '# Note: USES df_v2 and swings_v2 from Section 8\n',
    'SYMBOL_DS = SYMBOL if "SYMBOL" in globals() else "Unknown"\n',
    'fig_reversal = DashboardBuilder.plot_reversal_analytics(df_v2, reversals_df, symbol=SYMBOL_DS)\n',
    'fig_reversal.show()\n',
    '\n',
    '# 3. Full Spectrum Analytics Table\n',
    'if not reversals_df.empty:\n',
    '    print("\\nFull Spectrum Reversal Table:")\n',
    '    # Highlight by strength and climax score\n',
    '    display(reversals_df.sort_values("strength", ascending=False).style.background_gradient(subset=["strength", "climax_score"], cmap="RdYlGn"))\n',
    'else:\n',
    '    print("No reversal patterns detected in the current window.")'
]

nb['cells'].append({
    'cell_type': 'code',
    'execution_count': None,
    'metadata': {},
    'outputs': [],
    'source': code_source
})

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("✅ midas.ipynb patched successfully with Section 9.")
