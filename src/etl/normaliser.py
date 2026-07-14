"""
Data normalization utilities for the N100 ETL pipeline.
"""

import re
import pandas as pd


def normalize_year(value):
    """
    Convert different year formats into integer years.

    Examples
    --------
    2024 -> 2024
    "2024" -> 2024
    "FY2024" -> 2024
    "FY 2024" -> 2024
    "2024-25" -> 2024
    "2024/25" -> 2024
    """

    if pd.isna(value):
        return None

    if isinstance(value, int):
        return value

    value = str(value).strip().upper()

    match = re.search(r"(19|20)\d{2}", value)

    if match:
        return int(match.group())

    return None


def normalize_ticker(value):
    """
    Standardize stock ticker symbols.

    Examples
    --------
    tcs -> TCS
    TCS.NS -> TCS
    TCS.BO -> TCS
    INFY NS -> INFY
    """

    if pd.isna(value):
        return None

    ticker = str(value).strip().upper()

    ticker = ticker.replace(".NS", "")
    ticker = ticker.replace(".BO", "")
    ticker = ticker.replace(" NSE", "")
    ticker = ticker.replace(" BSE", "")
    ticker = ticker.replace(" ", "")

    return ticker

def normalize_headers(df):
    """
    Standardize DataFrame column names.

    Example:
    "Company Name" -> "company_name"
    "Market Cap (Cr.)" -> "market_cap_cr"
    """

    columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
        .str.replace("/", "_", regex=False)
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace(".", "", regex=False)
    )

    df.columns = columns

    return df
