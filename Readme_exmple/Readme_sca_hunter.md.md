# ULEPSZONA DOKUMENTACJA PROJEKTU SCA-HUNTER

## BOT STATUS LOG (Wersja Finalna z PostgreSQL)

```json
{
    "project_name": "SCA-Hunter",
    "project_version": "0.1.0-alpha",
    "last_updated": "2026-01-11T21:00:00Z",
    "status": "ARCHITECTURE_COMPLETE",
    "overall_progress_percent": 0,
    "deployment_status": "PENDING_IMPLEMENTATION",
    "tech_stack": {
        "backend": "FastAPI + Python 3.11+",
        "database": "PostgreSQL 15+",
        "cve_source": "cve-search (MongoDB backend)",
        "architecture": "Clean Architecture + TDD",
        "deployment": "Docker Compose"
    },
    "progress_log": [
        {
            "step": 0,
            "task": "Project Definition and Architecture",
            "description": "Finalized comprehensive blueprint for SCA-Hunter with PostgreSQL integration, Clean Architecture pattern, and complete TDD task breakdown.",
            "timestamp": "2026-01-11T21:00:00Z",
            "status": "COMPLETE"
        }
    ],
    "issue_history": [],
    "next_milestone": "MODUŁ 0: Infrastructure Setup (Steps 01-04)"
}
```

---

## 🛠️ KOMPLETNY TASK BREAKDOWN

### **MODUŁ 0: ARCHITEKTURA, INFRASTRUKTURA I FUNDAMENTY**

