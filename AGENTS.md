# Agent Instructions

## Environment & Developer Commands
- **Python Virtual Environment**: Windows environment requires invoking `.venv\Scripts\` binaries directly:
  - Run tests: `.venv\Scripts\pytest.exe`
  - Single test file: `.venv\Scripts\pytest.exe tests/analytics/test_ratios.py`
  - Test coverage: `.venv\Scripts\pytest.exe --cov=src --cov-report=term-missing`
  - Linting & Formatting: `.venv\Scripts\flake8.exe src tests` / `.venv\Scripts\black.exe src tests`
- **Runner Scripts**: Always run scripts as Python modules with `-m` from the repository root:
  - Data Cleaning: `.venv\Scripts\python.exe -m src.run_cleaner`
  - Database Loading: `.venv\Scripts\python.exe -m src.main`
  - Data Quality Validation: `.venv\Scripts\python.exe -m src.run_validator`
  - Ratio & KPI Engine: `.venv\Scripts\python.exe -m src.run_ratio_engine`
  - Ratio Validation: `.venv\Scripts\python.exe -m src.run_ratio_validator`

## Pipeline Execution Flow
1. `data/raw/{core,supporting}/*.xlsx` — Source Excel financial datasets.
2. `src.run_cleaner` — Normalizes headers, years, tickers; outputs to `data/cleaned/*.csv`.
3. `src.main` — Builds SQLite schema (`db/schema.sql`) and populates `db/nifty100.db` (11 tables with foreign keys enabled).
4. `src.run_validator` — Executes 16 Data Quality rules (DQ-01 to DQ-16); writes `data/output/validation_failures.csv`.
5. `src.run_ratio_engine` — Computes 50+ financial KPIs into SQLite `financial_ratios` table and exports CSV reports to `data/output/`.
6. `src.run_ratio_validator` — Validates calculated financial ratios in SQLite.

## Domain & Repository Conventions
- **Financials Sector Exception**: High leverage flag (`D/E > 5`) is suppressed for the 19 companies in the Financials sector (banks/NBFCs).
- **Debt-Free Handling**: Zero borrowings set `debt_to_equity = 0`, `interest_coverage = None`, and `icr_label = 'Debt Free'`.
- **CAGR Edge Cases**: Non-positive ranges or turnarounds yield `None` with categorical flags (`DECLINE_TO_LOSS`, `TURNAROUND`, `BOTH_NEGATIVE`, `ZERO_BASE`, `INSUFFICIENT`).
- **Configuration & Paths**: Use `src/constants.py` (`PROJECT_ROOT`, `DB_FILE`, `DATA_DIR`) and `src/config.py` (`.env` overrides) rather than hardcoding paths.
