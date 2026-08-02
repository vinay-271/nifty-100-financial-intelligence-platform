from pathlib import Path

from src.etl.loader import ExcelLoader
from src.etl.cleaner import DataCleaner


def test_cleaner_pipeline():

    loader = ExcelLoader(Path("data/raw"))

    datasets = loader.load_all()

    cleaner = DataCleaner()

    cleaned = cleaner.clean(datasets)

    assert cleaned is not None
    assert isinstance(cleaned, dict)
    assert len(cleaned) > 0

    # Ensure expected datasets exist
    assert "companies" in cleaned
    assert "profitandloss" in cleaned
    assert "balancesheet" in cleaned
    assert "cashflow" in cleaned
