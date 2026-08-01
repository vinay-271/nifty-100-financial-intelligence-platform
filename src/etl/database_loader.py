import sqlite3
from pathlib import Path
from loguru import logger
import pandas as pd
import re




class DatabaseLoader:
    """Loads cleaned datasets into the SQLite data warehouse."""

    def __init__(self):
        self.db_path = Path("db") / "nifty100.db"
        self.schema_path = Path("db") / "schema.sql"
        self.cleaned_data_path = Path("data") / "cleaned"
        self.connection = None
        self.load_audit = []

    def add_load_audit(
        self,
        table_name,
        loaded_rows,
        rejected_rows,
        reason=""
    ):
        self.load_audit.append({
            "table_name": table_name,
            "loaded_rows": loaded_rows,
            "rejected_rows": rejected_rows,
            "reason": reason
        })

    def connect(self):
        """Create a connection to the SQLite database."""

        self.connection = sqlite3.connect(self.db_path)

        logger.info(f"Connected to database: {self.db_path}")

        return self.connection

    def close(self):
        """Close the database connection."""

        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")

    def create_tables(self):
        # """Create all warehouse tables from schema.sql."""

        # if self.connection is None:
        #     self.connect()

        # with open(self.schema_path, "r", encoding="utf-8") as file:
        #     schema = file.read()

        # self.connection.executescript(schema)
        # self.connection.commit()

        # logger.info("Database schema created successfully.")
        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema = f.read()

        for stmt in schema.split(";"):
            stmt = stmt.strip()
            if not stmt:
                continue

            try:
                self.connection.executescript(schema)
                # self.connection.commit()
            except Exception as e:
                print("\nFAILED STATEMENT:\n")
                print(stmt)
                raise

    def load_companies(self):
        """Load companies.csv into companies table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(
            self.cleaned_data_path / "companies.csv"
        )

        df.to_sql(
            "companies",
            self.connection,
            if_exists="append",
            index=False
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(df)} records into companies."
        )

    def clear_tables(self):
        """Clear all database tables."""

        if self.connection is None:
            self.connect()

        cursor = self.connection.cursor()

        tables = [
            "peer_groups",
            "sectors",
            "market_cap",
            "financial_ratios",
            "stock_prices",
            "prosandcons",
            "documents",
            "analysis",
            "cashflow",
            "balancesheet",
            "profitandloss",
            "companies",
        ]

        for table in tables:
            cursor.execute(f"DELETE FROM {table}")

        self.connection.commit()

        logger.info("All tables cleared.")

    def load_profitandloss(self):
        """Load profitandloss.csv into profitandloss table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(
            self.cleaned_data_path / "profitandloss.csv"
        )

        valid_df, rejected_df = self.filter_valid_company_ids(df)

        valid_df.to_sql(
            "profitandloss",
            self.connection,
            if_exists="append",
            index=False
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(valid_df)} records into profitandloss."
        )

        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing company_id."
        )

        self.add_load_audit(
            table_name="profitandloss",
            loaded_rows=len(valid_df),
            rejected_rows=len(rejected_df),
            reason="Missing company_id"
        )

        # print(
        #     rejected_df["company_id"]
        #     .value_counts()
        # )

    def filter_valid_company_ids(self, df: pd.DataFrame):
        """
        Keep only rows whose company_id exists in companies table.
        Returns:
            valid_df
            rejected_df
        """

        companies = pd.read_sql(
            "SELECT id FROM companies",
            self.connection
        )

        valid_ids = set(companies["id"])

        valid_df = df[df["company_id"].isin(valid_ids)].copy()

        rejected_df = df[~df["company_id"].isin(valid_ids)].copy()

        return valid_df, rejected_df

    def export_load_audit(self):
        audit = pd.DataFrame(self.load_audit)

        output_path = (
            Path("data")
            / "output"
            / "load_audit.csv"
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        audit.to_csv(
            output_path,
            index=False
        )

        logger.info(
            f"Load audit saved to {output_path}"
        )

    def load_balancesheet(self):
        """Load balancesheet.csv into balancesheet table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(
            self.cleaned_data_path / "balancesheet.csv"
        )

        valid_df, rejected_df = self.filter_valid_company_ids(df)

        valid_df.to_sql(
            "balancesheet",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(valid_df)} records into balancesheet."
        )

        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing company_id."
        )

        self.add_load_audit(
            "balancesheet",
            len(valid_df),
            len(rejected_df),
            "Missing company_id"
        )

    def load_cashflow(self):
        """Load cashflow.csv into cashflow table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(
            self.cleaned_data_path / "cashflow.csv"
        )

        valid_df, rejected_df = self.filter_valid_company_ids(df)

        valid_df.to_sql(
            "cashflow",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(valid_df)} records into cashflow."
        )

        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing company_id."
        )

        self.add_load_audit(
            "cashflow",
            len(valid_df),
            len(rejected_df),
            "Missing company_id"
        )

    def load_analysis(self):
        """Load analysis.csv into analysis table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(
            self.cleaned_data_path / "analysis.csv"
        )

        valid_df, rejected_df = self.filter_valid_company_ids(df)

        valid_df.to_sql(
            "analysis",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(valid_df)} records into analysis."
        )

        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing company_id."
        )

        self.add_load_audit(
            "analysis",
            len(valid_df),
            len(rejected_df),
            "Missing company_id"
        )

    def load_documents(self):
        """Load documents.csv into documents table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(
            self.cleaned_data_path / "documents.csv"
        )

        valid_df, rejected_df = self.filter_valid_company_ids(df)

        valid_df.to_sql(
            "documents",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(valid_df)} records into documents."
        )

        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing company_id."
        )

        self.add_load_audit(
            "documents",
            len(valid_df),
            len(rejected_df),
            "Missing company_id"
        )

    def load_prosandcons(self):
        """Load prosandcons.csv into prosandcons table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(
            self.cleaned_data_path / "prosandcons.csv"
        )

        valid_df, rejected_df = self.filter_valid_company_ids(df)

        valid_df.to_sql(
            "prosandcons",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(valid_df)} records into prosandcons."
        )

        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing company_id."
        )

        self.add_load_audit(
            "prosandcons",
            len(valid_df),
            len(rejected_df),
            "Missing company_id"
        )

    def load_stock_prices(self):
        """Load stock_prices.csv into stock_prices table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(
            self.cleaned_data_path / "stock_prices.csv"
        )

        valid_df, rejected_df = self.filter_valid_company_ids(df)

        valid_df.to_sql(
            "stock_prices",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(valid_df)} records into stock_prices."
        )

        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing company_id."
        )

        self.add_load_audit(
            "stock_prices",
            len(valid_df),
            len(rejected_df),
            "Missing company_id"
        )

    def load_financial_ratios(self):
        """Load financial_ratios.csv into financial_ratios table."""

        if self.connection is None:
            self.connect()

        df = pd.read_csv(self.cleaned_data_path / "financial_ratios.csv")

        valid_df, rejected_df = self.filter_valid_company_ids(df)

        valid_df.to_sql(
            "financial_ratios",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(
            f"Loaded {len(valid_df)} records into financial_ratios."
        )

        logger.warning(
            f"Rejected {len(rejected_df)} records due to missing company_id."
        )

        self.add_load_audit(
            "financial_ratios",
            len(valid_df),
            len(rejected_df),
            "Missing company_id"
        )

    def load_market_cap(self):
        if self.connection is None:
            self.connect()

        df = pd.read_csv(self.cleaned_data_path / "market_cap.csv")

        valid_ids = set(
            pd.read_sql(
                "SELECT id FROM companies",
                self.connection
            )["id"]
        )

        rejected = df[~df["company_id"].isin(valid_ids)]
        df = df[df["company_id"].isin(valid_ids)]

        df.to_sql(
            "market_cap",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(f"Loaded {len(df)} records into market_cap.")
        logger.warning(
            f"Rejected {len(rejected)} records due to missing company_id."
        )

        self.load_audit.append({
            "table": "market_cap",
            "loaded": len(df),
            "rejected": len(rejected),
        })
