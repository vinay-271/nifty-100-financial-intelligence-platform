# Sprint 2 Retrospective — Financial Ratio Engine

## Sprint Overview

**Epic:** Epic 02 — Financial Ratio Engine
**Sprint:** Sprint 2 — Financial Metrics
**Duration:** Day 08–14
**Status:** ✅ Complete

## Sprint Objective

Build a modular Financial Ratio Engine capable of computing and validating financial KPIs across the N100 dataset. The sprint focused on profitability, leverage, efficiency, growth, CAGR, cash-flow, and capital-allocation metrics, while handling financial-data edge cases and maintaining a validated SQLite output.

---

## Delivered Features

### Profitability Ratios

Implemented:

- Net Profit Margin
- Operating Profit Margin
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)
- Return on Assets (ROA)

Special handling was added for invalid or zero denominators and negative equity situations.

### Leverage & Efficiency Ratios

Implemented:

- Debt-to-Equity
- Interest Coverage Ratio
- Asset Turnover
- Net Debt
- Debt-free handling
- High-leverage flag

The Financials-sector carve-out was implemented so that structurally high leverage in financial companies does not automatically trigger the standard high-leverage warning.

### CAGR & Growth Engine

Implemented CAGR calculations for:

- Revenue
- PAT
- EPS
- Book Value
- Stock Price

Supported growth windows include 3-year, 5-year, and 10-year calculations where sufficient historical data is available.

CAGR edge cases handled include:

- Positive → Positive
- Positive → Negative
- Negative → Positive
- Negative → Negative
- Zero base
- Insufficient historical data

### Cash-Flow KPIs

Implemented:

- Free Cash Flow
- CFO Quality Score
- CapEx Intensity
- FCF Conversion Rate
- Capital allocation pattern classification

Capital allocation patterns are classified using CFO, CFI, and CFF signs.

---

## Database Population

The complete ratio engine was integrated into the SQLite database.

The `financial_ratios` table contains:

- **1,164 company-year records**
- Computed profitability ratios
- Leverage and efficiency ratios
- Cash-flow metrics
- Growth/CAGR metrics
- EPS and book-value related metrics

Database validation confirmed the expected row population and no foreign-key violations.

---

## Testing

The complete test suite was executed at the end of Sprint 2.

### Final Test Result

```text
96 passed
0 failed
```
# Sprint 2 Summary: Financial Ratio Engine & Validation Pipeline

## 🧪 Test Suite Coverage

The comprehensive test suite successfully covered the following core logical components:
* Ratio calculations
* Cash-flow KPI calculations
* CAGR-related logic
* Ticker normalization
* Year normalization
* Data cleaning

> ⚠️ **Note:** There were 12 existing Pandas deprecation warnings related to `select_dtypes(include=["object"])`. These did not cause test failures and will be addressed in a future refactor.

---

## 🔍 Ratio Validation

A dedicated `RatioValidator` was implemented to compare calculated ROE and ROCE values against source/reference values.

* **Output File:** `data/output/ratio_edge_cases.csv`
* **Total Anomalies Identified:** 1,104

### Anomaly Breakdown by Metric

| Metric    | Anomalies |
| :-------- | :-------- |
| ROE       | 528       |
| ROCE      | 576       |
| **Total** | **1,104** |

### Validation Categories

| Category            | Count |
| :------------------ | :---- |
| Formula Discrepancy | 528   |
| Version Difference  | 384   |
| Data Source Issue   | 192   |

> 📌 **Architectural Decision:** These anomalies were intentionally retained for auditability instead of silently modifying the calculated ratio values. The source/reference ratios are treated as validation inputs, while the ratio-engine calculations are used exclusively for analytics.

---

## 🧮 Important Formula Decisions

The ratio engine utilizes the following finalized formula implementations:

* **ROE (Return on Equity)**
  $$\text{Net Profit} / (\text{Equity Capital} + \text{Reserves}) \times 100$$
  * *Edge Case:* Returns `None` when the equity denominator is not valid.
