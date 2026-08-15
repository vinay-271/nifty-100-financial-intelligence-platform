import sqlite3

import pytest

from src.etl.validator import DataValidator


@pytest.fixture
def validator(tmp_path):
    db_path = tmp_path / "test.db"

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")

    validator = DataValidator()
    validator.connection = connection

    yield validator

    connection.close()


def create_table(validator, sql):
    validator.connection.execute(sql)
    validator.connection.commit()

def create_empty_tables(validator, tables):
    for table in tables:
        if table == "companies":
            validator.connection.execute(
                """
                CREATE TABLE companies (
                    id TEXT,
                    company_name TEXT
                )
                """
            )

        elif table == "profitandloss":
            validator.connection.execute(
                """
                CREATE TABLE profitandloss (
                    id INTEGER,
                    company_id TEXT,
                    year TEXT
                )
                """
            )

        elif table in {"balancesheet", "cashflow", "financial_ratios", "market_cap"}:
            validator.connection.execute(
                f"""
                CREATE TABLE {table} (
                    id INTEGER,
                    company_id TEXT,
                    year TEXT
                )
                """
            )

        elif table == "analysis":
            validator.connection.execute(
                """
                CREATE TABLE analysis (
                    id INTEGER
                )
                """
            )

        elif table == "documents":
            validator.connection.execute(
                """
                CREATE TABLE documents (
                    id INTEGER
                )
                """
            )

        elif table == "prosandcons":
            validator.connection.execute(
                """
                CREATE TABLE prosandcons (
                    id INTEGER
                )
                """
            )

        elif table == "stock_prices":
            validator.connection.execute(
                """
                CREATE TABLE stock_prices (
                    id INTEGER
                )
                """
            )

        elif table == "peer_groups":
            validator.connection.execute(
                """
                CREATE TABLE peer_groups (
                    id INTEGER
                )
                """
            )

        elif table == "sectors":
            validator.connection.execute(
                """
                CREATE TABLE sectors (
                    id INTEGER
                )
                """
            )

    validator.connection.commit()
# ============================================================
# DQ-01 — Primary Key Uniqueness
# ============================================================

def test_dq01_pk_uniqueness(validator):
    create_empty_tables(
        validator,
        [
            "companies",
            "profitandloss",
            "balancesheet",
            "cashflow",
            "analysis",
            "documents",
            "prosandcons",
            "stock_prices",
            "financial_ratios",
            "market_cap",
            "peer_groups",
            "sectors",
        ],
    )

    validator.connection.executemany(
        "INSERT INTO companies VALUES (?, ?)",
        [
            ("TCS", "Tata Consultancy Services"),
            ("TCS", "Tata Consultancy Services"),
        ],
    )
    validator.connection.commit()

    validator.dq01_pk_uniqueness()

    failures = [f for f in validator.failures if f["rule"] == "DQ-01"]

    assert len(failures) == 1
    assert failures[0]["table"] == "companies"
    assert failures[0]["record_id"] == "TCS"


# ============================================================
# DQ-02 — Company / Year Uniqueness
# ============================================================

def test_dq02_company_year_uniqueness(validator):
    create_empty_tables(
        validator,
        [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
        ],
    )

    validator.connection.executemany(
        "INSERT INTO profitandloss VALUES (?, ?, ?)",
        [
            (1, "TCS", "Mar 2024"),
            (2, "TCS", "Mar 2024"),
        ],
    )
    validator.connection.commit()

    validator.dq02_company_year_uniqueness()

    failures = [f for f in validator.failures if f["rule"] == "DQ-02"]

    assert len(failures) == 1
    assert failures[0]["record_id"] == "TCS-Mar 2024"


# ============================================================
# DQ-03 — Foreign Key Integrity
# ============================================================

def test_dq03_fk_integrity(validator):
    create_table(
        validator,
        """
        CREATE TABLE companies (
            id TEXT PRIMARY KEY
        )
        """,
    )

    create_table(
        validator,
        """
        CREATE TABLE profitandloss (
            id INTEGER PRIMARY KEY,
            company_id TEXT,
            year TEXT,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        )
        """,
    )

    validator.connection.execute(
        "INSERT INTO companies VALUES ('TCS')"
    )

    validator.connection.commit()

    # Disable enforcement only for inserting deliberately bad data.
    validator.connection.execute("PRAGMA foreign_keys = OFF")

    validator.connection.execute(
        "INSERT INTO profitandloss VALUES (1, 'INVALID', 'Mar 2024')"
    )

    validator.connection.commit()

    validator.connection.execute("PRAGMA foreign_keys = ON")

    validator.dq03_fk_integrity()

    failures = [f for f in validator.failures if f["rule"] == "DQ-03"]

    assert len(failures) == 1
    assert failures[0]["table"] == "profitandloss"


