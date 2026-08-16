import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
)


st.title("Trend Analysis")

st.write(
    "Explore historical financial performance and growth trends "
    "for Nifty 100 companies."
)


# ---------------------------------------------------------------
# Company selection
# ---------------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.warning("No company data available.")
    st.stop()

company_options = companies["id"].tolist()

ticker = st.selectbox(
    "Select Company",
    company_options,
)

company = companies[
    companies["id"] == ticker
].iloc[0]

st.subheader(company["company_name"])


# ---------------------------------------------------------------
# Load data
# ---------------------------------------------------------------

ratios = get_ratios(ticker)
pl = get_pl(ticker)

if ratios.empty and pl.empty:
    st.warning("No historical financial data available.")
    st.stop()


# ---------------------------------------------------------------
# Financial Ratio Trends
# ---------------------------------------------------------------

st.divider()
st.subheader("Financial Ratio Trends")

if ratios.empty:
    st.info("No ratio history available.")
else:
    ratio_options = {
        "Return on Equity (ROE)": "return_on_equity_pct",
        "Return on Capital Employed (ROCE)": "return_on_capital_employed_pct",
        "Net Profit Margin": "net_profit_margin_pct",
        "Operating Profit Margin": "operating_profit_margin_pct",
        "Debt / Equity": "debt_to_equity",
        "Interest Coverage": "interest_coverage",
        "Asset Turnover": "asset_turnover",
    }

    selected_ratio = st.selectbox(
        "Select Ratio",
        list(ratio_options.keys()),
    )

    column = ratio_options[selected_ratio]

    trend = ratios[
        ["year", column]
    ].copy()

    trend[column] = pd.to_numeric(
        trend[column],
        errors="coerce",
    )

    trend = trend.dropna(subset=[column])

    if trend.empty:
        st.info("No valid data available for this ratio.")
    else:
        fig = px.line(
            trend,
            x="year",
            y=column,
            markers=True,
            title=selected_ratio,
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title=selected_ratio,
            hovermode="x unified",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ---------------------------------------------------------------
# Profitability Trends
# ---------------------------------------------------------------

st.divider()
st.subheader("Profitability Trends")

if pl.empty:
    st.info("No Profit & Loss history available.")
else:
    profit_columns = [
        column
        for column in [
            "sales",
            "operating_profit",
            "net_profit",
        ]
        if column in pl.columns
    ]

    if profit_columns:
        profit_data = pl[
            ["year"] + profit_columns
        ].copy()

        for column in profit_columns:
            profit_data[column] = pd.to_numeric(
                profit_data[column],
                errors="coerce",
            )

        long_data = profit_data.melt(
            id_vars="year",
            var_name="Metric",
            value_name="Value",
        )

        fig = px.line(
            long_data,
            x="year",
            y="Value",
            color="Metric",
            markers=True,
            title="Sales and Profit History",
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title="Value",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ---------------------------------------------------------------
# EPS Trend
# ---------------------------------------------------------------

if not pl.empty and "eps" in pl.columns:

    st.divider()
    st.subheader("EPS Trend")

    eps_data = pl[
        ["year", "eps"]
    ].copy()

    eps_data["eps"] = pd.to_numeric(
        eps_data["eps"],
        errors="coerce",
    )

    eps_data = eps_data.dropna(
        subset=["eps"]
    )

    if not eps_data.empty:

        fig = px.line(
            eps_data,
            x="year",
            y="eps",
            markers=True,
            title="Earnings Per Share",
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title="EPS",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ---------------------------------------------------------------
# Growth Summary
# ---------------------------------------------------------------

st.divider()
st.subheader("5-Year Growth Summary")

if ratios.empty:
    st.info("No ratio data available for CAGR analysis.")
else:

    # Use the latest annual ratio record.
    annual_ratios = ratios[
        ratios["year"]
        .astype(str)
        .str.match(r"^[A-Za-z]{3}\s\d{4}$")
    ].copy()

    if annual_ratios.empty:
        st.info("No annual ratio data available.")
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

        growth_metrics = [
            (
                "Revenue CAGR",
                "revenue_cagr_5yr",
            ),
            (
                "PAT CAGR",
                "pat_cagr_5yr",
            ),
            (
                "EPS CAGR",
                "eps_cagr_5yr",
            ),
        ]

        cols = st.columns(3)

        for col, (label, column) in zip(
            cols,
            growth_metrics,
        ):

            value = latest.get(column)

            if pd.isna(value):
                display = "N/A"
            else:
                display = f"{float(value):.2f}%"

            with col:
                st.metric(
                    label,
                    display,
                )
