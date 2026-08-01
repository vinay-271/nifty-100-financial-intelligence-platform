from pathlib import Path

from etl.loader import ExcelLoader
from etl.cleaner import DataCleaner

loader = ExcelLoader(
    Path("data/raw")
)

datasets = loader.load_all()

cleaner = DataCleaner()

cleaner.clean(datasets)

print("Cleaning completed successfully.")
