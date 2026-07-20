# N100 Financial Intelligence Platform

## 🚧 Project Status

**Current Sprint:** Sprint 1 – Data Foundation

**Progress**

- ✅ Day 1 – Environment Setup
- ✅ Day 2 – Excel Loader & Normalizer
- ⏳ Day 3 – Data Quality Validation
- ⏳ Day 4 – SQLite Database Schema
- ⏳ Day 5 – Full Data Load
- ⏳ Day 6 – Manual Data Review
- ⏳ Day 7 – Sprint Wrap-Up

## Features Implemented

- Generic Excel Loader
- Automatic Excel File Discovery
- Batch Loading of All Datasets
- Header Normalization
- Year Normalization
- Stock Ticker Normalization
- Structured Logging
- Environment-based Configuration
- Modular ETL Architecture
- 35+ Unit Tests using pytest

## Sprint 1 – Data Foundation

### Objectives

- Build a scalable ETL pipeline
- Load 12 Excel datasets
- Validate data quality
- Create SQLite data warehouse
- Generate audit reports

## Tech Stack

- Python 3.12
- Pandas
- NumPy
- SQLAlchemy
- OpenPyXL
- Pytest
- Loguru
- Rich
- Python-dotenv
- SQLite

## Sprint Progress

| Sprint                       | Status        |
| ---------------------------- | ------------- |
| Sprint 1 – Data Foundation   | 🟨 In Progress |
| Sprint 2 – Financial Metrics | ⏳ Pending     |
| Sprint 3 – Analytics Engine  | ⏳ Pending     |
| Sprint 4 – Dashboard & API   | ⏳ Pending     |


## Unit Testing

Implemented parameterized unit tests using pytest.

Current Test Coverage

- normalize_year() — 20 test cases
- normalize_ticker() — 15 test cases

Total: 35 Passing Tests
