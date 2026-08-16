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
# Sector distribution
# ---------------------------------------------------------------

st.subheader("Sector Distribution")

sector_counts = (
    sectors.groupby("sector")
    .size()
    .reset_index(name="companies")
    .sort_values("companies", ascending=False)
)

fig = px.bar(
    sector_counts,
    x="sector",
    y="companies",
    title="Companies by Sector",
    text="companies",
)

fig.update_layout(
    xaxis_title="Sector",
    yaxis_title="Number of Companies",
)

st.plotly_chart(
    fig,
    use_container_width=True,
)


# ---------------------------------------------------------------
# Sector selection
# ---------------------------------------------------------------

st.divider()
st.subheader("Sector Details")

sector_options = sector_counts["sector"].tolist()

selected_sector = st.selectbox(
    "Select Sector",
    sector_options,
)


# ---------------------------------------------------------------
# Sector companies
# ---------------------------------------------------------------

sector_companies = sectors[
    sectors["sector"] == selected_sector
].copy()

company_ids = sector_companies["company_id"].tolist()

sector_company_data = companies[
    companies["id"].isin(company_ids)
].copy()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Companies",
        len(sector_company_data),
    )

with col2:
    st.metric(
        "Sector",
        selected_sector,
    )


st.markdown("### Companies")

display_columns = [
    column
    for column in [
        "id",
        "company_name",
    ]
    if column in sector_company_data.columns
]

st.dataframe(
    sector_company_data[display_columns],
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------------
# Sector financial metrics
# ---------------------------------------------------------------

st.divider()
st.subheader("Sector Financial Metrics")

ratio_records = []

for company_id in company_ids:

    ratios = get_ratios(company_id)

    if ratios.empty:
        continue

    # Use latest annual observation.
    annual = ratios[
        ratios["year"].astype(str).str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )
    ]

    if annual.empty:
        continue

    latest = annual.iloc[-1]

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

    numeric_columns = [
        "ROE",
        "ROCE",
        "Net Profit Margin",
        "Debt / Equity",
        "Interest Coverage",
    ]

    averages = (
        ratio_df[numeric_columns]
        .mean()
        .to_frame("Sector Average")
        .round(2)
    )

    st.dataframe(
        averages,
        use_container_width=True,
    )


    # -----------------------------------------------------------
    # Metric comparison chart
    # -----------------------------------------------------------

    metric = st.selectbox(
        "Compare Sector Metric",
        numeric_columns,
    )

    chart_data = ratio_df[
        ["company_id", metric]
    ].dropna()

    if not chart_data.empty:

        chart_data = chart_data.sort_values(
            metric,
            ascending=False,
        )

        fig = px.bar(
            chart_data,
            x="company_id",
            y=metric,
            title=f"{metric} — {selected_sector}",
        )

        fig.update_layout(
            xaxis_title="Company",
            yaxis_title=metric,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )
