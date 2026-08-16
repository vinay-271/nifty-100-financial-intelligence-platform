import streamlit as st
import pandas as pd

from src.dashboard.utils.db import get_peers


st.title("Peer Comparison")

st.write(
    "Compare companies within their assigned peer groups "
    "using percentile-ranked financial metrics."
)


# ---------------------------------------------------------------
# Peer group selection
# ---------------------------------------------------------------

peer_groups = [
    "Automobiles",
    "Consumer Finance",
    "FMCG",
    "IT Services",
    "Life Insurance",
    "Oil & Gas",
    "Pharmaceuticals",
    "Power & Utilities",
    "Private Banks",
    "Public Sector Banks",
    "Steel",
]

peer_group = st.selectbox(
    "Select Peer Group",
    peer_groups,
)


# ---------------------------------------------------------------
# Load peer data
# ---------------------------------------------------------------

data = get_peers(peer_group)

if data.empty:
    st.warning("No peer data available for this group.")
    st.stop()


# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------

st.divider()

companies = data["company_id"].nunique()
metrics = data["metric"].nunique()

col1, col2 = st.columns(2)

with col1:
    st.metric("Companies", companies)

with col2:
    st.metric("Metrics", metrics)


# ---------------------------------------------------------------
# Convert percentile data into company-level table
# ---------------------------------------------------------------

pivot = data.pivot_table(
    index="company_id",
    columns="metric",
    values="percentile_rank",
    aggfunc="first",
)

metric_order = [
    "roe",
    "roce",
    "net_profit_margin",
    "debt_to_equity",
    "free_cash_flow",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
    "eps_cagr_5yr",
    "interest_coverage",
    "asset_turnover",
]

available_metrics = [
    metric for metric in metric_order
    if metric in pivot.columns
]

pivot = pivot[available_metrics].reset_index()


# ---------------------------------------------------------------
# Percentile display
# ---------------------------------------------------------------

st.subheader("Peer Percentile Rankings")

st.caption(
    "Higher percentile indicates stronger relative performance "
    "within the selected peer group."
)


def highlight_percentile(value):
    if pd.isna(value):
        return ""

    if value >= 0.75:
        return "background-color: #b7e1cd"
    elif value <= 0.25:
        return "background-color: #f4cccc"
    else:
        return "background-color: #fff2cc"


styled = (
    pivot.style
    .format(
        {
            column: "{:.0%}"
            for column in available_metrics
        }
    )
    .map(
        highlight_percentile,
        subset=available_metrics,
    )
)

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------------
# Raw peer data
# ---------------------------------------------------------------

with st.expander("View detailed peer data"):

    detail = data.copy()

    detail["percentile_rank"] = (
        detail["percentile_rank"] * 100
    ).round(1)

    st.dataframe(
        detail,
        use_container_width=True,
        hide_index=True,
    )
