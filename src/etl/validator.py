"""
Data Quality Validator for the N100 Financial Intelligence Platform.

This module provides a reusable validation framework for checking
primary keys, foreign keys, composite keys, and business rules.
"""

from pathlib import Path
import pandas as pd
from loguru import logger


class DataValidator:
    """
    Generic Data Quality Validator.
    """

    def __init__(self, datasets: dict):

        self.datasets = datasets

        self.failures = []

        logger.info("DataValidator initialized.")

    def validate(self):
        """
        Run all validation rules.
        """

        logger.info("Starting validation...")

        self.validate_primary_keys()

        self.validate_composite_keys()

        self.validate_foreign_keys()

        logger.info("Validation completed.")

    def validate_primary_keys(self):
        """
        DQ-01

        Validate that primary keys are unique and not null.
        """

        logger.info("Running DQ-01 : Primary Key Validation")

        primary_keys = {
            "companies": "id",
            "profitandloss": "id",
            "balancesheet": "id",
            "cashflow": "id"
        }

        for dataset_name, pk in primary_keys.items():

            if dataset_name not in self.datasets:
                logger.warning(f"{dataset_name} not found.")
                continue

            df = self.datasets[dataset_name]

            # Missing primary keys
            missing = df[df[pk].isna()]

            for index in missing.index:
                self.add_failure(
                    "DQ-01",
                    "ERROR",
                    dataset_name,
                    index,
                    f"Primary key '{pk}' is NULL."
                )

            # Duplicate primary keys
            duplicates = df[df.duplicated(subset=[pk], keep=False)]

            for index, row in duplicates.iterrows():
                self.add_failure(
                    "DQ-01",
                    "ERROR",
                    dataset_name,
                    index,
                    f"Duplicate primary key '{row[pk]}'."
                )

        logger.info("DQ-01 completed.")

    def validate_composite_keys(self):
        """
        DQ-02

        Validate composite business keys.
        """

        logger.info("Running DQ-02 : Composite Key Validation")

        composite_keys = {
            "profitandloss": ["company_id", "year"],
            "balancesheet": ["company_id", "year"],
            "cashflow": ["company_id", "year"]
        }

        for dataset_name, columns in composite_keys.items():

            if dataset_name not in self.datasets:
                logger.warning(f"{dataset_name} not found.")
                continue

            df = self.datasets[dataset_name]

            duplicates = df[
                df.duplicated(subset=columns, keep=False)
            ]

            for index, row in duplicates.iterrows():

                values = ", ".join(
                    str(row[col]) for col in columns
                )

                self.add_failure(
                    "DQ-02",
                    "ERROR",
                    dataset_name,
                    index,
                    f"Duplicate composite key ({values})."
                )

        logger.info("DQ-02 completed.")

    def validate_foreign_keys(self):
        """
        DQ-03

        Validate foreign key integrity.
        """

        logger.info("Running DQ-03 : Foreign Key Validation")

        if "companies" not in self.datasets:
            logger.error("Companies dataset missing.")
            return

        company_ids = set(
            self.datasets["companies"]["id"]
            .astype(str)
            .str.strip()
        )

        child_tables = [
            "profitandloss",
            "balancesheet",
            "cashflow"
        ]

        for dataset_name in child_tables:

            if dataset_name not in self.datasets:
                logger.warning(f"{dataset_name} not found.")
                continue

            df = self.datasets[dataset_name]

            invalid = df[
                ~df["company_id"]
                .astype(str)
                .str.strip()
                .isin(company_ids)
            ]

            for index, row in invalid.iterrows():

                self.add_failure(
                    "DQ-03",
                    "ERROR",
                    dataset_name,
                    index,
                    f"Company ID '{row['company_id']}' not found."
                )

        logger.info("DQ-03 completed.")

    def add_failure(
        self,
        rule_id,
        severity,
        dataset,
        row,
        message
    ):
        """
        Add a validation failure.
        """

        self.failures.append({

            "Rule_ID": rule_id,

            "Severity": severity,

            "Dataset": dataset,

            "Row": row,

            "Message": message

        })

    def export_report(
        self,
        output_path="data/output/validation_failures.csv"
    ):
        """
        Export validation failures to CSV.
        """

        Path(output_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        report = pd.DataFrame(self.failures)

        report.to_csv(
            output_path,
            index=False
        )

        logger.info(
            f"Validation report saved to {output_path}"
        )

        return report

    def summary(self):
        """
        Print validation summary.
        """

        report = pd.DataFrame(self.failures)

        print("\nValidation Summary")
        print("------------------")

        if report.empty:
            print("No validation failures.")
            return

        print(f"Total Failures : {len(report)}\n")

        print("By Rule")
        print(report["Rule_ID"].value_counts())

        print("\nBy Severity")
        print(report["Severity"].value_counts())

        print("\nBy Dataset")
        print(report["Dataset"].value_counts())
