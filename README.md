# N100 Financial Intelligence Platform

A modular financial analytics platform for the Nifty 100 universe. The platform ingests, cleans, validates, stores, and analyzes financial data through a structured ETL pipeline, SQLite data warehouse, analytics engines, a Streamlit dashboard, generated financial reports, and a FastAPI REST API.

---

## Project Status

**Final submission status:** Complete

The platform covers the complete workflow from raw financial datasets through data quality validation, financial analytics, screening, peer analysis, valuation, clustering, portfolio analytics, company tearsheets, REST API access, dashboard visualization, automated testing, and documentation.

### Final QA Snapshot

```text
Companies analyzed:              92
Cluster count:                    5
Company tearsheets generated:    92
Automated tests:                 210 passed
Test failures:                    0
Test warnings:                  25
API performance test:          PASS
API test requests:              10
API performance wall time:   2.589 sec
```

The warnings are non-fatal. They are primarily dependency/API deprecation warnings, NumPy edge-case warnings in composite-score tests, and a Pandas compatibility warning.

---

# Features

## ETL Pipeline

- Generic Excel loader
- Automatic Excel file discovery
- Batch loading of financial datasets
- Header normalization
- Year normalization
- Stock ticker normalization
- Numeric data cleaning
- Missing-value normalization
- Duplicate business-record removal
- Structured logging
- Environment-based configuration

### Pipeline

```text
Raw Excel Datasets
       |
       v
Excel Loader
       |
       v
Data Cleaner / Normaliser
       |
       v
Data Quality Validator
       |
       v
SQLite Data Warehouse
       |
       +-----------------------------+
       |                             |
       v                             v
Financial Analytics             Reporting / API
```

---

# Data Quality Validation

The ETL validation layer implements 16 data-quality rules:

- DQ-01 Primary Key Uniqueness
- DQ-02 Company-Year Uniqueness
- DQ-03 Foreign Key Integrity
- DQ-04 Balance Sheet Validation
- DQ-05 Operating Profit Margin Cross-check
- DQ-06 Sales Validation
- DQ-07 Cash Flow Validation
- DQ-08 Tax Percentage Validation
- DQ-09 Dividend Payout Validation
- DQ-10 URL Validation
- DQ-11 EPS Validation
- DQ-12 Company Coverage
- DQ-13 Year Coverage
- DQ-14 Duplicate Business Records
- DQ-15 Missing Critical Fields
- DQ-16 Numeric Sanity Checks

---

# Financial Analytics

## Profitability

- Net Profit Margin
- Operating Profit Margin
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)
- Return on Assets (ROA)

## Leverage & Efficiency

- Debt-to-Equity Ratio
- Interest Coverage Ratio
- Asset Turnover
- High-Leverage Flag
- Debt-Free Classification
- Debt-to-Equity trend

## Growth

- Revenue CAGR
- PAT CAGR
- EPS CAGR
- Book Value CAGR
- Stock Price CAGR
- 3-year Revenue CAGR

## Cash Flow

- Free Cash Flow
- Cash From Operations
- Capex
- FCF CAGR
- CFO/PAT analysis
- Cash-flow quality indicators
- Capital-allocation patterns

## Composite Quality Score

Companies are evaluated using a weighted composite quality model covering:

- Profitability
- Cash Quality
- Growth
- Leverage

The scoring engine includes winsorisation, normalization, metric direction handling, sector-relative scoring, and composite scoring.

---

# Screening

The Nifty 100 Screener supports configurable financial filters and six predefined strategies:

1. Quality Compounder
2. Value Pick
3. Growth Accelerator
4. Dividend Champion
5. Debt-Free Blue Chip
6. Turnaround Watch

Screening results can be exported to CSV and Excel.

---

# Peer Analysis

The peer analytics engine provides percentile-based company comparisons across authoritative peer groups.

Supported metrics include:

- ROE
- ROCE
- Net Profit Margin
- Debt-to-Equity
- Free Cash Flow
- PAT CAGR
- Revenue CAGR
- EPS CAGR
- Interest Coverage
- Asset Turnover

The platform also provides peer comparison exports and radar-chart visualization.

---

# Valuation Analysis

The valuation engine evaluates the latest available market valuation data.

### Metrics

- P/E
- P/B
- EV/EBITDA
- FCF Yield
- Five-year median P/E
- P/E versus sector median

### Valuation Flags

Companies are classified using sector-relative P/E:

- **Caution** — P/E > 1.5× sector median
- **Discount** — P/E < 0.7× sector median
- **Fair** — otherwise

Generated outputs include:

```text
output/valuation_summary.xlsx
output/valuation_flags.csv
```

The valuation summary contains 92 companies.

---

# Clustering & Portfolio Intelligence

The platform includes an unsupervised KMeans-based company clustering workflow.

### Clustering features

- Return on Equity
- Debt-to-Equity
- Revenue CAGR (5Y)
- Free Cash Flow CAGR (5Y)
- Operating Profit Margin