# ============================================================
# DQ-04 — Balance Sheet Balance
# ============================================================

def test_dq04_balance_sheet_balance(validator):
    create_table(
        validator,
        """
        CREATE TABLE balancesheet (
            id INTEGER,
            company_id TEXT,
            year TEXT,
            total_assets REAL,
            total_liabilities REAL
        )
        """,
    )

    validator.connection.execute(
        """
        INSERT INTO balancesheet
        VALUES (1, 'TCS', 'Mar 2024', 1000, 900)
        """
    )
    validator.connection.commit()

    validator.dq04_balance_sheet_balance()

    failures = [f for f in validator.failures if f["rule"] == "DQ-04"]

    assert len(failures) == 1
    assert failures[0]["severity"] == "WARNING"


def test_dq04_balanced_sheet_passes(validator):
    create_table(
        validator,
        """
        CREATE TABLE balancesheet (
            id INTEGER,
            company_id TEXT,
            year TEXT,
            total_assets REAL,
            total_liabilities REAL
        )
        """,
    )

    validator.connection.execute(
        """
        INSERT INTO balancesheet
        VALUES (1, 'TCS', 'Mar 2024', 1000, 1005)
        """
    )
    validator.connection.commit()

    validator.dq04_balance_sheet_balance()

    assert not any(
        f["rule"] == "DQ-04"
        for f in validator.failures
    )


# ============================================================
# DQ-05 — OPM Cross Check
# ============================================================

def test_dq05_opm_cross_check(validator):
    create_table(
        validator,
        """
        CREATE TABLE profitandloss (
            id INTEGER,
            sales REAL,
            operating_profit REAL,
            opm_percentage REAL
        )
        """,
    )

    validator.connection.execute(
        """
        INSERT INTO profitandloss
        VALUES (1, 1000, 100, 80)
        """
    )
    validator.connection.commit()

    validator.dq05_opm_cross_check()

    failures = [f for f in validator.failures if f["rule"] == "DQ-05"]

    assert len(failures) == 1


# ============================================================
# DQ-06 — Positive Sales
# ============================================================

def test_dq06_positive_sales(validator):
    create_table(
        validator,
        """
        CREATE TABLE profitandloss (
            id INTEGER,
            sales REAL,
            expenses REAL,
            operating_profit REAL,
            net_profit REAL
        )
        """,
    )

    validator.connection.execute(
        """
        INSERT INTO profitandloss
        VALUES (1, -100, 50, 20, 10)
        """
    )
    validator.connection.commit()

    validator.dq06_positive_sales()

    failures = [f for f in validator.failures if f["rule"] == "DQ-06"]

    assert len(failures) == 1
    assert failures[0]["severity"] == "CRITICAL"


# ============================================================
# DQ-07 — Net Cash Flow
# ============================================================

def test_dq07_net_cash_flow(validator):
    create_table(
        validator,
        """
        CREATE TABLE cashflow (
            id INTEGER,
            operating_activity REAL,
            investing_activity REAL,
            financing_activity REAL,
            net_cash_flow REAL
        )
        """,
    )

    validator.connection.execute(
        """
        INSERT INTO cashflow
        VALUES (1, 100, -20, -10, 500)
        """
    )
    validator.connection.commit()

    validator.dq07_net_cash_flow()

    failures = [f for f in validator.failures if f["rule"] == "DQ-07"]

    assert len(failures) == 1


# ============================================================
# DQ-08 — Tax Rate
# ============================================================

def test_dq08_tax_rate(validator):
    create_table(
        validator,
        """
        CREATE TABLE profitandloss (
            id INTEGER,
            tax_percentage REAL
        )
        """,
    )

    validator.connection.execute(
        "INSERT INTO profitandloss VALUES (1, 150)"
    )
    validator.connection.commit()

    validator.dq08_tax_rate()

    failures = [f for f in validator.failures if f["rule"] == "DQ-08"]

    assert len(failures) == 1