| Step   | Task                                    | Opis / Wymagany Rezultat                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Weryfikacja                                                                            |
| ------ | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **01** | **Project Setup & Repository**          | Inicjalizacja Git repo, utworzenie struktury folderów zgodnie z Clean Architecture:`sca-hunter/``├── app/``│ ├── core/ # Domain logic``│ ├── inventory/ # Dependency parsers``│ ├── scanner/ # SCA engine``│ ├── intelligence/ # CVE resolver``│ ├── decision/ # Decision engine``│ ├── report/ # Report generator``│ ├── db/ # Database layer``│ └── api/ # FastAPI endpoints``├── tests/``├── docker/``└── docs/`                                                                                                                                                                                                               | ✅ Struktura folderów istnieje✅ `.gitignore` skonfigurowany✅ `pyproject.toml` utworzony |
| **02** | **Dependencies & Virtual Environment**  | Instalacja bazowych zależności:- FastAPI + Uvicorn- SQLAlchemy 2.0+ (async)- asyncpg (PostgreSQL driver)- Pydantic 2.0+- httpx (async HTTP client)- pytest + pytest-asyncio- alembic (migrations)                                                                                                                                                                                                                                                                                                                                                                                                                                 | ✅ `poetry install` lub `pip install -r requirements.txt` działa✅ Virtual env aktywny   |
| **03** | **Docker Compose: Multi-Service Setup** | Konfiguracja `docker-compose.yml`:`yaml``services:` `postgres:` `image: postgres:15-alpine` `environment:` `POSTGRES_DB: sca_hunter` `POSTGRES_USER: hunter` `POSTGRES_PASSWORD: secure_pass` `volumes:` `- postgres_data:/var/lib/postgresql/data` `cve-search:` `image: cve-search/cve-search:latest` `depends_on:` `- mongodb` `ports:` `- "5000:5000"` `mongodb:` `image: mongo:6` `volumes:` `- mongo_data:/data/db` `app:` `build: .` `depends_on:` `- postgres` `- cve-search` `environment:` `DATABASE_URL: postgresql+asyncpg://hunter:secure_pass@postgres:5432/sca_hunter` `CVE_SEARCH_URL: http://cve-search:5000```` | ✅ `docker-compose up` uruchamia wszystkie serwisy✅ PostgreSQL i cve-search odpowiadają |
| **04** | **PostgreSQL Connection Layer**         | Implementacja `app/db/session.py`:- AsyncEngine configuration- async_sessionmaker factory- Base declarative class- Connection pooling setup- Health check function                                                                                                                                                                                                                                                                                                                                                                                                                                                                | ✅ Test połączenia do PostgreSQL przechodzi✅ `async with get_session()` działa          |
| **05** | **Project Charter & Documentation**     | Utworzenie `docs/project_charter.md` zawierającego:- **Cel projektu**: Automatyczna detekcja exploitable CVE w aplikacjach- **Filozofia**: TDD + Clean Architecture- **Logika decyzyjna**: Jak określamy "nowe CVE"- **Kryteria sukcesu**: Metryki (False Positive Rate < 5%)- **Architektura**: Diagram modułów                                                                                                                                                                                                                                                                                                                  | ✅ Dokument zatwierdzony✅ Diagram architektury w Mermaid/PlantUML                       |
| **06** | **Alembic Migration Setup**             | Inicjalizacja Alembic dla zarządzania migracjami:- `alembic init migrations`- Konfiguracja `alembic.ini` z async PostgreSQL- Template migration script                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | ✅ `alembic upgrade head` działa✅ Migracje versionowane w Git                           |

---

### **MODUŁ 1: DATABASE MODELS & SCHEMA (PostgreSQL)**

| Step   | Task                     | Opis / Wymagany Rezultat                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Weryfikacja                                            |
| ------ | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **07** | **Model: ScanResult**    | Utworzenie `app/db/models.py` z modelem `ScanResult`:`python``class ScanResult(Base):` `__tablename__ = "scan_results"` `id = Column(UUID, primary_key=True)` `scan_id = Column(String(64), unique=True, index=True)` `target_name = Column(String(255), nullable=False)` `target_type = Column(Enum("python", "php", "nodejs"))` `manifest_path = Column(String(512))` `started_at = Column(DateTime(timezone=True))` `completed_at = Column(DateTime(timezone=True))` `status = Column(Enum("pending", "running", "completed", "failed"))` `total_dependencies = Column(Integer, default=0)` `total_vulnerabilities = Column(Integer, default=0)` `high_priority_count = Column(Integer, default=0)````                                                                                                                                 | ✅ Migration utworzona✅ Tabela istnieje w PostgreSQL    |
| **08** | **Model: Vulnerability** | Model `Vulnerability` z relacją do `ScanResult`:`python``class Vulnerability(Base):` `__tablename__ = "vulnerabilities"` `id = Column(UUID, primary_key=True)` `scan_id = Column(UUID, ForeignKey("scan_results.id"))` `cve_id = Column(String(20), index=True)` `component_name = Column(String(255), nullable=False)` `component_ecosystem = Column(String(50))` `used_version = Column(String(50))` `fixed_version = Column(String(50))` `cvss_score = Column(Float)` `cvss_vector = Column(String(100))` `summary = Column(Text)` `exposure_priority = Column(Enum("LOW", "MEDIUM", "HIGH", "CRITICAL"))` `exposure_reason = Column(Text) # Heuristic explanation` `is_transitive = Column(Boolean, default=False)` `dependency_path = Column(ARRAY(String)) # Path if transitive` `detected_at = Column(DateTime(timezone=True))```` | ✅ Migration utworzona✅ Foreign key relationship działa |
| **09** | **Model: Component**     | Model dla inwentaryzacji komponentów:`python``class Component(Base):` `__tablename__ = "components"` `id = Column(UUID, primary_key=True)` `scan_id = Column(UUID, ForeignKey("scan_results.id"))` `name = Column(String(255), nullable=False)` `version = Column(String(50), nullable=False)` `ecosystem = Column(String(50))` `is_direct = Column(Boolean, default=True)` `parent_component_id = Column(UUID, ForeignKey("components.id"))````                                                                                                                                                                                                                                                                                                                                                                                          | ✅ Migration utworzona✅ Self-referential FK działa      |
| **10** | **Pydantic Schemas**     | Utworzenie `app/core/schemas.py` z DTO:- `DependencySchema`- `VulnerabilitySchema`- `ScanResultSchema`- `ReportSchema`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | ✅ Schemas validują przykładowe dane✅ Tests pass        |