Missing feature values are handled using sector-median imputation before clustering.

### Final clusters

The final five clusters are:

- Core / Balanced Businesses — 64 companies
- Highly Leveraged — 13 companies
- High-Margin Growth — 12 companies
- Extreme-ROE Businesses — 2 companies
- Exceptional Growth / Base Effect — 1 company

Cluster analysis also produces:

```text
output/cluster_labels.csv
output/cluster_profiles.csv
output/cluster_outliers.csv
output/portfolio_statistics.csv
reports/elbow_plot.png
reports/cluster_correlation_heatmap.png
```

The clustering analysis explicitly surfaces extreme observations instead of silently treating them as ordinary observations.

---

# Company Tear Sheets

The reporting layer generates a standardized two-page PDF tearsheet for each company.

Final generation result:

```text
Companies: 92
Generated tearsheets: 92
```

Tearsheet files are stored under:

```text
output/tearsheets/
```

The tearsheets combine company information, financial KPIs, historical financial data, valuation information, charts, and analytical commentary.

---

# Streamlit Dashboard

The project includes an eight-page Streamlit dashboard.

## 1. Home

Provides:

- Nifty 100 company coverage
- Sector coverage
- Latest financial period
- Company universe
- Sector distribution

## 2. Company Profile

Provides:

- Company overview
- Financial ratios
- Profit & Loss
- Balance Sheet
- Cash Flow
- Valuation data
- Historical financial charts

## 3. Screener

Provides:

- Six predefined screening strategies
- Composite quality scores
- Screening results
- Export functionality

## 4. Peer Comparison

Provides:

- Peer-group selection
- Percentile rankings
- Company comparison
- Radar-chart visualization
- Detailed peer data

## 5. Trend Analysis

Provides:

- Financial ratio trends
- Profitability trends
- EPS trends
- Revenue/PAT growth
- Five-year CAGR summary

## 6. Sector Analysis

Provides:

- Sector composition
- Sector weights
- Industry distribution
- Sector company lists
- Sector financial averages
- Company-level metric comparisons

## 7. Capital Allocation

Provides:

- Operating cash flow
- Investing cash flow
- Financing cash flow
- Free cash flow
- Capex
- Debt analysis
- Cash-flow trends

## 8. Reports

Provides access to generated analytical artifacts, including screener, peer, radar, and other downloadable reports.

---

# REST API

A FastAPI REST API exposes the major analytical capabilities of the platform.

### API service

```text
src/api/main.py
```

### Main endpoint groups

```text
/health
/companies
/screener
/sectors
/peers
/valuation
/portfolio
/documents
```

Examples:

```text
GET /health
GET /companies/{company_id}
GET /companies/{company_id}/profit-loss
GET /companies/{company_id}/balance-sheet
GET /companies/{company_id}/cash-flow
GET /companies/{company_id}/ratios

GET /screener/presets
GET /screener/preset/{preset_name}

GET /peers/{company_id}

GET /sectors
GET /sectors/{sector}

GET /valuation/flags
GET /valuation/summary

GET /portfolio/statistics
GET /portfolio/clusters
```

The API also handles invalid company identifiers with appropriate HTTP errors.

The generated OpenAPI specification is included with the submission as:

```text
docs/openapi.json
```

---

# API Testing & Performance

The project contains a dedicated API regression test suite under:

```text
tests/api/
```

The complete automated test suite currently reports:

```text
210 passed
25 warnings
0 failures
```

An API performance test was also executed using 10 requests:

```text
Requests:       10
Successful:     10
Total wall time: 2.589 sec
Average:         2.472 sec
Maximum:         2.585 sec
Minimum:         2.291 sec
PASS:            True
```

The performance evidence is included as:

```text
reports/api_performance.txt
```

---

# NLP / Analytical Commentary

The project includes an NLP layer for parsing company analysis and generating structured pros/cons information.

Relevant modules:

```text
src/nlp/parser.py
src/nlp/pros_cons_generator.py
```

Generated analytical outputs include:

```text
output/analysis_parsed.csv
output/pros_cons_generated.csv
output/parse_failures.csv
```

---

# Project Architecture

```text
Raw Excel Datasets
        |
        v
   Excel Loader
        |
        v
 Data Cleaner / Normaliser
        |
        v
Data Quality Validator
        |
        v
 SQLite Data Warehouse
        |
        +-------------------------------+
        |               |               |
        v               v               v
Financial Ratios    Cash Flow       Market Data
Engine              KPIs
        |               |               |
        +-------+-------+---------------+
                |
                v
          Analytics Layer
                |
       +--------+---------+----------------+
       |        |         |                |
       v        v         v                v
   Screener   Peer    Valuation       Clustering
    Engine   Engine    Engine          Analysis
       |        |         |                |
       +--------+---------+----------------+
                         |
             +-----------+-----------+
             |                       |
             v                       v
      Streamlit Dashboard       FastAPI REST API
             |                       |
             +-----------+-----------+
                         |
                         v
                  Reports / PDFs
```

