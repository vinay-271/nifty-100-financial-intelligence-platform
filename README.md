# N100 Financial Intelligence Platform

A modular financial analytics platform that ingests, cleans, validates, and analyzes Nifty 100 company financial data using a scalable ETL pipeline and SQLite data warehouse.

---

# 🚀 Project Status

**Current Sprint:** Sprint 2 – Financial Metrics

## Progress

### Sprint 1 – Data Foundation ✅

- ✅ Day 1 – Environment Setup
- ✅ Day 2 – Excel Loader & Normalizer
- ✅ Day 3 – Data Quality Validation (DQ-01 to DQ-16)
- ✅ Day 4 – SQLite Database Schema
- ✅ Day 5 – Full Data Load (12 datasets)
- ✅ Day 6 – Manual Data Review
- ✅ Day 7 – Sprint Wrap-Up

### Sprint 2 – Financial Metrics 🚧

- ✅ Day 8 – Profitability Ratio Engine
- ✅ Day 9 – Leverage & Efficiency Ratio Engine
- ✅ Day 10 – Growth & CAGR Engine
- ⏳ Day 11 – Cash Flow KPI Engine
- ⏳ Day 12 – Financial Ratio Database Update
- ⏳ Day 13 – KPI Validation & Review
- ⏳ Day 14 – Sprint Wrap-Up

---

# Features Implemented

## ETL Pipeline

- Generic Excel Loader
- Automatic Excel File Discovery
- Batch Loading of 12 Excel datasets
- Header Normalization
- Year Normalization
- Stock Ticker Normalization
- Numeric Data Cleaning
- Missing Value Normalization
- Duplicate Business Record Removal
- Structured Logging
- Environment-based Configuration

---

## Data Warehouse

- SQLite Database
- 11 Relational Tables
- Primary & Foreign Key Constraints
- Foreign Key Validation
- Load Audit Report Generation
- Validation Failure Report Generation

---

## Data Quality Validation

Implemented all **16 Data Quality Rules**

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

## Financial Analytics Engine

### Profitability Metrics

- Net Profit Margin
- Operating Profit Margin
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)
- Return on Assets (ROA)

### Leverage & Efficiency Metrics

- Debt-to-Equity Ratio
- Interest Coverage Ratio
- Asset Turnover Ratio
- High Leverage Flag
- Debt-Free Label

### Growth Analytics

- Generic CAGR Calculator
- Sales CAGR
- Profit CAGR
- EPS CAGR
- Book Value CAGR
- Stock Price CAGR

---

## Reports Generated

- load_audit.csv
- validation_failures.csv
- profitability_ratios.csv
- financial_ratios_computed.csv
- opm_edge_cases.csv

---

# Project Architecture

```
Excel Files
      │
      ▼
 Excel Loader
      │
      ▼
 Data Cleaner
      │
      ▼
 Data Validator
      │
      ▼
 SQLite Database
      │
      ▼
 Ratio Engine
      ├── Profitability
      ├── Leverage
      └── Growth
      │
      ▼
 Computed KPI Reports
```

---

# Tech Stack

- Python 3.12
- Pandas
- NumPy
- SQLite
- OpenPyXL
- Pytest
- Loguru
- Rich
- Python-dotenv

---

# Sprint Progress

| Sprint                         | Status                  |
| ------------------------------ | ----------------------- |
| ✅ Sprint 1 – Data Foundation   | Complete                |
| 🟨 Sprint 2 – Financial Metrics | In Progress (Day 10/14) |
| ⏳ Sprint 3 – Analytics Engine  | Pending                 |
| ⏳ Sprint 4 – Dashboard & API   | Pending                 |

---

# Testing

Implemented comprehensive automated testing using **pytest**.

## Current Test Coverage

### ETL

- normalize_year()
- normalize_ticker()
- Data Cleaner

### Financial Analytics

- Profitability Ratio Functions
- Leverage & Efficiency Ratio Functions

## Current Status

- **79+ automated tests passing**
- Data Quality Validation (DQ-01 to DQ-16)
- Manual validation completed for:
  - ABB
  - AXISBANK
  - TCS
  - RELIANCE
  - ADANIENSOL

---

# Current Outputs

- SQLite database with 11 populated tables
- Zero foreign key violations
- Complete ETL pipeline
- Financial KPI computation engine
- Automated validation reports
- Exploratory SQL queries
- Unit-tested analytics library

---

# Next Milestones

- Cash Flow KPI Engine
- Financial Ratio Database Update
- KPI Validation & Benchmarking
- Analytics Dashboard
- REST API
- Interactive Financial Intelligence Platform
