import pytest

from src.etl.normaliser import normalize_year


@pytest.mark.parametrize(
    "input_value, expected",
    [
        (2024, 2024),
        (1999, 1999),
        ("2024", 2024),
        ("1998", 1998),
        ("FY2024", 2024),
        ("FY 2024", 2024),
        ("FY2023-24", 2023),
        ("2024-25", 2024),
        ("2024/25", 2024),
        ("Mar 2024", 2024),
        ("Dec 2023", 2023),
        ("Year 2022", 2022),
        (" 2021 ", 2021),
        ("FY-2020", 2020),
        ("2019 Annual Report", 2019),
        ("abc2024xyz", 2024),
        ("Q1 FY2024", 2024),
        ("FY19", None),
        ("", None),
        ("abcd", None),
        (None, None),
        (float("nan"), None),
    ]
)
def test_normalize_year(input_value, expected):
    assert normalize_year(input_value) == expected
