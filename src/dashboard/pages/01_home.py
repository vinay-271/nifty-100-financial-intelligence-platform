import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import (
    get_companies,
    get_sectors,
    get_ratios_by_year,
    get_market_data_by_year,
)


st.title("Nifty 100 Overview")

st.caption(
    "Financial overview of the Nifty 100 universe."
)


# -------------------------------------------------------------------
# Load base data
# -------------------------------------------------------------------

companies = get_companies()
sectors = get_sectors()

if companies.empty:
    st.warning("No company data available.")
    st.stop()


# -------------------------------------------------------------------
# Year selector
# -------------------------------------------------------------------

available_years = [
    f"Mar {year}"
    for year in range(2019, 2025)
]

selected_year = st.selectbox(
    "Financial Year",
    available_years,
    index=len(available_years) - 1,
)


ratios = get_ratios_by_year(selected_year)
market_data = get_market_data_by_year(
    selected_year.replace("Mar ", "")
)

market_data["company_id"] = market_data["company_id"].astype(str)
ratios["company_id"] = ratios["company_id"].astype(str)

home_data = ratios.merge(
    market_data[
        [
            "company_id",
            "pe_ratio",
        ]
    ],
    on="company_id",
    how="left",
)

if ratios.empty:
    st.warning(
        f"No financial data available for {selected_year}."
    )
    st.stop()


# -------------------------------------------------------------------
# KPI calculations
# -------------------------------------------------------------------

roe = pd.to_numeric(
    home_data["return_on_equity_pct"],
    errors="coerce",
)

pe = pd.to_numeric(
    home_data["pe_ratio"],
    errors="coerce",
)

de = pd.to_numeric(
    home_data["debt_to_equity"],
    errors="coerce",
)

revenue_cagr = pd.to_numeric(
    home_data["revenue_cagr_5yr"],
    errors="coerce",
)

company_count = home_data["company_id"].nunique()

debt_free_count = (
    de.fillna(999999)
    .eq(0)
    .sum()
)


# -------------------------------------------------------------------
# KPI cards
# -------------------------------------------------------------------

st.subheader(f"Market Snapshot — {selected_year}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Average ROE",
        (
            f"{roe.mean():.2f}%"
            if roe.notna().any()
            else "N/A"
        ),
    )

with col2:
    st.metric(
        "Median P/E",
        (
            f"{pe.median():.2f}"
            if pe.notna().any()
            else "N/A"
        ),
    )

with col3:
    st.metric(
        "Median D/E",
        (
            f"{de.median():.2f}"
            if de.notna().any()
            else "N/A"
        ),
    )


col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        "Companies",
        company_count,
    )

with col5:
    st.metric(
        "Median Revenue CAGR",
        (
            f"{revenue_cagr.median():.2f}%"
            if revenue_cagr.notna().any()
            else "N/A"
        ),
    )

with col6:
    st.metric(
        "Debt-Free Companies",
        int(debt_free_count),
    )


# -------------------------------------------------------------------
# Sector distribution
# -------------------------------------------------------------------

st.divider()
st.subheader("Sector Distribution")

if sectors.empty or "sector" not in sectors.columns:
    st.warning("No sector data available.")
else:
    sector_counts = (
        sectors.groupby("sector")
        .size()
        .reset_index(name="Companies")
        .sort_values("Companies", ascending=False)
    )

    fig = px.pie(
        sector_counts,
        names="sector",
        values="Companies",
        hole=0.45,
    )

    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        legend_title="Sector",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# -------------------------------------------------------------------
# Top 5 Composite Quality Companies
# -------------------------------------------------------------------

st.divider()

st.subheader(
    f"Top 5 Companies by Composite Quality Score — {selected_year}"
)

top5 = home_data[
    [
        "company_id",
        "composite_quality_score",
    ]
].copy()

top5["composite_quality_score"] = pd.to_numeric(
    top5["composite_quality_score"],
    errors="coerce",
)

top5 = (
    top5
    .dropna(subset=["composite_quality_score"])
    .sort_values(
        "composite_quality_score",
        ascending=False,
    )
    .head(5)
)

if top5.empty:
    st.info(
        "No composite quality scores are available "
        f"for {selected_year}."
    )
else:
    top5 = top5.merge(
        companies[
            ["id", "company_name"]
        ],
        left_on="company_id",
        right_on="id",
        how="left",
    )

    top5["Company"] = (
        top5["company_id"]
        + " — "
        + top5["company_name"].fillna("")
    )

    top5_display = top5[
        [
            "Company",
            "composite_quality_score",
        ]
    ].rename(
        columns={
            "composite_quality_score": "Composite Score",
        }
    )

    top5_display["Composite Score"] = (
        top5_display["Composite Score"].round(2)
    )

    st.dataframe(
        top5_display,
        use_container_width=True,
        hide_index=True,
    )
