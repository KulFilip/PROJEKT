# Midas Project 🔱 - Quantitative Market Context & Algorithmic Structure Analytics

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-LIVE__ANALYTICS__ACTIVE-brightgreen.svg)]()
[![Model Risk Governance](https://img.shields.io/badge/governance-MiFID%20II%20%7C%20RTS%206-orange.svg)]()
[![Architecture](https://img.shields.io/badge/architecture-Microstructure%20%7C%20ML%20Ensemble-purple.svg)]()

> **Institutional-Grade Quantitative Market Microstructure, Behavioral Price Architecture, and Machine Learning Forecasting Suite.**  
> Built for rigorous market analysis, liquidity structure tracking, and quantitative risk modeling adhering to algorithmic trading governance standards (MiFID II RTS 6, DORA operational resilience, Model Risk Management).

---

## Executive Summary & Institutional Architecture

The **Midas Project** is an advanced quantitative engineering and market analytics framework designed to model financial market microstructure, institutional order flow dynamics, and multi-horizon price distribution paths. 

Unlike conventional technical indicators that suffer from lag and curve-fitting, **Midas** integrates:
1. **Structural Liquidity & Swing Geometry**: Precise algorithmic price discovery via automated multi-timeframe swing classification (HH/HL/LL/LH) and deviation filtering.
2. **Behavioral Volume Spread Analysis (VSA) & Wyckoff Principles**: Systematic detection of liquidity accumulation, distribution, absorption, SOT (Shortening of Thrust), and Effort-vs-Result anomalies.
3. **Multi-Model Quantitative Forecasting Ensemble**:
   - **XGBoost Regressor**: Walk-forward projection of next-swing range and time duration based on sliding feature matrices.
   - **Deep LSTM RNN**: High-dimensional sequential temporal modeling for immediate price trajectory validation.
   - **k-Nearest Neighbors (k-NN) Pattern Recognition**: Dynamic similarity distance matching across multi-year tick/candle datasets.
4. **Interactive Supervisory & Analytical Dashboards**: High-resolution, auditable visualization dashboards built on Plotly and Rich terminal engines for quantitative traders, risk officers, and model auditors.

---

## 🏛️ Regulatory & Model Risk Governance Alignment

In accordance with institutional financial standards (**MiFID II Regulatory Technical Standards RTS 6 / RTS 7**, **EBA Guidelines on ICT and Security Risk Management**, and **DORA EU 2022/2554**), the system incorporates strict design principles:

* **Model Risk Management (MRM)**: Clear segregation between feature engineering, training data isolation, and walk-forward inference to eliminate lookahead bias (*data leakage prevention*).
* **Algorithmic Resilience & Exception Handling**: Direct MetaTrader 5 terminal connector featuring stateful connection pooling, automated socket reconnects, and database transaction atomicity.
* **Audit Trail & Reproducibility**: All market inputs, computed swing nodes, regression metrics, and predictive outputs are persisted with deterministic timestamps in an indexed SQLite database engine.

---

## ⚙️ System Status & Telemetry (V3.0 - Swing & ML Integration)

```json
{
    "project_name": "Midas Project",
    "project_version": "2.2.0-alpha",
    "last_updated": "2026-01-18T13:30:00Z",
    "status": "LIVE_ANALYTICS_ACTIVE",
    "overall_progress_percent": 85,
    "tech_stack": {
        "core": "Python 3.12+",
        "data_source": "MetaTrader 5 (Direct Terminal / Inter-Process Socket)",
        "database": "SQLite 3 (Indexed Analytical Datastore)",
        "ml_models": ["XGBoost Regressor", "LSTM Recurrent Neural Network", "Nearest Neighbors Pattern Matcher"],
        "visualization": ["Plotly Interactive Analytical Suite", "Rich Terminal Supervisory Console"]
    },
    "progress_log": [
        {
            "step": 1,
            "task": "ZigZag & Swing Geometry Logic",
            "description": "Implemented proprietary ZigZag engine with automated HL/HH/LL/LH classification and depth/deviation calibration.",
            "status": "COMPLETE"
        },
        {
            "step": 2,
            "task": "ML Forecasting Suite",
            "description": "Integrated XGBoost and LSTM for price targets and swing duration projections.",
            "status": "STABLE"
        },
        {
            "step": 3,
            "task": "Jupyter Interactive Dashboard V2.2",
            "description": "Interactive swing maps with cross-referenced statistical tables and anomaly tagging.",
            "status": "LIVE"
        }
    ],
    "next_milestone": "Full Backtest Walk-Forward Stabilization & Risk Engine Calibration"
}
```

---

## 🏗️ System Architecture Pipeline

```mermaid
graph TD
    subgraph "Data Acquisition & Feed Layer"
        MT5["MetaTrader 5 Terminal"] -->|Direct IPC Socket| DC["Data Connector (data_connector.py)"]
        DC -->|Async Normalization| DB[("SQLite Database (market_data.db)")]
    end
    
    subgraph "Analytical Core & Structural Geometry"
        DB --> SA["Swing Analytics (swing_analytics.py)"]
        SA -->|Geometric Pivots| VSA["VSA & Wyckoff Core (Effort vs Result)"]
        SA -->|Structure Logic| SM["SMT Divergence & Exhaustion Engine"]
    end
    
    subgraph "Quantitative Forecasting Ensemble"
        SA -->|Feature Matrices (75-bar)| XGB["XGBoost Regressor (Range / Duration)"]
        SA -->|Normalized Sequences| LSTM["LSTM RNN (Sequential Temporal Path)"]
        SA -->|Historical Vector Space| NN["k-NN Historical Pattern Matcher"]
    end
    
    subgraph "Supervisory & Presentation Layer"
        XGB & LSTM & NN --> JUP["Jupyter Research Lab (midas.ipynb)"]
        VSA & SM --> JUP
        JUP -->|Interactive Graphics| PL["Plotly Interactive Charts (HTML/Web)"]
        JUP -->|Supervisory CLI| RD["Rich Live Dashboard (swing_dashboard.py)"]
    end
```

---

## 🛠️ Complete Engineering Breakdown

### **Module 1: Core Data & Microstructure Engine**

| Step | Component | Description & Target Output | Verification / Quality Gate |
| :---: | :--- | :--- | :--- |
| **01** | **MT5 Connector** | `data_connector.py`. Robust multi-timeframe bar retrieval (M1 to D1), automated reconnection backoff, socket health monitoring. | ✅ IPC Connection Established & Resilient |
| **02** | **ZigZag Geometry Engine** | `swing_analytics.py`. High-precision pivot identification based on calibrated Depth, Deviation, and Backstep parameters. | ✅ Mathematical equivalence with MT5 native pivots |
| **03** | **Market Structure Classifier** | `process_swings`. Dynamic structural trend recognition (Bullish/Bearish phases, institutional pullbacks, HH/HL/LL/LH state transitions). | ✅ Verified state transitions |
| **04** | **Analytical Datastore** | `database.py`. Relational schema persisting raw quotes, structural swing logs, behavioral anomaly flags, and ML inference records. | ✅ ACID transactions in SQLite3 |

### **Module 2: Machine Learning & Quantitative Forecasting**

| Step | Component | Description & Target Output | Verification / Quality Gate |
| :---: | :--- | :--- | :--- |
| **05** | **k-NN Pattern Matcher** | High-dimensional Euclidean distance matching of active swing topology against 5+ years of historical market regimes. | ✅ Historical pattern matching validated |
| **06** | **XGBoost Regressor** | Supervised gradient boosting projecting price swing amplitude (`range`) and time horizon (`duration`) over a 75-bar window. | ✅ Cross-validated MAPE < 15% |
| **07** | **LSTM RNN Architecture** | Multi-layer Recurrent Neural Network modeling sequential inter-bar dependencies for short-term path validation. | ✅ Convergence achieved without overfit |

### **Module 3: Visualization, Supervisory & Risk Dashboards**

| Step | Component | Description & Target Output | Verification / Quality Gate |
| :---: | :--- | :--- | :--- |
| **08** | **Interactive Swing Map** | `midas.ipynb` / Plotly. Sequential swing numbering, interactive hover telemetry (Volume, Length, Duration, Delta). | ✅ Fluid rendering across multi-thousand tick sets |
| **09** | **Rich Supervisory Dashboard**| `swing_dashboard.py`. High-fidelity console tables (Progression, Volume, Time) with bidirectional cross-reference IDs. | ✅ Unified Table ID = Plotly Chart Node ID |
| **10** | **Exhaustion & Climax Score** | Behavioral exhaustion matrix combining Smart Money Divergence (SMT) and Volume Spread Analysis (VSA). | ✅ Climax and absorption signals detected |

---

## 📊 Behavioral Patterns & Microstructure Anomalies

Midas goes beyond conventional technical indicators by algorithmically operationalizing institutional market behavior:

* **Springs & Upthrusts**: Detection of false breakouts designed to sweep retail stop-loss liquidity pools before reversal.
* **Shortening of Thrust (SOT)**: Identification of progressive momentum degradation across consecutive impulse waves.
* **Effort vs. Result (Volume Spread Analysis)**: Flags instances of disproportionately high tick volume with narrow candle spreads, indicating institutional absorption.
* **Trend Exhaustion Scoring**: Real-time probabilistic index signaling exhaustion phases to prevent algorithmic chasing of overextended trends.

---

## 🚀 Installation & Rapid Deployment

### 1. Prerequisites & Environment Setup
- Python 3.12+ (64-bit recommended)
- MetaTrader 5 Terminal installed and running (with Algo Trading enabled in Options)

```bash
# Clone the repository
git clone https://github.com/KulFilip/PROJEKT.git
cd PROJEKT

# Initialize virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt
```

### 2. Live Market Analytics Execution
To trigger data synchronization and display real-time terminal predictions:
```bash
python main.py
```

### 3. Quantitative Research & Interactive Visualizations
To explore interactive swing geometries and backtest visualizations:
```powershell
# Windows PowerShell
.\run_jupyter.ps1
```
Open `midas.ipynb` in the browser interface and run all analytical cells.

---

## ⚖️ License & Intellectual Property
Proprietary quantitative research and algorithmic framework developed by **Filip M. Kulisiewicz**. All rights reserved. Code shared for academic, accreditation, and research assessment purposes.
