"""
Excel loading utilities for the N100 Financial Intelligence Platform.
"""

from pathlib import Path
import pandas as pd
from loguru import logger
from etl.normaliser import normalize_headers
from config import EXCEL_HEADER_ROW

class ExcelLoader:
    """
    Generic Excel Loader for all project datasets.
    """

    def __init__(self, data_directory: Path):
        self.data_directory = Path(data_directory)

    def discover_excel_files(self):
        """
        Recursively discover all Excel files.
        """

        files = sorted(self.data_directory.rglob("*.xlsx"))

        logger.info(f"Discovered {len(files)} Excel files.")

        return files

    def load_excel(self, filepath: Path, sheet_name=0):
        """
        Load a single Excel file.
        """

        try:

            df = pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                header=EXCEL_HEADER_ROW
            )
            """
                Load a single Excel workbook.

                Notes
                -----
                The N100 source datasets contain a metadata/title row
                followed by the actual header row.

                Therefore we read the Excel sheet using:

                    header=1

                so that pandas treats the second row as column names.
            """

            df = normalize_headers(df)

            logger.info(
                f"{filepath.name} loaded successfully "
                f"({df.shape[0]} rows × {df.shape[1]} columns)"
            )

            return df

        except Exception as e:

            logger.error(f"Failed to load {filepath.name}")

            logger.exception(e)

            raise

    def preview(self, df, rows=5):
        """
        Return first few rows.
        """

        return df.head(rows)

    def get_shape(self, df):

        return df.shape

    def get_columns(self, df):

        return list(df.columns)

    def load_all(self):
        """
        Load every Excel file into a dictionary.
        """

        datasets = {}

        files = self.discover_excel_files()

        for file in files:

            datasets[file.stem] = self.load_excel(file)

        logger.info(
            f"Loaded {len(datasets)} datasets."
        )

        return datasets
