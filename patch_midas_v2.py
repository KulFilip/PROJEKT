
import json
import os

notebook_path = 'midas.ipynb'

if os.path.exists(notebook_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # Define new cells
    new_cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 8. Advanced Production Analysis (V2)\n",
                "\n",
                "This section uses `analysis_v2.py` which includes:\n",
                "- **VSA/Wyckoff Features**: Advanced volume and spread analysis.\n",
                "- **Enriched Swings**: Swing-level data enriched with bar-level statistics.\n",
                "- **Verified No-Leakage**: Strict temporal separation for ML training."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from analysis_v2 import Analyzer as AnalyzerV2, ForexFeatures, ValidationTools\n",
                "import pandas as pd\n",
                "\n",
                "# 1. Calculate Comprehensive Forex Features\n",
                "print(\"Calculating V2 features...\")\n",
                "df_v2 = ForexFeatures.calculate_all(df)\n",
                "\n",
                "# 2. Analyze Swings (ZigZag)\n",
                "df_v2['zigzag'] = AnalyzerV2.calculate_zigzag(df_v2)\n",
                "swings_v2 = AnalyzerV2.analyze_swings(df_v2)\n",
                "\n",
                "# 3. Enrich Swings with Forex Features (Critical Tier)\n",
                "swings_enriched = AnalyzerV2.enrich_swings_with_forex_features(swings_v2, df_v2, feature_tier='critical')\n",
                "\n",
                "print(f\"\\nEnriched Swings: {len(swings_enriched)}\")\n",
                "display(swings_enriched.tail())"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 4. Backtest V2 Logic (XGBoost)\n",
                "BT_MODEL_V2 = 'XGBoost'\n",
                "print(f\"Running V2 Backtest ({BT_MODEL_V2})...\")\n",
                "results_v2 = AnalyzerV2.backtest(swings_enriched, df_v2, method=BT_MODEL_V2, window=10, min_history=50)\n",
                "\n",
                "if not results_v2.empty:\n",
                "    scores_v2 = AnalyzerV2.verify_performance(results_v2)\n",
                "    print(f\"\\n=== {BT_MODEL_V2} V2 SCORES ===\")\n",
                "    for k, v in scores_v2.items():\n",
                "        val = v*100 if 'mape' in k or 'accuracy' in k else v\n",
                "        suffix = '%' if 'mape' in k or 'accuracy' in k else ''\n",
                "        print(f\"{k.replace('_', ' ').title()}: {val:.2f}{suffix}\")\n",
                "    \n",
                "    # Save Report\n",
                "    AnalyzerV2.save_backtest_report(results_v2, scores_v2, f\"{BT_MODEL_V2}_V2\", symbol=symbol)\n",
                "else:\n",
                "    print(\"Backtest failed or insufficient data.\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 5. Data Leakage Verification\n",
                "print(\"Running Leakage Verification...\")\n",
                "ValidationTools.test_data_leakage(swings_enriched, df_v2, window=10)"
            ]
        }
    ]

    # Append new cells
    # Remove the last empty cell if it exists
    if nb['cells'] and not nb['cells'][-1]['source']:
        nb['cells'].pop()
        
    nb['cells'].extend(new_cells)

    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    print(f"Successfully patched {notebook_path} with V2 compartment.")
else:
    print(f"Error: {notebook_path} not found.")
