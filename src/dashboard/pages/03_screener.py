import streamlit as st
import pandas as pd

from src.screener.engine import ScreenerEngine
from src.dashboard.utils.db import get_companies


st.title("Nifty 100 Screener")

st.write(
    "Screen the Nifty 100 universe using the predefined financial "
    "screening strategies."
)


# -------------------------------------------------------------------
# Presets
# -------------------------------------------------------------------

PRESETS = {
    "Quality Compounder": "quality_compounder",
    "Value Pick": "value_pick",
    "Growth Accelerator": "growth_accelerator",
    "Dividend Champion": "dividend_champion",
    "Debt-Free Blue Chip": "debt_free_blue_chip",
    "Turnaround Watch": "turnaround_watch",
}


selected_label = st.selectbox(
    "Select Screener",
    list(PRESETS.keys()),
)

selected_preset = PRESETS[selected_label]


# -------------------------------------------------------------------
# Run screener
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def run_screener(preset):
    engine = ScreenerEngine()

    try:
        engine.connect()
        result = engine.run_preset(preset)
        return result
    finally:
        engine.close()


try:
    results = run_screener(selected_preset)
except Exception as exc:
    st.error(f"Unable to run screener: {exc}")
    st.stop()


# -------------------------------------------------------------------
# Summary metrics
# -------------------------------------------------------------------

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Companies Found",
        len(results),
    )

with col2:
    avg_score = results["composite_quality_score"].mean()

    st.metric(
        "Average Composite Score",
        f"{avg_score:.1f}" if pd.notna(avg_score) else "N/A",
    )

with col3:
    max_score = results["composite_quality_score"].max()

    st.metric(
        "Highest Composite Score",
        f"{max_score:.1f}" if pd.notna(max_score) else "N/A",
    )


# -------------------------------------------------------------------
# Results table
# -------------------------------------------------------------------

st.divider()
st.subheader(f"{selected_label} Results")


display_columns = [
    "company_id",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "composite_quality_score",
]

display_columns = [
    column
    for column in display_columns
    if column in results.columns
]


display_df = results[display_columns].copy()


rename_columns = {
    "company_id": "Company",
    "return_on_equity_pct": "ROE %",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)",
    "revenue_cagr_5yr": "Revenue CAGR %",
    "pat_cagr_5yr": "PAT CAGR %",
    "composite_quality_score": "Quality Score",
}

display_df = display_df.rename(
    columns=rename_columns
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# -------------------------------------------------------------------
# Download
# -------------------------------------------------------------------

csv_data = display_df.to_csv(index=False)

st.download_button(
    label="Download Results as CSV",
    data=csv_data,
    file_name=f"{selected_preset}_screener.csv",
    mime="text/csv",
)
