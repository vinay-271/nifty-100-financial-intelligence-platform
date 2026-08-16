import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import (
    get_sectors,
    get_companies,
    get_ratios,
)


st.title("Sector Analysis")

st.write(
    "Explore the composition and financial characteristics "
    "of the Nifty 100 sectors."
)


# ---------------------------------------------------------------
# Load data
# ---------------------------------------------------------------

sectors = get_sectors()
companies = get_companies()

if sectors.empty:
    st.warning("No sector data available.")
    st.stop()


# ---------------------------------------------------------------
# Sector Distribution
# ---------------------------------------------------------------

st.subheader("Sector Distribution")

sector_counts = (
    sectors.groupby("sector")
    .size()
    .reset_index(name="companies")
    .sort_values(
        "companies",
        ascending=False,
    )
)

fig = px.pie(
    sector_counts,
    names="sector",
    values="companies",
    hole=0.45,
    title="Nifty 100 Sector Composition",
)

fig.update_traces(
    textposition="inside",
    textinfo="percent",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# ---------------------------------------------------------------
# Sector Selection
# ---------------------------------------------------------------

st.divider()

st.subheader("Sector Details")

sector_options = sector_counts[
    "sector"
].tolist()

selected_sector = st.selectbox(
    "Select Sector",
    sector_options,
)


# ---------------------------------------------------------------
# Selected Sector Data
# ---------------------------------------------------------------

sector_data = sectors[
    sectors["sector"] == selected_sector
].copy()

company_ids = sector_data[
    "company_id"
].dropna().unique().tolist()

sector_companies = companies[
    companies["id"].isin(company_ids)
].copy()


# ---------------------------------------------------------------
# Sector KPIs
# ---------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Companies",
        len(sector_companies),
    )

with col2:
    st.metric(
        "Sector Weight",
        f"{sector_data['weight_pct'].sum():.2f}%",
    )

with col3:
    large_cap_count = (
        sector_data[
            sector_data["market_cap_category"]
            == "Large Cap"
        ]
        .shape[0]
    )

    st.metric(
        "Large Cap",
        large_cap_count,
    )

with col4:
    industry_count = sector_data[
        "industry"
    ].nunique()

    st.metric(
        "Industries",
        industry_count,
    )


# ---------------------------------------------------------------
# Companies
# ---------------------------------------------------------------

st.divider()

st.subheader(
    f"Companies — {selected_sector}"
)

display_columns = [
    column
    for column in [
        "id",
        "company_name",
    ]
    if column in sector_companies.columns
]

st.dataframe(
    sector_companies[
        display_columns
    ],
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------------
# Industry Distribution
# ---------------------------------------------------------------

st.divider()

st.subheader("Industry Distribution")

industry_counts = (
    sector_data
    .groupby("industry")
    .size()
    .reset_index(name="companies")
    .sort_values(
        "companies",
        ascending=False,
    )
)

fig = px.bar(
    industry_counts,
    x="industry",
    y="companies",
    text="companies",
    title=f"Industries within {selected_sector}",
)

fig.update_layout(
    xaxis_title="Industry",
    yaxis_title="Companies",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# ---------------------------------------------------------------
# Sector Financial Metrics
# ---------------------------------------------------------------

st.divider()

st.subheader("Sector Financial Metrics")

ratio_records = []

for company_id in company_ids:

    ratios = get_ratios(company_id)

    if ratios.empty:
        continue

    # -----------------------------------------------------------
    # Select latest annual observation
    # -----------------------------------------------------------

    annual = ratios[
        ratios["year"]
        .astype(str)
        .str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )
    ].copy()

    if annual.empty:
        continue

    annual["fiscal_year"] = (
        annual["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0]
        .astype(int)
    )

    latest = annual.loc[
        annual["fiscal_year"].idxmax()
    ]

    ratio_records.append(
        {
            "company_id": company_id,

            "ROE": latest.get(
                "return_on_equity_pct"
            ),

            "ROCE": latest.get(
                "return_on_capital_employed_pct"
            ),

            "Net Profit Margin": latest.get(
                "net_profit_margin_pct"
            ),

            "Debt / Equity": latest.get(
                "debt_to_equity"
            ),

            "Interest Coverage": latest.get(
                "interest_coverage"
            ),

            "Revenue CAGR": latest.get(
                "revenue_cagr_5yr"
            ),

            "PAT CAGR": latest.get(
                "pat_cagr_5yr"
            ),

            "EPS CAGR": latest.get(
                "eps_cagr_5yr"
            ),

            "Quality Score": latest.get(
                "composite_quality_score"
            ),
        }
    )


if not ratio_records:

    st.info(
        "No financial ratio data available "
        "for this sector."
    )

else:

    ratio_df = pd.DataFrame(
        ratio_records
    )

    metric_columns = [
        "ROE",
        "ROCE",
        "Net Profit Margin",
        "Debt / Equity",
        "Interest Coverage",
        "Revenue CAGR",
        "PAT CAGR",
        "EPS CAGR",
        "Quality Score",
    ]

    # -----------------------------------------------------------
    # Sector averages
    # -----------------------------------------------------------

    averages = (
        ratio_df[
            metric_columns
        ]
        .mean()
        .to_frame("Sector Average")
        .round(2)
    )

    st.dataframe(
        averages,
        use_container_width=True,
    )


    # -----------------------------------------------------------
    # Metric Comparison
    # -----------------------------------------------------------

    st.subheader(
        "Company Comparison"
    )

    selected_metric = st.selectbox(
        "Select Financial Metric",
        metric_columns,
    )

    chart_data = ratio_df[
        [
            "company_id",
            selected_metric,
        ]
    ].dropna()

    chart_data = chart_data.sort_values(
        selected_metric,
        ascending=False,
    )

    if chart_data.empty:

        st.info(
            "No data available for this metric."
        )

    else:

        fig = px.bar(
            chart_data,
            x="company_id",
            y=selected_metric,
            text=selected_metric,
            title=(
                f"{selected_metric} — "
                f"{selected_sector}"
            ),
        )

        fig.update_layout(
            xaxis_title="Company",
            yaxis_title=selected_metric,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


    # -----------------------------------------------------------
    # Detailed Financial Metrics
    # -----------------------------------------------------------

    st.subheader(
        "Company Financial Metrics"
    )

    detailed = ratio_df.copy()

    detailed = detailed.merge(
        sector_companies[
            [
                "id",
                "company_name",
            ]
        ],
        left_on="company_id",
        right_on="id",
        how="left",
    )

    detailed = detailed.drop(
        columns=["id"],
        errors="ignore",
    )

    detailed = detailed.rename(
        columns={
            "company_id": "Ticker",
            "company_name": "Company",
        }
    )

    column_order = [
        "Ticker",
        "Company",
    ] + metric_columns

    detailed = detailed[
        [
            column
            for column in column_order
            if column in detailed.columns
        ]
    ]

    st.dataframe(
        detailed,
        use_container_width=True,
        hide_index=True,
    )