---

### **MODUŁ 2: INVENTORY & DEPENDENCY PARSERS**

|Step|Task|Opis / Wymagany Rezultat|Weryfikacja|
|---|---|---|---|
|**11**|**Parser Interface (Protocol)**|Definicja `app/inventory/parser_protocol.py`:`python``class DependencyParser(Protocol):` `def parse(self, file_path: Path) -> List[Dependency]:` `...````|✅ Interface zdefiniowany|
|**12**|**Python Parser (requirements.txt)**|Implementacja `app/inventory/python_parser.py`:- Parsowanie `==`, `>=`, `~=`, `^` operators- Obsługa komentarzy i pustych linii- Ekstrakcja extras (np. `requests[security]`)|✅ Parsuje przykładowy `requirements.txt`✅ Unit tests pass (min. 5 cases)|
|**13**|**PHP Parser (composer.lock)**|Implementacja `app/inventory/php_parser.py`:- Parsowanie JSON `composer.lock`- Ekstrakcja z sekcji `packages` i `packages-dev`- Obsługa `version` locked versions|✅ Parsuje przykładowy `composer.lock`✅ Unit tests pass|
|**14**|**Node.js Parser (package-lock.json v3)**|Implementacja `app/inventory/nodejs_parser.py`:- Parsowanie lockfile v3 format- Rekonstrukcja dependency tree- Identyfikacja direct vs transitive deps|✅ Parsuje przykładowy `package-lock.json`✅ Unit tests pass|
|**15**|**TDD: Parser Edge Cases**|Testy dla:- Puste pliki- Niepoprawny JSON/format- Brakujące pola wymagane- Duplikaty zależności- Case sensitivity|✅ Wszystkie edge cases pokryte✅ Coverage > 90%|
|**16**|**Parser Factory**|Implementacja `app/inventory/parser_factory.py`:`python``def get_parser(file_path: Path) -> DependencyParser:` `if file_path.name == "requirements.txt":` `return PythonParser()` `elif file_path.name == "composer.lock":` `return PHPParser()` `# ...````|✅ Factory zwraca właściwy parser✅ Raises error dla nieobsługiwanego pliku|

---

### **MODUŁ 3: CVE INTELLIGENCE ENGINE**

