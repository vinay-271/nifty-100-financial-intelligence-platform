# N100 Financial Intelligence Platform

A modular financial analytics platform for the Nifty 100 universe that ingests, cleans, validates, stores, and analyzes financial data through a structured ETL pipeline, SQLite data warehouse, analytics engines, and interactive Streamlit dashboard.

---

# 🚀 Project Status

**Current Sprint:** Sprint 4 – Dashboard & Valuation
**Status:** ✅ Complete

The platform currently covers the complete data pipeline from raw financial datasets through analytics, screening, valuation, and interactive visualization.

---

# Features

## ETL Pipeline

- Generic Excel Loader
- Automatic Excel File Discovery
- Batch loading of financial datasets
- Header normalization
- Year normalization
- Stock ticker normalization
- Numeric data cleaning
- Missing value normalization
- Duplicate business record removal
- Structured logging
- Environment-based configuration

---

## Data Quality Validation

Implemented **16 Data Quality Rules**:

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
- High Leverage Flag
- Debt-Free Classification

## Growth

- Revenue CAGR
- PAT CAGR
- EPS CAGR
- Book Value CAGR
- Stock Price CAGR

## Cash Flow

- Free Cash Flow
- Cash From Operations
- Capex
- FCF CAGR
- CFO/PAT analysis
- Cash-flow quality indicators

## Composite Quality Score

Companies are evaluated using a weighted composite quality model covering:

- Profitability
- Cash Quality
- Growth
- Leverage

The scoring engine includes winsorisation, normalization, metric direction handling, and composite scoring.

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

The peer analytics engine provides percentile-based company comparisons across peer groups.

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

The dashboard also provides interactive peer comparison and radar-chart visualization.

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

Generated outputs:

```text
output/valuation_summary.xlsx
output/valuation_flags.csv
````

The valuation summary contains 92 companies.

---

# 📊 Streamlit Dashboard

The project includes an interactive eight-page Streamlit dashboard.

## 1. Home

Provides:

* Nifty 100 company coverage
* Sector coverage
* Latest financial period
* Company universe
* Sector distribution

## 2. Company Profile

Provides:

* Company overview
* Financial ratios
* Profit & Loss
* Balance Sheet
* Cash Flow
* Valuation data
* Historical financial charts

## 3. Screener

Provides:

* Six predefined screening strategies
* Composite quality scores
* Screening results
* CSV export

## 4. Peer Comparison

Provides:

* Peer-group selection
* Percentile rankings
* Company comparison
* Radar-chart visualization
* Detailed peer data

## 5. Trend Analysis

Provides:

* Financial ratio trends
* Profitability trends
* EPS trends
* Revenue/PAT growth
* Five-year CAGR summary

## 6. Sector Analysis

Provides:

* Sector composition
* Sector weights
* Industry distribution
* Sector company lists
* Sector financial averages
* Company-level metric comparisons

## 7. Capital Allocation

Provides:

* Operating cash flow
* Investing cash flow
* Financing cash flow
* Free cash flow
* Capex
* Debt analysis
* Cash-flow trends

## 8. Reports

Provides access to generated:

* Screener reports
* Peer comparison reports
* Radar charts
* Downloadable analytics artifacts

---

# Project Architecture

```text
Raw Excel Datasets
        │
        ▼
   Excel Loader
        │
        ▼
   Data Cleaner
        │
        ▼
 Data Quality Validator
        │
        ▼
 SQLite Data Warehouse
        │
        ├───────────────┐
        ▼               ▼
 Financial Ratio    Cash Flow
     Engine            KPIs
        │               │
        └───────┬───────┘
                ▼
        Analytics Layer
                │
       ┌────────┼─────────┐
       ▼        ▼         ▼
   Screener   Peer     Valuation
    Engine   Engine      Engine
       │        │         │
       └────────┼─────────┘
                ▼
        Streamlit Dashboard
                │
       ┌────────┼─────────────┐
       ▼        ▼             ▼
    Profiles  Analytics     Reports
```

---

# Project Structure

```text
n100/
│
├── config/
│   └── screener_config.yaml
│
├── data/
│   ├── raw/
│   └── processed/
│
├── db/
│   └── nifty100.db
│
├── output/
│   ├── screener_output.xlsx
│   ├── peer_comparison.xlsx
│   ├── valuation_summary.xlsx
│   └── valuation_flags.csv
│
├── reports/
│   ├── nifty100_screener.xlsx
│   └── radar_charts/
│
├── src/
│   ├── analytics/
│   ├── dashboard/
│   ├── etl/
│   └── screener/
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

# Running the Dashboard

Create/activate the Python environment and install dependencies:

```powershell
pip install -r requirements.txt
```

Run the Streamlit application from the project root:

```powershell
streamlit run src/dashboard/app.py
```

The dashboard opens with the eight available analytics pages in the sidebar.

---

# Running the Tests

Run the complete test suite:

```powershell
pytest -q
```

Current regression status:

```text
189 passed
22 warnings
```

The warnings are non-fatal and do not cause test failures.

---

# Generated Outputs

The platform generates several analytical artifacts.

### ETL / Validation

```text
load_audit.csv
validation_failures.csv
```

### Financial Analytics

```text
profitability_ratios.csv
financial_ratios_computed.csv
opm_edge_cases.csv
```

### Screening

```text
output/screener_output.xlsx
reports/nifty100_screener.xlsx
```

### Peer Analysis

```text
output/peer_comparison.xlsx
```

### Valuation

```text
output/valuation_summary.xlsx
output/valuation_flags.csv
```

### Radar Charts

```text
reports/radar_charts/
```

---

# Technology Stack

* Python 3.12
* Pandas
* NumPy
* SQLite
* OpenPyXL
* PyYAML
* Plotly
* Streamlit
* Pytest
* Loguru
* Rich
* Python-dotenv

---

# Sprint Progress

| Sprint                               | Status     |
| ------------------------------------ | ---------- |
| Sprint 1 – Data Foundation           | ✅ Complete |
| Sprint 2 – Financial Metrics         | ✅ Complete |
| Sprint 3 – Analytics Engine          | ✅ Complete |
| Sprint 4 – Dashboard, Valuation & QA | ✅ Complete |
| Sprint 5                             | ⏳ Pending  |

---

# Sprint 4 Completion

Sprint 4 delivered:

* Eight functional Streamlit dashboard screens
* Interactive company financial profiles
* Six preset screeners
* Composite quality scoring
* Peer percentile comparison
* Peer radar charts
* Historical trend analysis
* Sector analytics
* Capital allocation analysis
* Reports and downloadable outputs
* Valuation engine
* Sector-relative valuation flags
* 92-company valuation summary
* Integration and regression testing
* Partial-data handling
* Performance validation

### QA Results

```text
Automated tests: 189 passed
Regression runtime: ~15 seconds
Profile database load: ~0.007 seconds
Valuation companies: 92
Dashboard screens: 8
```

---

# Known Data Edge Cases

The source dataset contains limited missing values for some companies.

Examples identified during valuation QA:

* ABB has no sector mapping, so sector-relative P/E comparison is unavailable.
* ATGL has missing free cash flow, so FCF Yield is unavailable.

These cases are handled without crashing the analytics pipeline or dashboard.

---
