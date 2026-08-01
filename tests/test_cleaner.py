import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.etl.loader import ExcelLoader
from src.etl.cleaner import DataCleaner

loader = ExcelLoader()
datasets = loader.load_all()

cleaner = DataCleaner()
cleaned = cleaner.clean(datasets)

cleaner.export_cleaned_data()

print("Cleaning completed successfully.")