* **ROCE (Return on Capital Employed)**
  $$\text{EBIT} / (\text{Equity} + \text{Reserves} + \text{Borrowings}) \times 100$$
* **Debt-to-Equity**
  $$\text{Borrowings} / (\text{Equity Capital} + \text{Reserves})$$
  * *Edge Case:* Debt-free companies are handled explicitly.
* **Interest Coverage**
  $$(\text{Operating Profit} + \text{Other Income}) / \text{Interest}$$
  * *Edge Case:* Returns `None` when interest expense is zero.
* **Asset Turnover**
  $$\text{Sales} / \text{Total Assets}$$
* **Free Cash Flow (FCF)**
  $$\text{Operating Activity} + \text{Investing Activity}$$
  * *Edge Case:* Negative FCF is allowed because it represents a valid financial condition rather than an invalid calculation.

---

## 🛠️ Edge Cases Handled

The sprint specifically addressed and mitigated errors for:
* Zero denominators
* Negative equity
* Debt-free companies
* High leverage
* Financial-sector leverage
* Zero CAGR base
* CAGR turnarounds
* Decline-to-loss situations
* Both-negative CAGR values
* Insufficient historical data
* Negative free cash flow
* ROE/ROCE source-data mismatches

### 🏦 Financials Sector Carve-Out
Financial companies were treated separately for leverage warnings because high leverage is structurally common in banks, NBFCs, and insurance companies.

* **Target Classification:** `Financials`
* **Rule:** The standard `Debt-to-Equity > 5` high-leverage warning is suppressed.
* **Verification:** Verified using financial-sector companies such as `AXISBANK`, where Debt-to-Equity can exceed 5 while the high-leverage flag remains `False`.

---

## 🚦 Day 14 Screener Validation

The final screening logic filtered companies based on the following criteria:
1. `ROE > 15%`
2. `Debt-to-Equity < 1`

* **Screener Output:** 38 companies
* **Sprint Requirement:** Between 15 and 50 companies

### **Result:**
✓ **Screener Validation Passed** (The resulting companies were reviewed and confirmed for general business relevance).

---

## 📊 Final Demonstration

A five-company financial ratio demonstration was generated from the `financial_ratios` table, covering:
* Net Profit Margin & Operating Profit Margin
* ROE & ROCE
* Debt-to-Equity & Interest Coverage
* Asset Turnover & Free Cash Flow
* Revenue CAGR, PAT CAGR, & EPS CAGR

* **Final Database Row Count:** 1,164 records
* **Sprint Requirement:** 1,100+ records (Requirement exceeded)

---

## 💡 Key Lessons Learned
* **Engine vs. Source Discrepancies:** Source-provided financial ratios cannot always be assumed to use the same calculation methodology as the analytics engine.
* **Sanitization:** Financial ratios require explicit denominator and sign handling to avoid misleading results.
* **Sector Nuance:** Financial-sector companies require a completely different interpretation of leverage metrics.
* **CAGR Hazards:** CAGR calculations require careful, customized treatment of negative and zero starting values.
* **Pipeline Isolation:** Separating calculation, validation, and database persistence makes the analytics pipeline significantly easier to audit.
* **Regression Protection:** Automated tests are essential for protecting volatile financial formulas against regressions.
* **Auditability over Silos:** Edge-case reporting is highly preferable to silently changing or discarding unusual financial values.

---

## 🚀 Sprint Outcome

Sprint 2 successfully delivered the core Financial Ratio Engine and its validation pipeline.

### Definition of Done
- [x] Financial ratio engine implemented
- [x] 1,100+ financial ratio records populated
- [x] Ratio edge cases handled
- [x] ROE validation implemented
- [x] ROCE validation implemented
- [x] Financials-sector leverage carve-out implemented
- [x] Automated tests passing
- [x] Screener validation completed
- [x] Ratio edge-case report generated
- [x] Five-company KPI demonstration completed
- [x] Sprint retrospective documented

### Final Status
**Sprint 2 — Financial Ratio Engine:** ✅ **COMPLETE**

