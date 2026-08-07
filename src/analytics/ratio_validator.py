import sqlite3
from pathlib import Path

import pandas as pd
from loguru import logger


class RatioValidator:

    def __init__(self, db_path="db/nifty100.db"):

        self.db_path = db_path
        self.connection = None

        self.edge_cases = []

    def connect(self):

        self.connection = sqlite3.connect(self.db_path)

        logger.info(f"Connected to {self.db_path}")

    def close(self):

        if self.connection:
            self.connection.close()

            logger.info("Database connection closed.")

    def validate(self):

        logger.info("Running ratio validation...")

        self.validate_roe()

        self.validate_roce()

        self.export_log()

        logger.info("Validation complete.")

    def validate_roe(self):

        logger.info("Checking ROE...")

        query = """
        SELECT

            fr.company_id,
            fr.year,

            fr.return_on_equity_pct AS computed,

            c.roe_percentage AS source

        FROM financial_ratios fr

        INNER JOIN companies c

            ON fr.company_id = c.id

        WHERE c.roe_percentage IS NOT NULL
        """

        df = pd.read_sql(query, self.connection)

        for _, row in df.iterrows():

            if pd.isna(row.source):
                continue

            difference = abs(row.computed - row.source)

            if difference > 5:

                self.edge_cases.append({

                    "company_id": row.company_id,

                    "year": row.year,

                    "metric": "ROE",

                    "computed": round(row.computed, 2),

                    "source": round(row.source, 2),

                    "difference": round(difference, 2),

                    "category": "Formula Discrepancy"

                })

        logger.info(
            f"ROE anomalies: {len(self.edge_cases)}"
        )

    def export_log(self):

        output = Path("data/output/ratio_edge_cases.csv")

        pd.DataFrame(
            self.edge_cases
        ).to_csv(
            output,
            index=False,
        )

        logger.info(
            f"Saved {len(self.edge_cases)} edge cases to {output}"
        )

    def validate_roce(self):

        logger.info("Checking ROCE...")

        query = """
        SELECT

            fr.company_id,
            fr.year,

            fr.return_on_capital_employed_pct AS computed,

            c.roce_percentage AS source

        FROM financial_ratios fr

        INNER JOIN companies c

            ON fr.company_id = c.id

        WHERE
            fr.return_on_capital_employed_pct IS NOT NULL
            AND c.roce_percentage IS NOT NULL
        """

        df = pd.read_sql(query, self.connection)

        count = 0

        for _, row in df.iterrows():

            difference = abs(row.computed - row.source)

            if difference > 5:

                # Categorize anomaly
                if difference > 20:
                    category = "Data Source Issue"
                else:
                    category = "Version Difference"

                self.edge_cases.append({

                    "company_id": row.company_id,

                    "year": row.year,

                    "metric": "ROCE",

                    "computed": round(row.computed, 2),

                    "source": round(row.source, 2),

                    "difference": round(difference, 2),

                    "category": category

                })

                count += 1

        logger.info(
            f"ROCE anomalies: {count}"
        )
