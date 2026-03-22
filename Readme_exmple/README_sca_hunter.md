# SCA-Hunter 🛡️

SCA-Hunter is a modern Software Composition Analysis (SCA) tool designed for rapid identification and prioritization of vulnerabilities in open-source dependencies. It features a robust heuristics engine, DORA-compliant reporting, and a FastAPI-powered orchestration layer.

## 🚀 Key Features

-   **Multi-Ecosystem Support**: Native parsing for Python (`requirements.txt`), Node.js (`package-lock.json`), and PHP (`composer.lock`).
-   **OSV.dev Integration**: Real-time vulnerability intelligence using the Google Open Source Vulnerabilities (OSV) API.
-   **Intelligent Heuristics**: Custom scoring engine that prioritizes vulnerabilities based on keywords (e.g., RCE, SQLi) and CVSS scores.
-   **DORA-Compliant Reporting**: Generates HTML reports fully compatible with the Digital Operational Resilience Act (DORA) requirements.
-   **API-First Design**: Built with FastAPI, allowing easy integration into CI/CD pipelines and external security dashboards.
-   **Rich CLI Interface**: Beautiful terminal output using the `rich` library for quick manual scans.

---

## � Manifest Discovery & Directory Handling

SCA-Hunter is designed to handle both individual files and entire project directories. 

### How it finds manifests:
The system uses the `ManifestScanner` (located in `app/scanner/discovery.py`) to locate supported dependency files.
- **Recursive Scan**: By default, it performs a recursive search from the target directory.
- **Supported Files**:
  - `requirements.txt` ➡️ **Python** (PyPI)
  - `package-lock.json` ➡️ **Node.js** (npm)
  - `composer.lock` ➡️ **PHP** (Packagist)
- **Exclusions**: Hidden directories (e.g., `.git`, `.venv`, `node_modules`) are automatically ignored to ensure performance and accuracy.

---

## �🛠️ Prerequisites

-   **Python 3.12+**
-   **Docker & Docker Compose**
-   **Poetry** (optional, for dependency management)

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-repo/sca-hunter.git
cd sca-hunter
```

### 2. Set up the environment
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Start infrastructure
```bash
docker-compose up -d
```
*Note: The PostgreSQL database is exposed on port **5433**.*

### 4. Apply Migrations
```bash
$env:DATABASE_URL="postgresql+asyncpg://hunter:Hunta#2026_Secure!@localhost:5433/sca_hunter"
python -m alembic upgrade head
```

---

## 📖 Usage

### CLI (Manual Scan)
You can run a scan directly from the command line using the `run_test_scan.py` script or by interacting with the orchestrator directly.

### Scanning Implementation
The core scanning logic is encapsulated in the `ScanOrchestrator` (`app/scanner/orchestrator.py`). 

**The Pipeline Flow:**
1. **Discovery**: `ManifestScanner` identifies all manifests in the target path.
2. **Parsing**: ecosystem-specific parsers (`app/inventory/`) extract dependencies and versions.
3. **Resolution**: `OSVClient` (`app/intelligence/`) queries the OSV.dev database for vulnerabilities.
4. **Analysis**: The `DecisionEngine` (`app/decision/`) applies heuristics to score and prioritize findings.
5. **Persistence**: Results are saved to **PostgreSQL** via SQLAlchemy models.
6. **Delivery**: Reports are generated in the requested format.

```bash
# Example: Scan a Python manifest
python run_test_scan.py
```

### API (Orchestration)
The API provides endpoints for triggering scans and retrieving reports.

**Start the API Server:**
```bash
$env:PYTHONPATH="."
python -m uvicorn app.main:app --reload
```

**Access Documentation:**
Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

**Key Endpoints:**
- `POST /api/v1/scans`: Trigger a new scan.
- `GET /api/v1/scans/{id}`: Get scan status and summary.
- `GET /api/v1/scans/{id}/report/{format}`: Export report (json, html, dora).

---

## 📊 DORA Compliance
SCA-Hunter includes a dedicated report generator for DORA compliance, ensuring your organization meets ICT risk management requirements.

Reports include:
- **Executive Summary** (Risk landscape)
- **Classification of ICT Risks**
- **Incident Reporting Metadata**
- **Remediation & Action Plan**

---

## 🏗️ Architecture

```mermaid
graph TD
    A[API / CLI] --> B[Orchestrator]
    B --> C[Inventory Parsers]
    B --> D[OSV Intelligence Client]
    D --> E[External OSV API]
    B --> F[Heuristics Engine]
    B --> G[Database]
    B --> H[Report Generators]
    H --> I[JSON / HTML / DORA]
```

---

## 🧪 Testing
Run the full test suite to ensure everything is working correctly:

```bash
python -m pytest tests/
```

---

## 📄 License
Project created for internal security and compliance demonstrative purposes.
