# N100 Financial Intelligence Platform — Data Dictionary

This document describes the primary SQLite data warehouse tables used by the N100 Financial Intelligence Platform.

The database contains company master data, annual financial statements, analytical metrics, market data, peer mappings, sector mappings, and derived analytical outputs.

---

## Database

```text
db/nifty100.db
```

Primary entity key:

```text
company_id
```

Most company-level tables use `company_id` as their logical foreign key to the company master table.

---

## Core Tables

| Table | Primary Key | Foreign Key | Description |
|---|---|---|---|
| `companies` | `id` | — | Company master information, identifiers, names, logos and related metadata |
| `profitandloss` | `id` | `company_id` | Annual profit and loss statements |
| `balancesheet` | `id` | `company_id` | Annual balance sheet information |
| `cashflow` | `id` | `company_id` | Annual operating, investing and financing cash-flow information |
| `analysis` | `id` | `company_id` | Source financial-analysis metrics and qualitative/company analysis |
| `documents` | `id` | `company_id` | Company annual-report and document metadata |
| `prosandcons` | `id` | `company_id` | Company strengths, weaknesses and qualitative observations |
| `financial_ratios` | `id` | `company_id` | Derived financial ratios and growth metrics |
| `market_cap` | `id` | `company_id` | Market capitalization and related valuation data |
| `peer_groups` | `id` | `company_id` | Authoritative peer-company mapping |
| `sectors` | `id` | — | Company sector, industry and market-cap classification |
| `stock_prices` | `id` | `company_id` | Historical stock-price data |

---

# 1. companies

Company master table.

Typical fields include:

| Field | Description |
|---|---|
| `id` | Company/ticker identifier |
| `company_name` | Full company name |
| `company_logo` | Company logo URL, where available |
| `chart_link` | External chart/reference URL, where available |

The company identifier is used throughout the analytical pipeline to join company-level records.

---

# 2. profitandloss

Annual income-statement data.

Typical fields include:

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `year` | Financial reporting period |
| `sales` | Revenue/sales |
| `expenses` | Total operating/other expenses |
| `operating_profit` | Operating profit |
| `opm_percentage` | Operating profit margin |
| `other_income` | Other income |
| `interest` | Interest expense |
| `depreciation` | Depreciation |
| `profit_before_tax` | Profit before tax |
| `tax` | Tax expense |
| `net_profit` | Net profit |
| `eps` | Earnings per share |
| `dividend_payout` | Dividend payout |

Exact available fields depend on the source dataset.

---

# 3. balancesheet

Annual balance-sheet data.

Typical fields include:

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `year` | Financial reporting period |
| `equity_capital` | Equity share capital |
| `reserves` | Reserves |
| `borrowings` | Total borrowings |
| `other_liabilities` | Other liabilities |
| `total_liabilities` | Total liabilities |
| `fixed_assets` | Fixed assets |
| `other_assets` | Other assets |
| `total_assets` | Total assets |

The table is also used by validation rules for balance-sheet consistency checks.

---

# 4. cashflow

Annual cash-flow data.

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `year` | Financial reporting period |
| `operating_activity` | Cash flow from operating activities |
| `investing_activity` | Cash flow from investing activities |
| `financing_activity` | Cash flow from financing activities |
| `net_cash` | Net change in cash |
| `capex` | Capital expenditure, where available |
| `free_cash_flow` | Free cash flow, where available |

The cash-flow analytics layer derives FCF quality, CFO/PAT relationships, FCF CAGR and capital-allocation patterns.

---

# 5. analysis

Source analytical/company-analysis information.

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `year` | Reporting period, where applicable |
| `content` / analysis fields | Source analysis information |

This table feeds the NLP parsing and pros/cons generation workflow where applicable.

---

# 6. documents

Company document metadata.

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `document` / URL fields | Annual-report and document references |

Documents are exposed through the document API where available.

---

# 7. prosandcons

Qualitative company strengths and weaknesses.

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `pros` | Positive observations |
| `cons` | Negative/risk observations |

Generated NLP outputs are also exported separately to:

```text
output/pros_cons_generated.csv
```

---

# 8. financial_ratios

Central derived financial-metrics table.

Key fields include:

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `year` | Financial reporting period |
| `net_profit_margin_pct` | Net profit margin (%) |
| `operating_profit_margin_pct` | Operating profit margin (%) |
| `return_on_equity_pct` | Return on equity (%) |
| `return_on_capital_employed_pct` | ROCE (%) |
| `debt_to_equity` | Debt-to-equity ratio |
| `interest_coverage` | Interest coverage ratio |
| `asset_turnover` | Asset turnover |
| `free_cash_flow_cr` | Free cash flow in crore |
| `capex_cr` | Capital expenditure in crore |
| `earnings_per_share` | EPS |
| `book_value_per_share` | Book value per share |
| `dividend_payout_ratio_pct` | Dividend payout ratio (%) |
| `total_debt_cr` | Total debt in crore |
| `cash_from_operations_cr` | Cash from operations in crore |
| `revenue_cagr_5yr` | Five-year revenue CAGR (%) |
| `pat_cagr_5yr` | Five-year PAT CAGR (%) |
| `eps_cagr_5yr` | Five-year EPS CAGR (%) |
| `composite_quality_score` | Composite quality score |