| Step   | Task                                | Opis / Wymagany Rezultat                                                                                                                                                                                                                            | Weryfikacja                                                                  |
| ------ | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **17** | **CVE-Search API Client**           | Implementacja `app/intelligence/cve_client.py`:- Async HTTP client (httpx)- Endpoint wrappers: - `/api/cve/{cve_id}` - `/api/search/{vendor}/{product}`- Error handling & retries- Rate limiting                                                    | ✅ Client łączy się z cve-search✅ Mock tests pass                             |
| **18** | **Version Comparison Utility**      | Implementacja `app/core/version_utils.py`:- Funkcja `is_vulnerable(current: str, fixed: str) -> bool`- Obsługa semantic versioning- Obsługa pre-release versions                                                                                    | ✅ Unit tests dla różnych formatów wersji✅ Edge cases pokryte                 |
| **19** | **CVE Resolver: Core Logic**        | Implementacja `app/scanner/cve_resolver.py`:`python``async def resolve_vulnerabilities(` `dependency: Dependency,` `cve_client: CVEClient``) -> List[Vulnerability]:` `# Query cve-search` `# Filter by version` `# Return only applicable CVEs```` | ✅ Resolver zwraca CVEs dla podatnej wersji✅ Nie zwraca dla załatanych wersji |
| **20** | **CVSS Score Normalization**        | Parsing i normalizacja CVSS z różnych formatów:- CVSS v2- CVSS v3.0- CVSS v3.1Konwersja do unified score (0-10)                                                                                                                                     | ✅ Wszystkie formaty parsowane poprawnie✅ Score mapping verified              |
| **21** | **TDD: Resolver Integration Tests** | Testy integracyjne z mock cve-search:- Dependency z known CVE- Dependency bez CVE- Multiple CVEs (różne severity)- Fixed version filtering                                                                                                          | ✅ Wszystkie scenariusze pass✅ Coverage > 85%                                 |

---

### **MODUŁ 4: CONTEXT ANALYSIS & HEURISTICS**

| Step   | Task                                            | Opis / Wymagany Rezultat                                                                                                                                                                                                                                                                                                                                    | Weryfikacja                                                          |
| ------ | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **22** | **Heuristic Engine: Keyword Scoring**           | Implementacja `app/decision/heuristics.py`:`python``RISK_KEYWORDS = {` `"CRITICAL": ["remote code execution", "RCE", "arbitrary code"],` `"HIGH": ["SQL injection", "XSS", "CSRF", "deserialization"],` `"MEDIUM": ["denial of service", "DoS", "information disclosure"],``}``def score_by_keywords(summary: str) -> str:` `# Return exposure priority```` | ✅ Scoring logic działa✅ Unit tests dla każdego poziomu               |
| **23** | **Heuristic Engine: CVSS-based Prioritization** | Logika uwzględniająca CVSS:- CVSS >= 9.0 → CRITICAL- CVSS 7.0-8.9 → HIGH- CVSS 4.0-6.9 → MEDIUM- CVSS < 4.0 → LOW                                                                                                                                                                                                                                           | ✅ Priorytet zgodny z CVSS✅ Edge cases (brak CVSS) obsłużone          |
| **24** | **Exploitability Check (Optional Enhancement)** | Integracja z EPSS (Exploit Prediction Scoring System):- Wywołanie API FIRST.org- Dodanie `epss_score` do modelu- Boost priority jeśli EPSS > 0.5                                                                                                                                                                                                            | ✅ EPSS data pobierana (jeśli dostępna)✅ Graceful fallback jeśli brak |
| **25** | **Code Context Analyzer (Zaawansowane)**        | **OPCJONALNE**: AST parsing dla wykrycia użycia:- Python: `ast.parse()` → szukanie wywołań podatnych funkcji- PHP: `php-parser` → token analysisJeśli wykryte użycie → boost priority                                                                                                                                                                       | ✅ Proof of concept działa✅ Może być w wersji beta                    |

---

### **MODUŁ 5: DECISION ENGINE**