# ============================================================
# DQ-09 — Dividend Payout
# ============================================================

def test_dq09_dividend_payout(validator):
    create_table(
        validator,
        """
        CREATE TABLE profitandloss (
            id INTEGER,
            dividend_payout REAL
        )
        """,
    )

    validator.connection.execute(
        "INSERT INTO profitandloss VALUES (1, 120)"
    )
    validator.connection.commit()

    validator.dq09_dividend_payout()

    failures = [f for f in validator.failures if f["rule"] == "DQ-09"]

    assert len(failures) == 1


# ============================================================
# DQ-10 — URL Validation
# ============================================================

def test_dq10_url_validation(validator):
    create_table(
        validator,
        """
        CREATE TABLE companies (
            id TEXT,
            website TEXT
        )
        """,
    )

    validator.connection.execute(
        "INSERT INTO companies VALUES ('TCS', 'www.tcs.com')"
    )
    validator.connection.commit()

    validator.dq10_url_validation()

    failures = [f for f in validator.failures if f["rule"] == "DQ-10"]

    assert len(failures) == 1


# ============================================================
# DQ-11 — EPS Sign
# ============================================================

def test_dq11_eps_sign(validator):
    create_table(
        validator,
        """
        CREATE TABLE profitandloss (
            id INTEGER,
            net_profit REAL,
            eps REAL
        )
        """,
    )

    validator.connection.execute(
        "INSERT INTO profitandloss VALUES (1, 100, -5)"
    )
    validator.connection.commit()

    validator.dq11_eps_sign()

    failures = [f for f in validator.failures if f["rule"] == "DQ-11"]

    assert len(failures) == 1


# ============================================================
# DQ-12 — Company Coverage
# ============================================================

def test_dq12_company_coverage(validator):
    create_table(
        validator,
        """
        CREATE TABLE companies (
            id TEXT
        )
        """,
    )

    for i in range(91):
        validator.connection.execute(
            "INSERT INTO companies VALUES (?)",
            (f"C{i}",),
        )

    validator.connection.commit()

    validator.dq12_company_coverage()

    failures = [f for f in validator.failures if f["rule"] == "DQ-12"]

    assert len(failures) == 1
    assert "Expected 92" in failures[0]["message"]


# ============================================================
# DQ-13 — Year Coverage
# ============================================================

def test_dq13_year_coverage(validator):
    create_table(
        validator,
        """
        CREATE TABLE profitandloss (
            company_id TEXT,
            year TEXT
        )
        """,
    )

    for year in ["Mar 2022", "Mar 2023", "Mar 2024"]:
        validator.connection.execute(
            "INSERT INTO profitandloss VALUES ('TCS', ?)",
            (year,),
        )

    validator.connection.commit()

    validator.dq13_year_coverage()

    failures = [f for f in validator.failures if f["rule"] == "DQ-13"]

    assert len(failures) == 1
    assert failures[0]["record_id"] == "TCS"


# ============================================================
# DQ-15 — Missing Critical Fields
# ============================================================

def test_dq15_missing_critical_fields(validator):
    create_empty_tables(
        validator,
        [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
        ],
    )

    validator.connection.execute(
        "INSERT INTO profitandloss VALUES (1, NULL, 'Mar 2024')"
    )
    validator.connection.commit()

    validator.dq15_missing_critical_fields()

    failures = [f for f in validator.failures if f["rule"] == "DQ-15"]

    assert len(failures) == 1
    assert failures[0]["record_id"] == 1


# ============================================================
# DQ-16 — Numeric Sanity
# ============================================================

def test_dq16_numeric_sanity(validator):
    create_table(
        validator,
        """
        CREATE TABLE balancesheet (
            id INTEGER,
            total_assets REAL,
            total_liabilities REAL
        )
        """,
    )

    validator.connection.execute(
        "INSERT INTO balancesheet VALUES (1, -100, 500)"
    )
    validator.connection.commit()

    validator.dq16_numeric_sanity()

    failures = [f for f in validator.failures if f["rule"] == "DQ-16"]

    assert len(failures) == 1
    assert failures[0]["severity"] == "WARNING"
