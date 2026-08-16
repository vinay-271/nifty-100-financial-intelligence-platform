import streamlit as st
import pandas as pd

from src.dashboard.utils.db import (
    get_companies,
    get_sectors,
    get_ratios,
    get_latest_period,
)


st.title("Nifty 100 Overview")

st.caption(
    "Financial overview of the Nifty 100 universe based on the project database."
)


# -------------------------------------------------------------------
# Load data
# -------------------------------------------------------------------

companies = get_companies()
sectors = get_sectors()


# -------------------------------------------------------------------
# KPI calculations
# -------------------------------------------------------------------

company_count = companies["id"].nunique()

sector_count = sectors["sector"].nunique()

latest_year = get_latest_period()


# -------------------------------------------------------------------
# KPI cards
# -------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Companies Covered",
        company_count,
    )

with col2:
    st.metric(
        "Sectors Covered",
        sector_count,
    )

with col3:
    st.metric(
        "Latest Financial Period",
        latest_year if latest_year else "N/A",
    )


st.divider()


# -------------------------------------------------------------------
# Company universe
# -------------------------------------------------------------------

st.subheader("Company Universe")

if not companies.empty:
    display_columns = [
        column
        for column in [
            "id",
            "company_name",
            "sector",
        ]
        if column in companies.columns
    ]

    st.dataframe(
        companies[display_columns],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("No company data available.")


# -------------------------------------------------------------------
# Sector distribution
# -------------------------------------------------------------------

st.subheader("Sector Distribution")

if not sectors.empty and "sector" in sectors.columns:
    sector_counts = (
        sectors.groupby("sector")
        .size()
        .sort_values(ascending=False)
    )

    st.bar_chart(sector_counts)

else:
    st.warning("No sector data available.")
