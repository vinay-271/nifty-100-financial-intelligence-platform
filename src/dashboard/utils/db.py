from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


DB_PATH = Path("db/nifty100.db")


def _get_connection():
    """Create a new SQLite connection."""
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def get_companies():
    """Return the Nifty 100 company master data."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM companies
            ORDER BY company_name
            """,
            conn,
        )


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """Return financial ratios for a company."""
    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
    """
    params = [ticker]

    if year is not None:
        query += " AND year = ?"
        params.append(year)

    query += """
        ORDER BY
            CASE WHEN year = 'TTM' THEN 1 ELSE 0 END,
            year DESC
    """

    with _get_connection() as conn:
        return pd.read_sql(query, conn, params=params)

@st.cache_data(ttl=600)
def get_ratios_by_year(year):
    """Return financial ratios for all companies for one annual period."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM financial_ratios
            WHERE year = ?
            """,
            conn,
            params=[year],
        )

@st.cache_data(ttl=600)
def get_pl(ticker):
    """Return profit and loss history for a company."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM profitandloss
            WHERE company_id = ?
            ORDER BY year
            """,
            conn,
            params=[ticker],
        )


@st.cache_data(ttl=600)
def get_bs(ticker):
    """Return balance sheet history for a company."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM balancesheet
            WHERE company_id = ?
            ORDER BY year
            """,
            conn,
            params=[ticker],
        )


@st.cache_data(ttl=600)
def get_cf(ticker):
    """Return cash flow history for a company."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM cashflow
            WHERE company_id = ?
            ORDER BY year
            """,
            conn,
            params=[ticker],
        )


@st.cache_data(ttl=600)
def get_sectors():
    """Return sector mappings."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM sectors
            ORDER BY sector
            """,
            conn,
        )


@st.cache_data(ttl=600)
def get_peers(group_name):
    """Return companies and percentile metrics for a peer group."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM peer_percentiles
            WHERE peer_group_name = ?
            ORDER BY company_id, metric
            """,
            conn,
            params=[group_name],
        )


@st.cache_data(ttl=600)
def get_valuation(ticker):
    """Return valuation data for a company."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM market_cap
            WHERE company_id = ?
            ORDER BY year
            """,
            conn,
            params=[ticker],
        )


@st.cache_data(ttl=600)
def get_latest_period():
    """Return the latest financial reporting period in the database."""
    with _get_connection() as conn:
        result = pd.read_sql(
            """
            SELECT year
            FROM financial_ratios
            WHERE year NOT LIKE 'TTM'
            ORDER BY
                CAST(substr(year, 5, 4) AS INTEGER) DESC,
                CASE substr(year, 1, 3)
                    WHEN 'Jan' THEN 1
                    WHEN 'Feb' THEN 2
                    WHEN 'Mar' THEN 3
                    WHEN 'Apr' THEN 4
                    WHEN 'May' THEN 5
                    WHEN 'Jun' THEN 6
                    WHEN 'Jul' THEN 7
                    WHEN 'Aug' THEN 8
                    WHEN 'Sep' THEN 9
                    WHEN 'Oct' THEN 10
                    WHEN 'Nov' THEN 11
                    WHEN 'Dec' THEN 12
                END DESC
            LIMIT 1
            """,
            conn,
        )

    if result.empty:
        return "N/A"

    return result.iloc[0]["year"]

@st.cache_data(ttl=600)
def get_market_data_by_year(year):
    """Return market and valuation data for one financial year."""
    with _get_connection() as conn:
        return pd.read_sql(
            """
            SELECT *
            FROM market_cap
            WHERE year = ?
            """,
            conn,
            params=[year],
        )
