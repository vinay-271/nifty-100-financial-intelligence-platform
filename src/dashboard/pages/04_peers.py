import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import (
    get_peers,
    get_ratios,
)

from pathlib import Path


PEER_GROUPS_PATH = Path(
    "data/raw/supporting/peer_groups.xlsx"
)


@st.cache_data(ttl=600)
def get_peer_group_mapping():
    return pd.read_excel(
        PEER_GROUPS_PATH
    )


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

peer_mapping = get_peer_group_mapping()

peer_mapping = peer_mapping[
    peer_mapping["peer_group_name"] == peer_group
].copy()

st.subheader("Company Analysis")

company_options = sorted(
    data["company_id"].unique()
)

selected_company = st.selectbox(
    "Select Company",
    company_options,
)

# ---------------------------------------------------------------
# Radar Chart — Company vs Peer Group Average
# ---------------------------------------------------------------

st.subheader("Company vs Peer Group Average")

RADAR_METRICS = [
    "roe",
    "roce",
    "net_profit_margin",
    "debt_to_equity",
    "free_cash_flow",
    "pat_cagr_5yr",
    "revenue_cagr_5yr",
]

RADAR_LABELS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
]


# ---------------------------------------------------------------
# Selected company's percentile values
# ---------------------------------------------------------------

company_data = data[
    data["company_id"] == selected_company
]

company_values = []

for metric in RADAR_METRICS:

    row = company_data[
        company_data["metric"] == metric
    ]

    if row.empty:
        company_values.append(0)
    else:
        percentile = row.iloc[0]["percentile_rank"]

        if pd.isna(percentile):
            company_values.append(0)
        else:
            company_values.append(
                float(percentile) * 100
            )


# ---------------------------------------------------------------
# Peer-group average percentile values
# ---------------------------------------------------------------

peer_average = (
    data[
        data["metric"].isin(RADAR_METRICS)
    ]
    .groupby("metric")["percentile_rank"]
    .mean()
)

peer_values = []

for metric in RADAR_METRICS:

    value = peer_average.get(
        metric,
        0,
    )

    if pd.isna(value):
        peer_values.append(0)
    else:
        peer_values.append(
            float(value) * 100
        )


# ---------------------------------------------------------------
# Composite Quality Score
# ---------------------------------------------------------------

ratios = get_ratios(selected_company)

annual_ratios = ratios[
    ratios["year"]
    .astype(str)
    .str.match(
        r"^[A-Za-z]{3}\s\d{4}$"
    )
].copy()


if annual_ratios.empty:

    company_composite = 0

else:

    annual_ratios["fiscal_year"] = (
        annual_ratios["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0]
        .astype(int)
    )

    latest_ratio = annual_ratios.loc[
        annual_ratios["fiscal_year"].idxmax()
    ]

    company_composite = (
        latest_ratio[
            "composite_quality_score"
        ]
    )

    if pd.isna(company_composite):
        company_composite = 0


# ---------------------------------------------------------------
# Peer-group average Composite Quality Score
# ---------------------------------------------------------------

peer_company_ids = (
    data["company_id"]
    .dropna()
    .unique()
)

peer_composite_scores = []

for company_id in peer_company_ids:

    company_ratios = get_ratios(
        company_id
    )

    annual = company_ratios[
        company_ratios["year"]
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

    score = latest[
        "composite_quality_score"
    ]

    if pd.notna(score):
        peer_composite_scores.append(
            float(score)
        )


if peer_composite_scores:

    peer_composite = (
        sum(peer_composite_scores)
        / len(peer_composite_scores)
    )

else:

    peer_composite = 0


# ---------------------------------------------------------------
# Add Composite Score as 8th axis
# ---------------------------------------------------------------

company_values.append(
    float(company_composite)
)

peer_values.append(
    float(peer_composite)
)

radar_labels = (
    RADAR_LABELS
    + ["Composite Score"]
)


# ---------------------------------------------------------------
# Close radar polygons
# ---------------------------------------------------------------

radar_labels_closed = (
    radar_labels
    + [radar_labels[0]]
)

company_values_closed = (
    company_values
    + [company_values[0]]
)

peer_values_closed = (
    peer_values
    + [peer_values[0]]
)


# ---------------------------------------------------------------
# Create Plotly radar chart
# ---------------------------------------------------------------

fig = go.Figure()


# Selected company
fig.add_trace(
    go.Scatterpolar(
        r=company_values_closed,
        theta=radar_labels_closed,
        fill="toself",
        name=selected_company,
    )
)


# Peer average
fig.add_trace(
    go.Scatterpolar(
        r=peer_values_closed,
        theta=radar_labels_closed,
        fill=None,
        name="Peer Average",
        line=dict(
            dash="dash"
        ),
    )
)


# ---------------------------------------------------------------
# Layout
# ---------------------------------------------------------------

fig.update_layout(
    title=f"{selected_company} vs {peer_group}",
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100],
            ticksuffix="%",
        )
    ),
    showlegend=True,
    height=600,
    margin=dict(
        l=60,
        r=60,
        t=80,
        b=60,
    ),
)


st.plotly_chart(
    fig,
    use_container_width=True,
)

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
