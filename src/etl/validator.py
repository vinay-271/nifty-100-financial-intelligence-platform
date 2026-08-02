import sqlite3
from pathlib import Path

import pandas as pd
from loguru import logger


class DataValidator:
    """Runs Data Quality (DQ) validation rules on the N100 database."""

    def __init__(self):
        self.db_path = Path("db") / "nifty100.db"
        self.output_path = Path("data") / "output"

        self.connection = None
        self.failures = []

    # ==========================================================
    # Database
    # ==========================================================

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")

    # ==========================================================
    # Main Validation Pipeline
    # ==========================================================

    def validate(self):

        if self.connection is None:
            self.connect()

        logger.info("Running Data Quality Validation...")

        self.dq01_pk_uniqueness()
        self.dq02_company_year_uniqueness()
        self.dq03_fk_integrity()

        self.dq04_balance_sheet_balance()
        self.dq05_opm_cross_check()
        self.dq06_positive_sales()
        self.dq07_net_cash_flow()
        self.dq08_tax_rate()
        self.dq09_dividend_payout()
        self.dq10_url_validation()
        self.dq11_eps_sign()
        self.dq12_company_coverage()
        self.dq13_year_coverage()
        # self.dq14_duplicate_business_records()
        self.dq15_missing_critical_fields()
        self.dq16_numeric_sanity()

        self.export_failures()

        logger.info("Validation completed.")

    # ==========================================================
    # DQ-01
    # Primary Key Uniqueness
    # ==========================================================

    def dq01_pk_uniqueness(self):

        logger.info("DQ-01: Checking primary key uniqueness...")

        cursor = self.connection.cursor()

        tables = [
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
        ]

        for table in tables:

            cursor.execute(f"""
                SELECT id, COUNT(*)
                FROM {table}
                GROUP BY id
                HAVING COUNT(*) > 1
            """)

            duplicates = cursor.fetchall()

            for record_id, count in duplicates:

                self.failures.append({
                    "rule": "DQ-01",
                    "table": table,
                    "severity": "CRITICAL",
                    "record_id": record_id,
                    "message": f"Primary key duplicated ({count} occurrences)."
                })

    # ==========================================================
    # DQ-02
    # (company_id, year) uniqueness
    # ==========================================================

    def dq02_company_year_uniqueness(self):

        logger.info("DQ-02: Checking (company_id, year) uniqueness...")

        cursor = self.connection.cursor()

        tables = [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
        ]

        for table in tables:

            cursor.execute(f"""
                SELECT company_id,
                       year,
                       COUNT(*)
                FROM {table}
                GROUP BY company_id, year
                HAVING COUNT(*) > 1
            """)

            duplicates = cursor.fetchall()

            for company_id, year, count in duplicates:

                self.failures.append({
                    "rule": "DQ-02",
                    "table": table,
                    "severity": "CRITICAL",
                    "record_id": f"{company_id}-{year}",
                    "message": f"Duplicate company/year combination ({count} rows)."
                })

    # ==========================================================
    # DQ-03
    # Foreign Key Integrity
    # ==========================================================

    def dq03_fk_integrity(self):

        logger.info("DQ-03: Checking foreign key integrity...")

        cursor = self.connection.cursor()

        cursor.execute("PRAGMA foreign_key_check")

        violations = cursor.fetchall()

        for table, rowid, parent, fk in violations:

            self.failures.append({
                "rule": "DQ-03",
                "table": table,
                "severity": "CRITICAL",
                "record_id": rowid,
                "message": f"Foreign key violation referencing '{parent}'."
            })

    # ==========================================================
    # DQ-04
    # Balance Sheet Balance
    # ==========================================================

    def dq04_balance_sheet_balance(self):
        """
        DQ-04: Verify Total Assets ≈ Total Liabilities (within 1%).
        """

        logger.info("DQ-04: Checking balance sheet equation...")

        query = """
            SELECT
                id,
                company_id,
                year,
                total_assets,
                total_liabilities
            FROM balancesheet
            """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            assets = row["total_assets"]
            liabilities = row["total_liabilities"]

            if pd.isna(assets) or pd.isna(liabilities):
                continue

            if assets == 0:
                continue

            difference_pct = abs(assets - liabilities) / abs(assets) * 100

            if difference_pct > 1:

                self.failures.append({
                    "rule": "DQ-04",
                    "table": "balancesheet",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message":
                        f"Assets ({assets}) != Liabilities ({liabilities}) "
                        f"Difference = {difference_pct:.2f}%"
                })

    # ==========================================================
    # DQ-05
    # OPM Cross Check
    # ==========================================================

    def dq05_opm_cross_check(self):
        """
        DQ-05: Verify Operating Profit Margin.
        """

        logger.info("DQ-05: Checking Operating Profit Margin...")

        query = """
            SELECT
                id,
                sales,
                operating_profit,
                opm_percentage
            FROM profitandloss
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            sales = row["sales"]

            if pd.isna(sales) or sales == 0:
                continue

            calculated = (
                row["operating_profit"] / sales
            ) * 100

            # difference = abs(calculated - row["opm_percentage"])

            # if difference > 0.5:

            #     self.failures.append({
            #         "rule": "DQ-05",
            #         "table": "profitandloss",
            #         "severity": "WARNING",
            #         "record_id": row["id"],
            #         "message":
            #             f"Stored OPM={row['opm_percentage']:.2f}, "
            #             f"Calculated={calculated:.2f}"
            #     })

            if row["opm_percentage"] > 100 or row["opm_percentage"] < -100:
                self.failures.append({
                    "rule": "DQ-05",
                    "table": "profitandloss",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message": f"Implausible OPM value ({row['opm_percentage']})."
                })
                continue

            difference = abs(calculated - row["opm_percentage"])

            if difference > 1:

                self.failures.append({
                    "rule": "DQ-05",
                    "table": "profitandloss",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message":
                        f"Stored={row['opm_percentage']:.2f}, "
                        f"Calculated={calculated:.2f}, "
                        f"Difference={difference:.2f}"
                })

    # ==========================================================
    # DQ-06
    # Positive Sales
    # ==========================================================

    def dq06_positive_sales(self):
        """
        DQ-06: Sales must be positive unless the entire financial statement is empty.
        """

        logger.info("DQ-06: Checking positive sales...")

        query = """
            SELECT
                id,
                sales,
                expenses,
                operating_profit,
                net_profit
            FROM profitandloss
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            sales = row["sales"]

            # Ignore completely empty financial records
            if (
                (pd.isna(sales) or sales == 0)
                and (pd.isna(row["expenses"]) or row["expenses"] == 0)
                and (pd.isna(row["operating_profit"]) or row["operating_profit"] == 0)
                and (pd.isna(row["net_profit"]) or row["net_profit"] == 0)
            ):
                continue

            # Flag genuinely invalid sales values
            if pd.isna(sales) or sales <= 0:

                self.failures.append({
                    "rule": "DQ-06",
                    "table": "profitandloss",
                    "severity": "CRITICAL",
                    "record_id": row["id"],
                    "message": f"Invalid sales value ({sales})"
                })

    # ==========================================================
    # DQ-07
    # Net Cash Flows Validation
    # ==========================================================

    def dq07_net_cash_flow(self):
        """
        DQ-07: Verify net cash flow equation.
        """

        logger.info("DQ-07: Checking net cash flow...")

        query = """
            SELECT
                id,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            calculated = (
                row["operating_activity"]
                + row["investing_activity"]
                + row["financing_activity"]
            )

            difference = abs(
                calculated - row["net_cash_flow"]
            )

            if difference > 1:

                self.failures.append({
                    "rule": "DQ-07",
                    "table": "cashflow",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message":
                        f"Expected {calculated:.2f}, "
                        f"Found {row['net_cash_flow']:.2f}"
                })


    # ==========================================================
    # DQ-08
    # Tax Rate Validation
    # ==========================================================
    def dq08_tax_rate(self):
        """
        DQ-08: Tax percentage should be between 0 and 100.
        """

        logger.info("DQ-08: Checking tax percentage...")

        query = """
            SELECT id, tax_percentage
            FROM profitandloss
            WHERE tax_percentage IS NOT NULL
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            tax = row["tax_percentage"]

            if tax < 0 or tax > 100:

                self.failures.append({
                    "rule": "DQ-08",
                    "table": "profitandloss",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message": f"Invalid tax percentage ({tax})."
                })

    # ==========================================================
    # DQ-09
    # Dividend Payout Validation
    # ==========================================================
    def dq09_dividend_payout(self):
        """
        DQ-09: Dividend payout should be between 0 and 100.
        """

        logger.info("DQ-09: Checking dividend payout...")

        query = """
            SELECT id, dividend_payout
            FROM profitandloss
            WHERE dividend_payout IS NOT NULL
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            payout = row["dividend_payout"]

            if payout < 0 or payout > 100:

                self.failures.append({
                    "rule": "DQ-09",
                    "table": "profitandloss",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message": f"Invalid dividend payout ({payout})."
                })

    # ==========================================================
    # DQ-10
    # URL Validation
    # ==========================================================
    def dq10_url_validation(self):
        """
        DQ-10: Website URLs should start with http:// or https://
        """

        logger.info("DQ-10: Checking company URLs...")

        query = """
            SELECT id, website
            FROM companies
            WHERE website IS NOT NULL
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            url = str(row["website"]).strip()

            if url and not (
                url.startswith("http://")
                or url.startswith("https://")
            ):

                self.failures.append({
                    "rule": "DQ-10",
                    "table": "companies",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message": f"Invalid URL ({url})"
                })

    # ==========================================================
    # DQ-11
    # EPS Sign Validation
    # ==========================================================
    def dq11_eps_sign(self):
        """
        DQ-11: EPS sign should match Net Profit sign.
        """

        logger.info("DQ-11: Checking EPS sign...")

        query = """
            SELECT
                id,
                net_profit,
                eps
            FROM profitandloss
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            profit = row["net_profit"]
            eps = row["eps"]

            if pd.isna(profit) or pd.isna(eps):
                continue

            if profit * eps < 0:

                self.failures.append({
                    "rule": "DQ-11",
                    "table": "profitandloss",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message": "EPS sign does not match Net Profit."
                })


    # ==========================================================
    # DQ-12
    # Company Coverage
    # ==========================================================
    def dq12_company_coverage(self):
        """
        DQ-12: Verify company count.
        """

        logger.info("DQ-12: Checking company coverage...")

        cursor = self.connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM companies")

        count = cursor.fetchone()[0]

        if count != 92:

            self.failures.append({
                "rule": "DQ-12",
                "table": "companies",
                "severity": "CRITICAL",
                "record_id": "",
                "message": f"Expected 92 companies, found {count}."
            })

    # ==========================================================
    # DQ-13
    # Year Coverage
    # ==========================================================
    def dq13_year_coverage(self):
        """
        DQ-13: Company should have at least 5 years of P&L.
        """

        logger.info("DQ-13: Checking year coverage...")

        query = """
            SELECT
                company_id,
                COUNT(DISTINCT year) AS years
            FROM profitandloss
            GROUP BY company_id
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            if row["years"] < 5:

                self.failures.append({
                    "rule": "DQ-13",
                    "table": "profitandloss",
                    "severity": "WARNING",
                    "record_id": row["company_id"],
                    "message": f"Only {row['years']} years available."
                })
    # ==========================================================
    # DQ-14
    # Duplicate Business Records
    # ==========================================================
    # def dq14_duplicate_business_records(self):
    #     """
    #     DQ-14: Duplicate company-year records.
    #     """

    #     logger.info("DQ-14: Checking duplicate business records...")

    #     tables = [
    #         "profitandloss",
    #         "balancesheet",
    #         "cashflow",
    #         "financial_ratios",
    #         "market_cap",
    #     ]

    #     cursor = self.connection.cursor()

    #     for table in tables:

    #         cursor.execute(f"""
    #             SELECT company_id,
    #                 year,
    #                 COUNT(*)
    #             FROM {table}
    #             GROUP BY company_id, year
    #             HAVING COUNT(*) > 1
    #         """)

    #         rows = cursor.fetchall()

    #         for company, year, count in rows:

    #             self.failures.append({
    #                 "rule": "DQ-14",
    #                 "table": table,
    #                 "severity": "CRITICAL",
    #                 "record_id": f"{company}-{year}",
    #                 "message": f"{count} duplicate records."
    #             })
    # ==========================================================
    # DQ-15
    # Missing Critical Fields
    # ==========================================================
    def dq15_missing_critical_fields(self):
        """
        DQ-15: company_id and year should not be NULL.
        """

        logger.info("DQ-15: Checking missing critical fields...")

        tables = [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
        ]

        cursor = self.connection.cursor()

        for table in tables:

            cursor.execute(f"""
                SELECT id
                FROM {table}
                WHERE company_id IS NULL
                OR year IS NULL
            """)

            rows = cursor.fetchall()

            for (record_id,) in rows:

                self.failures.append({
                    "rule": "DQ-15",
                    "table": table,
                    "severity": "CRITICAL",
                    "record_id": record_id,
                    "message": "Missing company_id or year."
                })
    # ==========================================================
    # DQ-16
    # Numeric Sanity
    # ==========================================================
    def dq16_numeric_sanity(self):
        """
        DQ-16: Negative Assets/Liabilities sanity check.
        """

        logger.info("DQ-16: Checking numeric sanity...")

        query = """
            SELECT
                id,
                total_assets,
                total_liabilities
            FROM balancesheet
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            assets = row["total_assets"]
            liabilities = row["total_liabilities"]

            if (
                assets is not None
                and assets < 0
            ) or (
                liabilities is not None
                and liabilities < 0
            ):

                self.failures.append({
                    "rule": "DQ-16",
                    "table": "balancesheet",
                    "severity": "WARNING",
                    "record_id": row["id"],
                    "message": "Negative asset/liability detected."
                })

    # ==========================================================
    # Export
    # ==========================================================
    def export_failures(self):

        self.output_path.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(self.failures)

        if df.empty:

            df = pd.DataFrame(columns=[
                "rule",
                "table",
                "severity",
                "record_id",
                "message",
            ])

        output_file = self.output_path / "validation_failures.csv"

        df.to_csv(output_file, index=False)

        logger.info(
            f"Saved {len(df)} validation failures to {output_file}"
        )
