import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import (
    get_companies,
    get_cf,
    get_bs,
    get_ratios,
)


st.title("Capital Allocation")

st.write(
    "Analyse how companies generate, invest, and deploy capital "
    "through operating cash flow, capital expenditure, free cash flow, "
    "and debt."
)


# ---------------------------------------------------------------
# Company selection
# ---------------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.warning("No company data available.")
    st.stop()

ticker = st.selectbox(
    "Select Company",
    companies["id"].tolist(),
)

company = companies[
    companies["id"] == ticker
].iloc[0]

st.subheader(company["company_name"])


# ---------------------------------------------------------------
# Load financial data
# ---------------------------------------------------------------

cf = get_cf(ticker)
bs = get_bs(ticker)
ratios = get_ratios(ticker)


if cf.empty and ratios.empty:
    st.warning("No capital allocation data available.")
    st.stop()


# ---------------------------------------------------------------
# Cash Flow Analysis
# ---------------------------------------------------------------

st.divider()
st.subheader("Cash Flow Analysis")

if cf.empty:
    st.info("No cash flow history available.")
else:

    cf_columns = [
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

    cf_display = cf[cf_columns].copy()

    st.dataframe(
        cf_display,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------
# Capital Allocation Metrics
# ---------------------------------------------------------------

st.divider()
st.subheader("Capital Allocation Metrics")

if ratios.empty:
    st.info("No ratio data available.")
else:

    annual = ratios[
        ratios["year"].astype(str).str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )
    ].copy()

    if annual.empty:
        latest = ratios.iloc[-1]
    else:
        annual["fiscal_year"] = (
            annual["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        latest = annual.loc[
            annual["fiscal_year"].idxmax()
        ]

    metrics = [
        (
            "Free Cash Flow",
            "free_cash_flow_cr",
            "Cr",
        ),
        (
            "Cash From Operations",
            "cash_from_operations_cr",
            "Cr",
        ),
        (
            "Capex",
            "capex_cr",
            "Cr",
        ),
        (
            "Total Debt",
            "total_debt_cr",
            "Cr",
        ),
    ]

    cols = st.columns(4)

    for i, (label, column, suffix) in enumerate(metrics):

        value = latest.get(column)

        if pd.isna(value):
            display = "N/A"
        else:
            display = f"{float(value):,.2f} {suffix}"

        with cols[i]:
            st.metric(
                label,
                display,
            )


# ---------------------------------------------------------------
# Operating Cash Flow vs Capex
# ---------------------------------------------------------------

st.divider()
st.subheader("Operating Cash Flow vs Capex")

if ratios.empty:
    st.info("No historical ratio data available.")
else:

    chart_columns = [
        column
        for column in [
            "year",
            "cash_from_operations_cr",
            "capex_cr",
        ]
        if column in ratios.columns
    ]

    if len(chart_columns) == 3:

        chart_data = ratios[
            chart_columns
        ].copy()

        chart_data = chart_data[
            chart_data["year"]
            .astype(str)
            .str.match(r"^[A-Za-z]{3}\s\d{4}$")
        ]

        chart_data["cash_from_operations_cr"] = (
            pd.to_numeric(
                chart_data["cash_from_operations_cr"],
                errors="coerce",
            )
        )

        chart_data["capex_cr"] = (
            pd.to_numeric(
                chart_data["capex_cr"],
                errors="coerce",
            )
        )

        chart_data = chart_data.dropna(
            subset=[
                "cash_from_operations_cr",
                "capex_cr",
            ]
        )

        if not chart_data.empty:

            long_data = chart_data.melt(
                id_vars="year",
                value_vars=[
                    "cash_from_operations_cr",
                    "capex_cr",
                ],
                var_name="Metric",
                value_name="Amount",
            )

            long_data["Metric"] = long_data[
                "Metric"
            ].replace(
                {
                    "cash_from_operations_cr":
                        "Cash From Operations",
                    "capex_cr":
                        "Capex",
                }
            )

            fig = px.bar(
                long_data,
                x="year",
                y="Amount",
                color="Metric",
                barmode="group",
                title="Operating Cash Flow vs Capital Expenditure",
            )

            fig.update_layout(
                xaxis_title="Financial Year",
                yaxis_title="₹ Crore",
                hovermode="x unified",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


# ---------------------------------------------------------------
# Free Cash Flow Trend
# ---------------------------------------------------------------

st.divider()
st.subheader("Free Cash Flow Trend")

if ratios.empty:
    st.info("No FCF history available.")
else:

    fcf_data = ratios[
        [
            "year",
            "free_cash_flow_cr",
        ]
    ].copy()

    fcf_data = fcf_data[
        fcf_data["year"]
        .astype(str)
        .str.match(r"^[A-Za-z]{3}\s\d{4}$")
    ]

    fcf_data["free_cash_flow_cr"] = pd.to_numeric(
        fcf_data["free_cash_flow_cr"],
        errors="coerce",
    )

    fcf_data = fcf_data.dropna(
        subset=["free_cash_flow_cr"]
    )

    if not fcf_data.empty:

        fig = px.line(
            fcf_data,
            x="year",
            y="free_cash_flow_cr",
            markers=True,
            title="Free Cash Flow",
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title="₹ Crore",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ---------------------------------------------------------------
# Debt Trend
# ---------------------------------------------------------------

st.divider()
st.subheader("Debt Trend")

if ratios.empty or "total_debt_cr" not in ratios.columns:
    st.info("No debt history available.")
else:

    debt_data = ratios[
        [
            "year",
            "total_debt_cr",
        ]
    ].copy()

    debt_data = debt_data[
        debt_data["year"]
        .astype(str)
        .str.match(r"^[A-Za-z]{3}\s\d{4}$")
    ]

    debt_data["total_debt_cr"] = pd.to_numeric(
        debt_data["total_debt_cr"],
        errors="coerce",
    )

    debt_data = debt_data.dropna(
        subset=["total_debt_cr"]
    )

    if not debt_data.empty:

        fig = px.line(
            debt_data,
            x="year",
            y="total_debt_cr",
            markers=True,
            title="Total Debt",
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title="₹ Crore",
            hovermode="x unified",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )
