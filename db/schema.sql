-- N100 Financial Intelligence Platform
-- SQLite Database Schema

-- PRAGMA foreign_keys = OFF;

-- DROP TABLE IF EXISTS peer_groups;
-- DROP TABLE IF EXISTS sectors;
-- DROP TABLE IF EXISTS market_cap;
-- DROP TABLE IF EXISTS financial_ratios;
-- DROP TABLE IF EXISTS stock_prices;
-- DROP TABLE IF EXISTS prosandcons;
-- DROP TABLE IF EXISTS documents;
-- DROP TABLE IF EXISTS analysis;
-- DROP TABLE IF EXISTS cashflow;
-- DROP TABLE IF EXISTS balancesheet;
-- DROP TABLE IF EXISTS profitandloss;
-- DROP TABLE IF EXISTS companies;

PRAGMA foreign_keys = ON;


CREATE TABLE companies (
    id TEXT PRIMARY KEY,

    company_logo TEXT,
    company_name TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,

    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

CREATE TABLE profitandloss (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,
    year TEXT NOT NULL,

    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE balancesheet (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,
    year TEXT NOT NULL,

    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE cashflow (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,
    year TEXT NOT NULL,

    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    compounded_sales_growth REAL,
    compounded_profit_growth REAL,
    stock_price_cagr REAL,
    roe REAL,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE documents (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,
    year TEXT,
    annual_report TEXT,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    pros TEXT,
    cons TEXT,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);


CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    adjusted_close REAL,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE financial_ratios (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,
    year TEXT NOT NULL,

    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,

    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================
-- Market Cap
-- ============================================================

CREATE TABLE market_cap (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,

    market_cap_cr REAL,
    enterprise_value_cr REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,

    FOREIGN KEY(company_id) REFERENCES companies(id)
);

-- ============================================================
-- Peer Groups
-- ============================================================

CREATE TABLE peer_groups (
    id INTEGER PRIMARY KEY,

    peer_group TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_primary_company BOOLEAN,

    FOREIGN KEY(company_id) REFERENCES companies(id)
);

-- ============================================================
-- Sectors
-- ============================================================

CREATE TABLE sectors (
    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    sector TEXT,
    industry TEXT,
    weight_pct REAL,
    market_cap_category TEXT,

    FOREIGN KEY(company_id) REFERENCES companies(id)
);
