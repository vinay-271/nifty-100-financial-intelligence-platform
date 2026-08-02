import pytest

from src.etl.normaliser import normalize_ticker


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("tcs", "TCS"),
        ("TCS", "TCS"),
        (" TCS ", "TCS"),
        ("TCS.NS", "TCS"),
        ("TCS.BO", "TCS"),
        ("INFY NSE", "INFY"),
        ("INFY BSE", "INFY"),
        ("RELIANCE", "RELIANCE"),
        (" reliance ", "RELIANCE"),
        ("hdfcbank.ns", "HDFCBANK"),
        ("axisbank.bo", "AXISBANK"),
        ("SBIN NSE", "SBIN"),
        ("SBIN BSE", "SBIN"),
        ("LTIM", "LTIM"),
        ("LTIM.NS", "LTIM"),
        ("LTIM BO", "LTIMBO"),
        ("M&M", "M&M"),
        ("BAJAJ-AUTO", "BAJAJ-AUTO"),
        ("", ""),
        (None, None),
        (float("nan"), None),
    ]
)
def test_normalize_ticker(input_value, expected):
    assert normalize_ticker(input_value) == expected
