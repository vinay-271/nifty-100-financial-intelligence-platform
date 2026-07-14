from pathlib import Path

from src.etl.loader import ExcelLoader

loader = ExcelLoader(Path("data/raw"))

datasets = loader.load_all()

print()

print(datasets.keys())

print()

companies = datasets["companies"]

print(companies.head())

print()

print(companies.columns.tolist())