---

# Project Structure

The development repository is organized approximately as:

```text
n100/
|
├── config/
│   └── screener_config.yaml
|
├── data/
│   ├── raw/
│   └── processed/
|
├── db/
│   └── nifty100.db
|
├── output/
│   ├── screener_output.xlsx
│   ├── peer_comparison.xlsx
│   ├── valuation_summary.xlsx
│   ├── valuation_flags.csv
│   ├── cluster_labels.csv
│   ├── cluster_profiles.csv
│   ├── cluster_outliers.csv
│   ├── portfolio_statistics.csv
│   └── tearsheets/
|
├── reports/
│   ├── elbow_plot.png
│   ├── cluster_correlation_heatmap.png
│   └── api_performance.txt
|
├── scripts/
│   └── generate_analyst_guide.py
|
├── src/
│   ├── analytics/
│   ├── api/
│   ├── dashboard/
│   ├── etl/
│   ├── nlp/
│   ├── reports/
│   └── screener/
|
├── tests/
│   ├── analytics/
│   ├── api/
│   ├── etl/
│   └── screener/
|
├── docs/
│   ├── analyst_guide.pdf
│   ├── openapi.json
│   └── data_dictionary.md
|
├── requirements.txt
└── README.md
```

---

# Running the Project

Create and activate a Python 3.12 environment, then install dependencies:

```powershell
pip install -r requirements.txt
```

## Run the Streamlit dashboard

From the project root:

```powershell
streamlit run src/dashboard/app.py
```

## Run the FastAPI service

From the project root:

```powershell
uvicorn src.api.main:app --reload
```

The API is then available locally at:

```text
http://127.0.0.1:8000
```

The interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Run the test suite

```powershell
pytest -q
```

Expected current result:

```text
210 passed
25 warnings
```

## Generate the analyst guide

The ReportLab generator is stored at:

```text
scripts/generate_analyst_guide.py
```

Run:

```powershell
python scripts/generate_analyst_guide.py
```

This generates:

```text
docs/analyst_guide.pdf
```

---

# Generated Outputs

## ETL / Validation

Typical outputs include:

```text
load_audit.csv
validation_failures.csv
```

## Financial Analytics

```text
profitability_ratios.csv
financial_ratios_computed.csv
opm_edge_cases.csv
```

## Screening

```text
output/screener_output.xlsx
```

## Peer Analysis

```text
output/peer_comparison.xlsx
```

## Valuation

```text
output/valuation_summary.xlsx
output/valuation_flags.csv
```

## Cash Flow

```text
output/cashflow_intelligence.xlsx
output/capital_allocation_distribution.csv
output/pattern_changes.csv
```

## Clustering

```text
output/cluster_labels.csv
output/cluster_profiles.csv
output/cluster_outliers.csv
output/portfolio_statistics.csv
reports/elbow_plot.png
reports/cluster_correlation_heatmap.png
```

## NLP

```text
output/analysis_parsed.csv
output/pros_cons_generated.csv
output/parse_failures.csv
```

## Company Reports

```text
output/tearsheets/*.pdf
```

---

# Technology Stack

- Python 3.12
- Pandas
- NumPy
- SQLite
- OpenPyXL
- PyYAML
- Plotly
- Streamlit
- FastAPI
- Uvicorn
- Scikit-learn
- Seaborn
- ReportLab
- Pytest
- Loguru
- Rich
- Python-dotenv

---

# Final Project Deliverables

The final submission is organized into five required categories:

```text
01_Source_Code/
02_Datasets/
03_Documentation/
04_PPT_Slides/
05_Demo_Video/
```

The source-code and documentation packages are complete.

The PPT/Slides and Demo Video folders are reserved for presentation/video deliverables if required by the submission authority. They are not represented as completed artifacts in this repository.

---

# Known Data Edge Cases

The source dataset contains limited missing or unusual values for some companies.

Examples identified during analytics QA include:

- ABB has no sector mapping, so sector-relative P/E comparison is unavailable.
- ATGL has missing free cash flow, so FCF Yield is unavailable.
- Some companies have extreme ROE values caused by very small equity bases or financial-structure effects.
- JIOFIN contains a very large revenue CAGR because of its short historical availability/base effect.

These cases are handled without crashing the analytics pipeline. The clustering workflow also reports outlier observations rather than silently removing them.

---

# Reproducibility

The project is designed so that the main analytical workflows can be reproduced from the supplied source code, configuration, datasets, and database.

For a clean environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

Then start either the dashboard or API as described above.

---

# Final QA

```text
Nifty 100 companies analyzed:       92
Clusters:                             5
Company tearsheets:                  92
Automated tests:                     210 passed
Test failures:                         0
API regression tests:                PASS
API performance test:                PASS
OpenAPI specification:               Generated
Analyst guide:                       Generated
```

---

# License / Submission Note

This project is intended as an academic/internship financial analytics platform. Financial outputs are analytical results generated from the supplied dataset and should not be interpreted as investment advice.
