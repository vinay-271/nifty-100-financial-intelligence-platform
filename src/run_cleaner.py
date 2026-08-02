from pathlib import Path

from src.etl.loader import ExcelLoader
from src.etl.cleaner import DataCleaner

loader = ExcelLoader(
    Path("data/raw")
)

datasets = loader.load_all()

cleaner = DataCleaner()

cleaner.clean(datasets)

print("Cleaning completed successfully.")