| Step   | Task                                      | Opis / Wymagany Rezultat                                                                                                                                                                                                                                                                    | Weryfikacja                                                 |
| ------ | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **26** | **Decision Engine: Core Logic**           | Implementacja `app/decision/engine.py`:`python``async def evaluate_vulnerability(` `vuln: Vulnerability,` `context: ScanContext``) -> VulnerabilityAssessment:` `# Apply heuristics` `# Check exploitability` `# Determine if "new CVE candidate"` `# Return final priority & reasoning```` | ✅ Engine zwraca assessment✅ Reasoning jest zrozumiałe       |
| **27** | **"New CVE" Detection Logic**             | Logika decyzyjna:1. CVE istnieje w upstream component2. Aplikacja używa starej wersji (nie załatanej)3. Heurystyka wskazuje HIGH exposure4. → Mark as "CVE Candidate" for target app                                                                                                        | ✅ Test case: PHPMailer RCE w Plugin X✅ Poprawnie oznaczone  |
| **28** | **Transitive Dependency Risk Assessment** | Ocena ryzyka dla zależności pośrednich:- Lower priority niż direct deps- Boost jeśli direct dep ma known CVE- Dependency path tracking                                                                                                                                                      | ✅ Transitive deps nie pomijane✅ Priority adjusted correctly |
| **29** | **TDD: Decision Engine Tests**            | Test scenarios:- HIGH priority CVE w direct dep- MEDIUM CVE w transitive dep- Patched version ale app używa old- False positive reduction                                                                                                                                                   | ✅ Wszystkie scenariusze pass✅ FPR < 5% target               |

---

### **MODUŁ 6: REPORT GENERATOR**

| Step   | Task                                        | Opis / Wymagany Rezultat                                                                                                                                                                                                                                                                                                                                                                            | Weryfikacja                                                     |
| ------ | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| **30** | **Report Template: Responsible Disclosure** | Utworzenie `app/report/templates/disclosure.md`:`markdown``# Security Vulnerability Report``**Product**: {product_name}``**Version**: {version}``**Component**: {component}``**CVE ID**: {cve_id} (upstream)``## Vulnerability Summary``{summary}``## Attack Vector``{attack_scenario}``## Proof of Concept``{poc_if_available}``## Remediation``Upgrade {component} to version {fixed_version}```` | ✅ Template renderuje poprawnie✅ Wszystkie placeholders działają |
| **31** | **Report Generator: JSON Output**           | Implementacja `app/report/json_generator.py`:- Export do JSON z pełnymi detalami- Schema validation- Pretty print option                                                                                                                                                                                                                                                                            | ✅ Valid JSON output✅ Schema validated                           |
| **32** | **Report Generator: HTML Output**           | Implementacja `app/report/html_generator.py`:- HTML template z CSS- Severity color coding- Tabele z sortowaniem                                                                                                                                                                                                                                                                                     | ✅ HTML renderuje w przeglądarce✅ Responsive design              |
| **33** | **Report Generator: CLI Summary**           | Implementacja `app/report/cli_formatter.py`:- Kolorowy output (rich library)- Tabela z HIGH priority vulns- Statistics summary                                                                                                                                                                                                                                                                      | ✅ CLI output czytelny✅ Colors działają                          |

---

### **MODUŁ 7: API & ORCHESTRATION (Future - odkładamy na później)**

| Step   | Task                                | Opis / Wymagany Rezultat                                                                                                                                                                                                                                                 | Weryfikacja                                                            |
| ------ | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| **34** | **FastAPI Application Setup**       | Utworzenie `app/api/main.py`:- Application lifecycle (startup/shutdown)- CORS configuration- Exception handlers- Health check endpoint                                                                                                                                   | ✅ `GET /health` zwraca 200✅ CORS headers poprawne                      |
| **35** | **API: Scan Initiation Endpoint**   | Implementacja `POST /api/v1/scan`:`python``@router.post("/scan")``async def initiate_scan(` `manifest: UploadFile,` `target_name: str,` `db: AsyncSession``) -> ScanResponse:` `# Parse manifest` `# Create ScanResult` `# Trigger async scan job` `# Return scan_id```` | ✅ Endpoint zwraca scan_id✅ File upload działa✅ Background task started |
| **36** | **API: Scan Status Endpoint**       | Implementacja `GET /api/v1/scan/{scan_id}/status`:- Zwraca status skanowania- Progress percentage- Estimated time remaining                                                                                                                                              | ✅ Status updates real-time✅ Progress accurate                          |
| **37** | **API: Results Retrieval Endpoint** | Implementacja `GET /api/v1/scan/{scan_id}/report`:- Query params: format (json/html/markdown)- Filtering: min_priority- Pagination support                                                                                                                               | ✅ All formats generowane✅ Filtering działa                             |
| **38** | **Background Task Orchestrator**    | Implementacja `app/scanner/orchestrator.py`:`python``async def run_scan_pipeline(scan_id: str):` `# 1. Parse dependencies` `# 2. Resolve CVEs` `# 3. Apply heuristics` `# 4. Decision engine` `# 5. Generate report` `# 6. Update DB````                                 | ✅ Pipeline wykonuje się end-to-end✅ Errors handled gracefully          |
| **39** | **Logging & Monitoring Setup**      | Implementacja `app/core/logging_config.py`:- Structured logging (JSON)- Log levels per module- Request ID tracking- Performance metrics                                                                                                                                  | ✅ Logs zapisują się do pliku✅ JSON format valid                        |