Additional derived metrics may be calculated by the screener and analytics engines, including 3-year revenue CAGR, FCF CAGR, CFO/PAT ratio and debt-to-equity trend.

---

# 9. market_cap

Market capitalization and valuation inputs.

Typical analytical fields include:

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `year` / date | Market-data period |
| `market_cap_cr` | Market capitalization in crore |
| `pe_ratio` | Price-to-earnings ratio |
| `pb_ratio` | Price-to-book ratio |
| `ev_ebitda` | EV/EBITDA |
| `dividend_yield_pct` | Dividend yield (%) |

The valuation engine uses these values together with financial ratios and sector information.

---

# 10. peer_groups

Authoritative peer-company mapping.

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `peer_group_name` | Assigned peer group |
| `metric` | Peer metric |
| `value` | Metric value |
| `percentile_rank` | Percentile ranking |
| `year` | Reporting period |

Peer percentile rankings are generated by the peer analytics engine.

---

# 11. sectors

Sector and industry classification.

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `sector` | Company sector |
| `industry` | Company industry |
| `weight_pct` | Nifty universe weight (%) |
| `market_cap_category` | Market-cap classification |

This table supports sector analysis and sector-relative valuation comparisons.

---

# 12. stock_prices

Historical market-price data.

| Field | Description |
|---|---|
| `id` | Record identifier |
| `company_id` | Company identifier |
| `date` | Trading date |
| `open` | Opening price |
| `high` | High price |
| `low` | Low price |
| `close` | Closing price |
| `volume` | Trading volume |

Historical stock prices support market-performance and CAGR analysis where applicable.

---

# Derived Analytical Outputs

The platform also creates analytical artifacts outside the core database.

## Screener

```text
output/screener_output.xlsx
```

Contains results for six configured screening strategies.

## Peer Analysis

```text
output/peer_comparison.xlsx
```

Contains peer comparisons and percentile-based analysis.

## Valuation

```text
output/valuation_summary.xlsx
output/valuation_flags.csv
```

## Clustering

```text
output/cluster_labels.csv
output/cluster_profiles.csv
output/cluster_outliers.csv
output/portfolio_statistics.csv
```

Clustering uses:

- ROE
- Debt-to-Equity
- Revenue CAGR (5Y)
- FCF CAGR (5Y)
- Operating Profit Margin

Missing feature values are imputed using sector medians before KMeans clustering.

## Cash Flow

```text
output/cashflow_intelligence.xlsx
output/capital_allocation_distribution.csv
output/pattern_changes.csv
```

## NLP

```text
output/analysis_parsed.csv
output/pros_cons_generated.csv
output/parse_failures.csv
```

## Company Tear Sheets

```text
output/tearsheets/*.pdf
```

One standardized PDF tearsheet is generated per company in the final 92-company universe.

---

# API Data Model

The FastAPI layer exposes analytical data through the following endpoint groups:

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

The API schema is documented in:

```text
docs/openapi.json
```

---

# Data Quality Notes

The source data contains some legitimate edge cases.

Examples observed during QA:

- Some companies may not have a sector mapping.
- Some companies may have missing free cash flow.
- Some companies have extreme ROE values because of very small equity bases or financial-structure effects.
- Some growth metrics can be extreme when a company has a short historical availability window or a very low starting base.

These values are not automatically discarded. Analytics modules handle missing values where possible and clustering analysis explicitly reports outlier observations.

---

# Units and Conventions

Unless otherwise specified:

- Monetary values are in **₹ crore**.
- Percentage fields use percentage units, e.g. `15.5` means 15.5%.
- CAGR fields are percentages.
- Ratios such as Debt-to-Equity are stored as numeric ratios.
- EPS and book value per share are per-share values in the source dataset.
- Financial years are represented using the source financial-period convention such as `Mar 2024` and may also contain `TTM` where applicable.

---

# Relationship Overview

```text
companies
   |
   +---- profitandloss
   +---- balancesheet
   +---- cashflow
   +---- analysis
   +---- documents
   +---- prosandcons
   +---- financial_ratios
   +---- market_cap
   +---- peer_groups
   +---- stock_prices

sectors
   |
   +---- company sector / industry classification

financial_ratios + market_cap + sectors
   |
   +---- screener
   +---- peer analysis
   +---- valuation
   +---- clustering
   +---- portfolio analytics
```
