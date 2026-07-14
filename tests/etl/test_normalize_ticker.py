import pytest

from src.etl.normaliser import normalize_ticker


@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("TCS", "TCS"),
        ("tcs", "TCS"),
        ("tcs.ns", "TCS"),
        ("TCS.NS", "TCS"),
        ("INFY.BO", "INFY"),
        ("infy.bo", "INFY"),
        (" INFY ", "INFY"),
        ("SBIN NSE", "SBIN"),
        ("RELIANCE BSE", "RELIANCE"),
        ("HDFCBANK", "HDFCBANK"),
        ("LT", "LT"),
        ("M&M", "M&M"),
        ("BAJAJ-AUTO", "BAJAJ-AUTO"),
        (None, None),
        ("", ""),
    ],
)
def test_normalize_ticker(input_value, expected):
    assert normalize_ticker(input_value) == expected
