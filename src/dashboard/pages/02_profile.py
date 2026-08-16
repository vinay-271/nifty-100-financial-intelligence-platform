import pandas as pd
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_valuation,
)


st.title("Company Profile")

companies = get_companies()

if companies.empty:
    st.warning("No company data available.")
    st.stop()


# -------------------------------------------------------------------
# Company selector
# -------------------------------------------------------------------

company_options = companies["id"].tolist()

ticker = st.selectbox(
    "Select Company",
    company_options,
)

company = companies[
    companies["id"] == ticker
].iloc[0]


# -------------------------------------------------------------------
# Company header
# -------------------------------------------------------------------

st.subheader(company["company_name"])

if pd.notna(company.get("about_company")):
    st.write(company["about_company"])


# -------------------------------------------------------------------
# Company overview
# -------------------------------------------------------------------

st.markdown("### Company Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Ticker",
        ticker,
    )

with col2:
    st.metric(
        "Face Value",
        company["face_value"]
        if pd.notna(company["face_value"])
        else "N/A",
    )

with col3:
    st.metric(
        "Book Value",
        company["book_value"]
        if pd.notna(company["book_value"])
        else "N/A",
    )

with col4:
    st.metric(
        "ROE",
        (
            f"{company['roe_percentage']:.2f}%"
            if pd.notna(company["roe_percentage"])
            else "N/A"
        ),
    )


# -------------------------------------------------------------------
# Financial ratios
# -------------------------------------------------------------------

st.divider()
st.subheader("Financial Ratios")

ratios = get_ratios(ticker)

if ratios.empty:
    st.info("No financial ratio data available.")
else:
    # Use the latest annual financial-ratio record.
    # TTM currently does not contain ROE, ROCE, or D/E values.
    annual_ratios = ratios[
        ratios["year"].astype(str).str.match(r"^[A-Za-z]{3}\s\d{4}$")
    ].copy()

    if annual_ratios.empty:
        latest = ratios.iloc[-1]
    else:
        annual_ratios["fiscal_year"] = (
            annual_ratios["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        latest = annual_ratios.loc[
            annual_ratios["fiscal_year"].idxmax()
        ]

    ratio_columns = [
        (
            "Net Profit Margin",
            "net_profit_margin_pct",
            "%",
        ),
        (
            "Operating Profit Margin",
            "operating_profit_margin_pct",
            "%",
        ),
        (
            "ROE",
            "return_on_equity_pct",
            "%",
        ),
        (
            "ROCE",
            "return_on_capital_employed_pct",
            "%",
        ),
        (
            "Debt / Equity",
            "debt_to_equity",
            "",
        ),
        (
            "Interest Coverage",
            "interest_coverage",
            "x",
        ),
    ]

    cols = st.columns(3)

    for i, (label, column, suffix) in enumerate(
        ratio_columns
    ):
        value = latest.get(column)

        if value is None:
            display = "N/A"
        else:
            try:
                display = f"{float(value):.2f}{suffix}"
            except (TypeError, ValueError):
                display = "N/A"

        with cols[i % 3]:
            st.metric(label, display)


# -------------------------------------------------------------------
# Profit & Loss
# -------------------------------------------------------------------

st.divider()
st.subheader("Profit & Loss")

pl = get_pl(ticker)

if pl.empty:
    st.info("No profit & loss data available.")
else:
    display_columns = [
        column
        for column in [
            "year",
            "sales",
            "operating_profit",
            "net_profit",
            "eps",
            "dividend_payout",
        ]
        if column in pl.columns
    ]

    st.dataframe(
        pl[display_columns],
        use_container_width=True,
        hide_index=True,
    )


# -------------------------------------------------------------------
# Balance Sheet
# -------------------------------------------------------------------

st.divider()
st.subheader("Balance Sheet")

bs = get_bs(ticker)

if bs.empty:
    st.info("No balance sheet data available.")
else:
    display_columns = [
        column
        for column in [
            "year",
            "equity_capital",
            "reserves",
            "borrowings",
            "total_liabilities",
            "fixed_assets",
            "investments",
            "total_assets",
        ]
        if column in bs.columns
    ]

    st.dataframe(
        bs[display_columns],
        use_container_width=True,
        hide_index=True,
    )


# -------------------------------------------------------------------
# Cash Flow
# -------------------------------------------------------------------

st.divider()
st.subheader("Cash Flow")

cf = get_cf(ticker)

if cf.empty:
    st.info("No cash flow data available.")
else:
    display_columns = [
        column
        for column in [
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ]
        if column in cf.columns
    ]

    st.dataframe(
        cf[display_columns],
        use_container_width=True,
        hide_index=True,
    )


# -------------------------------------------------------------------
# Valuation
# -------------------------------------------------------------------

st.divider()
st.subheader("Valuation")

valuation = get_valuation(ticker)

if valuation.empty:
    st.info("No valuation data available.")
else:
    display_columns = [
        column
        for column in [
            "year",
            "market_cap_cr",
            "enterprise_value_cr",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ]
        if column in valuation.columns
    ]

    st.dataframe(
        valuation[display_columns],
        use_container_width=True,
        hide_index=True,
    )
