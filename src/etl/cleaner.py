from pathlib import Path
from typing import Dict

import pandas as pd
from loguru import logger


class DataCleaner:
    """
    Cleans financial datasets before loading into the data warehouse.
    """

    def __init__(self):
        self.cleaned_data = {}

    def clean(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Main cleaning pipeline.
        """
        logger.info("Starting data cleaning...")

        self.cleaned_data = {
            name: df.copy(deep=True)
            for name, df in datasets.items()
        }

        # Cleaning steps (implemented in later tasks)
        self.trim_whitespace()
        self.normalize_missing_values()
        self.convert_numeric_columns()
        self.remove_duplicate_business_records()

        logger.info("Data cleaning completed.")

        return self.cleaned_data

    def trim_whitespace(self):
        """
        Remove leading/trailing whitespace and newline characters
        from all string columns.
        """
        logger.info("Cleaning Rule C-01: Trimming whitespace...")

        for dataset_name, df in self.cleaned_data.items():

            object_columns = df.select_dtypes(include=["object"]).columns

            for column in object_columns:
                df[column] = (
                    df[column]
                    .astype("string")
                    .str.replace("\n", " ", regex=False)
                    .str.replace("\t", " ", regex=False)
                    .str.strip()
                )

            self.cleaned_data[dataset_name] = df

        logger.info("Whitespace trimming completed.")

    def normalize_missing_values(self):
        """
        Replace common missing value placeholders with NaN.
        """
        logger.info("Cleaning Rule C-02: Normalizing missing values...")

        missing_values = {
            "": pd.NA,
            " ": pd.NA,
            "NA": pd.NA,
            "N/A": pd.NA,
            "NULL": pd.NA,
            "null": pd.NA,
            "-": pd.NA,
        }

        for dataset_name, df in self.cleaned_data.items():
            df.replace(missing_values, inplace=True)
            self.cleaned_data[dataset_name] = df

        logger.info("Missing value normalization completed.")

    def convert_numeric_columns(self):
        """
        Convert financial columns to numeric data types.
        """
        logger.info("Cleaning Rule C-03: Converting numeric columns...")

        numeric_columns = {
            "companies": [
                "face_value",
                "book_value",
                "roce_percentage",
                "roe_percentage",
            ],
            "profitandloss": [
                "sales",
                "expenses",
                "operating_profit",
                "opm_percentage",
                "other_income",
                "interest",
                "depreciation",
                "profit_before_tax",
                "tax_percentage",
                "net_profit",
                "eps",
                "dividend_payout",
            ],
            "balancesheet": [
                "equity_capital",
                "reserves",
                "borrowings",
                "other_liabilities",
                "total_liabilities",
                "fixed_assets",
                "cwip",
                "investments",
                "other_asset",
                "total_assets",
            ],
            "cashflow": [
                "operating_activity",
                "investing_activity",
                "financing_activity",
                "net_cash_flow",
            ],
        }

        for dataset_name, columns in numeric_columns.items():

            df = self.cleaned_data[dataset_name]

            for column in columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

            self.cleaned_data[dataset_name] = df

        logger.info("Numeric conversion completed.")

    def remove_duplicate_business_records(self):
        """
        Remove duplicate business records based on composite business keys.
        Keeps the first occurrence.
        """
        logger.info("Cleaning Rule C-04: Removing duplicate business records...")

        business_keys = {
            "profitandloss": ["company_id", "year"],
            "balancesheet": ["company_id", "year"],
            "cashflow": ["company_id", "year"],
        }

        for dataset_name, keys in business_keys.items():

            df = self.cleaned_data[dataset_name]

            before = len(df)

            df = df.drop_duplicates(
                subset=keys,
                keep="first"
            )

            after = len(df)

            logger.info(
                f"{dataset_name}: Removed {before - after} duplicate business records."
            )

            self.cleaned_data[dataset_name] = df

        logger.info("Duplicate removal completed.")

    def export_cleaned_data(self, output_dir: str = "data/cleaned"):
        """
        Save cleaned datasets as CSV files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for name, df in self.cleaned_data.items():
            file_path = output_path / f"{name}.csv"
            df.to_csv(file_path, index=False)

        logger.info(f"Cleaned datasets exported to {output_path}")
