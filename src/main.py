from pathlib import Path

from src.etl.loader import ExcelLoader
from src.etl.validator import DataValidator


core_loader = ExcelLoader(Path("data/raw/core"))
supporting_loader = ExcelLoader(Path("data/raw/supporting"))

datasets = {
    **core_loader.load_all(),
    **supporting_loader.load_all()
}

validator = DataValidator(datasets)

validator.validate()

validator.summary()

validator.export_report()
