-- ============================================================
-- N100 Financial Intelligence Platform
-- Exploratory SQL Queries
-- ============================================================

-- ============================================================
-- Q1. Total Companies
-- ============================================================

SELECT COUNT(*) AS total_companies
FROM companies;


-- ============================================================
-- Q2. Top 10 Companies by Market Capitalization (Latest Year)
-- ============================================================

SELECT
    company_id,
    market_cap_cr
FROM market_cap
WHERE year = (
    SELECT MAX(year)
    FROM market_cap
)
ORDER BY market_cap_cr DESC
LIMIT 10;


-- ============================================================
-- Q3. Top 10 Companies by Net Profit (Latest Financial Year)
-- ============================================================

SELECT
    company_id,
    year,
    net_profit
FROM profitandloss
WHERE year = (
    SELECT MAX(year)
    FROM profitandloss
)
ORDER BY net_profit DESC
LIMIT 10;


-- ============================================================
-- Q4. Top 10 Companies by Return on Equity (Latest Year)
-- ============================================================

SELECT
    company_id,
    year,
    return_on_equity_pct
FROM financial_ratios
WHERE year = (
    SELECT MAX(year)
    FROM financial_ratios
)
ORDER BY return_on_equity_pct DESC
LIMIT 10;


-- ============================================================
-- Q5. Top 10 Companies by Sales (Latest Year)
-- ============================================================

SELECT
    company_id,
    year,
    sales
FROM profitandloss
WHERE year = (
    SELECT MAX(year)
    FROM profitandloss
)
ORDER BY sales DESC
LIMIT 10;


-- ============================================================
-- Q6. Companies with Highest Debt-to-Equity Ratio
-- ============================================================

SELECT
    company_id,
    year,
    debt_to_equity
FROM financial_ratios
WHERE year = (
    SELECT MAX(year)
    FROM financial_ratios
)
ORDER BY debt_to_equity DESC
LIMIT 10;


-- ============================================================
-- Q7. Number of Companies in Each Sector
-- ============================================================

SELECT
    sector,
    COUNT(*) AS company_count
FROM sectors
GROUP BY sector
ORDER BY company_count DESC;


-- ============================================================
-- Q8. Average PE Ratio by Year
-- ============================================================

SELECT
    year,
    ROUND(AVG(pe_ratio), 2) AS avg_pe_ratio
FROM market_cap
GROUP BY year
ORDER BY year;


-- ============================================================
-- Q9. Stock Price History for ABB
-- ============================================================

SELECT
    date,
    open,
    high,
    low,
    close,
    volume
FROM stock_prices
WHERE company_id = 'ABB'
ORDER BY date;


-- ============================================================
-- Q10. Top 10 Companies by Dividend Yield
-- ============================================================

SELECT
    company_id,
    year,
    dividend_yield_pct
FROM market_cap
WHERE year = (
    SELECT MAX(year)
    FROM market_cap
)
ORDER BY dividend_yield_pct DESC
LIMIT 10;
