import pytest

from src.etl.normaliser import normalize_year


@pytest.mark.parametrize(
    "input_value, expected",
    [
        (2024, 2024),
        ("2024", 2024),
        ("FY2024", 2024),
        ("FY 2024", 2024),
        ("2024-25", 2024),
        ("2024/25", 2024),
        ("FY2023-24", 2023),
        ("FY 2022-23", 2022),
        ("2019", 2019),
        ("1998", 1998),
        ("FY1998", 1998),
        ("FY 2001", 2001),
        ("2020-2021", 2020),
        ("FY20", None),
        ("ABC", None),
        ("", None),
        (None, None),
        ("-", None),
        ("N/A", None),
        ("Financial Year 2025", 2025),
    ],
)
def test_normalize_year(input_value, expected):
    assert normalize_year(input_value) == expected
