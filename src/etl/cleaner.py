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
        logger.info("Starting data cleaning...")

        self.cleaned_data = {
            name: df.copy(deep=True)
            for name, df in datasets.items()
        }

        self.trim_whitespace()
        self.normalize_missing_values()
        self.convert_numeric_columns()

        self.normalize_stock_price_columns()
        self.normalize_financial_ratio_columns()
        self.normalize_market_cap_columns()
        self.normalize_peer_groups_columns()
        self.normalize_sectors_columns()

        self.remove_duplicate_business_records()

        self.export_cleaned_data()

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
            "financial_ratios": ["company_id", "year"],
            "market_cap": ["company_id", "year"],
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
            if name == "financial_ratios":
                print("\nExporting financial_ratios with columns:")
                print(df.columns.tolist())
            file_path = output_path / f"{name}.csv"
            df.to_csv(file_path, index=False)

        logger.info(f"Cleaned datasets exported to {output_path}")

    def normalize_stock_price_columns(self):
        """
        Cleaning Rule C-05:
        Rename stock_prices columns to standard names.
        """

        logger.info("Cleaning Rule C-05: Normalizing stock_prices columns...")

        df = self.cleaned_data["stock_prices"]

        df.columns = [
            "id",
            "company_id",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "adjusted_close",
        ]

        self.cleaned_data["stock_prices"] = df

        logger.info("Stock price columns normalized.")

    def normalize_financial_ratio_columns(self):
        df = self.cleaned_data["financial_ratios"]

        print("Before: ")
        print(df.columns.tolist())

        df.columns = [
            "id",
            "company_id",
            "year",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "free_cash_flow_cr",
            "capex_cr",
            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",
            "total_debt_cr",
            "cash_from_operations_cr",
        ]

        print("After: ")
        print(df.columns.tolist())

        self.cleaned_data["financial_ratios"] = df

    def normalize_market_cap_columns(self):
        """
        Cleaning Rule C-07: Normalize market_cap column names.
        """

        logger.info("Cleaning Rule C-07: Normalizing market_cap columns...")

        df = self.cleaned_data["market_cap"]

        df.columns = [
            "id",
            "company_id",
            "year",
            "market_cap_cr",
            "enterprise_value_cr",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ]

        self.cleaned_data["market_cap"] = df

        logger.info("Market cap columns normalized.")

    def normalize_peer_groups_columns(self):
        """
        Cleaning Rule C-08: Normalize peer_groups columns.
        """

        logger.info("Cleaning Rule C-08: Normalizing peer_groups columns...")

        df = self.cleaned_data["peer_groups"]

        df.columns = [
            "id",
            "peer_group",
            "company_id",
            "is_primary_company",
        ]

        self.cleaned_data["peer_groups"] = df

        logger.info("Peer groups columns normalized.")

    def normalize_sectors_columns(self):
        """
        Cleaning Rule C-09: Normalize sectors columns.
        """

        logger.info("Cleaning Rule C-09: Normalizing sectors columns...")

        df = self.cleaned_data["sectors"]

        df.columns = [
            "id",
            "company_id",
            "sector",
            "industry",
            "weight_pct",
            "market_cap_category",
        ]

        self.cleaned_data["sectors"] = df

        logger.info("Sectors columns normalized.")