### **MODUŁ 8: TESTING & QUALITY ASSURANCE**

| Step   | Task                                     | Opis / Wymagany Rezultat                                                                                                                                      | Weryfikacja                                             |
| ------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **40** | **Integration Test: Full Scan Pipeline** | Test `tests/integration/test_full_scan.py`:- Upload test manifest (requirements.txt)- Wait for scan completion- Verify results in DB- Check report generation | ✅ End-to-end test pass✅ No manual intervention needed   |
| **41** | **Performance Test: Large Manifest**     | Test z manifestem zawierającym 500+ dependencies:- Measure scan time- Check memory usage- Verify no timeouts                                                  | ✅ Scan completes < 5 min✅ Memory < 1GB                  |
| **42** | **Security Test: Input Validation**      | Testy bezpieczeństwa:- Malformed manifest files- Path traversal attempts- SQL injection in params- XSS in report output                                       | ✅ Wszystkie ataki zablokowane✅ No vulnerabilities found |
| **43** | **Code Coverage Report**                 | Generowanie coverage report:- Pytest-cov configuration- Target: > 80% coverage- Exclude: tests, migrations                                                    | ✅ Coverage >= 80%✅ Report wygenerowany                  |

---

### **MODUŁ 9: DEPLOYMENT & OPERATIONS**

| Step   | Task                                  | Opis / Wymagany Rezultat                                                                                                         | Weryfikacja                                              |
| ------ | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| **44** | **Dockerfile Optimization**           | Multi-stage build:- Stage 1: Dependencies installation- Stage 2: Runtime image- Non-root user- Health check                      | ✅ Image size < 500MB✅ Build time < 5 min                 |
| **45** | **Docker Compose: Production Config** | Utworzenie `docker-compose.prod.yml`:- Secrets management- Volume persistence- Network isolation- Resource limits                | ✅ Production deployment działa✅ Secrets nie w plain text |
| **47** | **Documentation: API Docs**           | Auto-generated OpenAPI docs:- FastAPI `/docs` endpoint- Request/response examples- Authentication guide                          | ✅ Swagger UI accessible✅ All endpoints documented        |
| **48** | **Documentation: User Guide**         | Utworzenie `docs/user_guide.md`:- Installation instructions- Quick start guide- Configuration options- Troubleshooting           | ✅ Dokument kompletny✅ Screenshots included               |

---

## 📊 METRYKI SUKCESU

Po zakończeniu wszystkich tasków, projekt musi spełniać:

| Metryka                 | Cel                  | Pomiar                              |
| ----------------------- | -------------------- | ----------------------------------- |
| **Code Coverage**       | ≥ 80%                | pytest-cov                          |
| **False Positive Rate** | < 5%                 | Manual validation na 100 CVE sample |
| **Scan Performance**    | < 5 min dla 500 deps | Performance tests                   |
| **API Response Time**   | < 2s dla GET /report | Load testing                        |
| **Documentation**       | 100% endpoints       | OpenAPI completeness                |

---

## 🔄 AKTUALIZACJE BOT STATUS LOG

Po każdym ukończonym tasku, bot aktualizuje:

```json
{
    "progress_log": [
        {
            "step": 1,
            "task": "Project Setup & Repository",
            "description": "Created Git repository with Clean Architecture folder structure",
            "timestamp": "2026-01-12T10:00:00Z",
            "status": "COMPLETE",
            "verification": "✅ All folders created, .gitignore configured"
        }
    ],
    "overall_progress_percent": 2.08
}
```

---

**GOTOWE DO IMPLEMENTACJI** 🚀