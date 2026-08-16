import streamlit as st
import pandas as pd

from src.screener.engine import ScreenerEngine
from src.dashboard.utils.db import (
    get_companies,
    get_sectors,
)


st.title("Nifty 100 Screener")

st.caption(
    "Filter the Nifty 100 universe using financial thresholds "
    "or start from a predefined strategy."
)


# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------

PRESETS = {
    "Quality Compounder": "quality_compounder",
    "Value Pick": "value_pick",
    "Growth Accelerator": "growth_accelerator",
    "Dividend Champion": "dividend_champion",
    "Debt-Free Blue Chip": "debt_free_blue_chip",
    "Turnaround Watch": "turnaround_watch",
}

# The ten dashboard sliders required by Sprint 4.
SLIDER_CONFIG = {
    "roe_min": {
        "label": "ROE minimum (%)",
        "min": 0.0,
        "max": 100.0,
        "step": 1.0,
    },
    "debt_to_equity_max": {
        "label": "D/E maximum",
        "min": 0.0,
        "max": 10.0,
        "step": 0.1,
    },
    "free_cash_flow_min": {
        "label": "FCF minimum (Cr)",
        "min": -10000.0,
        "max": 100000.0,
        "step": 500.0,
    },
    "revenue_cagr_5yr_min": {
        "label": "Revenue CAGR minimum (%)",
        "min": -50.0,
        "max": 50.0,
        "step": 1.0,
    },
    "pat_cagr_5yr_min": {
        "label": "PAT CAGR minimum (%)",
        "min": -50.0,
        "max": 100.0,
        "step": 1.0,
    },
    "opm_min": {
        "label": "OPM minimum (%)",
        "min": -50.0,
        "max": 100.0,
        "step": 1.0,
    },
    "pe_ratio_max": {
        "label": "P/E maximum",
        "min": 1.0,
        "max": 200.0,
        "step": 1.0,
    },
    "pb_ratio_max": {
        "label": "P/B maximum",
        "min": 0.1,
        "max": 30.0,
        "step": 0.5,
    },
    "dividend_yield_min": {
        "label": "Dividend Yield minimum (%)",
        "min": 0.0,
        "max": 20.0,
        "step": 0.5,
    },
    "icr_min": {
        "label": "Interest Coverage minimum",
        "min": 0.0,
        "max": 100.0,
        "step": 1.0,
    },
}


# -------------------------------------------------------------------
# Load supporting data
# -------------------------------------------------------------------

companies = get_companies()
sectors = get_sectors()


# -------------------------------------------------------------------
# Load preset configuration
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_screener_config():
    engine = ScreenerEngine()

    try:
        engine.connect()
        engine.load_config()
        return engine.config
    finally:
        engine.close()


config = get_screener_config()
preset_config = config.get("presets", {})


# -------------------------------------------------------------------
# Preset state
# -------------------------------------------------------------------

if "active_preset" not in st.session_state:
    st.session_state.active_preset = None


def apply_preset(preset_name):
    """Populate slider session-state values from a preset."""

    values = preset_config.get(preset_name, {})

    for key in SLIDER_CONFIG:
        if key in values:
            st.session_state[f"slider_{key}"] = values[key]

    st.session_state.active_preset = preset_name


# -------------------------------------------------------------------
# Preset buttons
# -------------------------------------------------------------------

st.sidebar.header("Preset Screeners")

preset_columns = st.sidebar.columns(2)

preset_items = list(PRESETS.items())

for i, (label, preset_name) in enumerate(preset_items):
    with preset_columns[i % 2]:
        if st.button(
            label,
            key=f"preset_{preset_name}",
            use_container_width=True,
        ):
            apply_preset(preset_name)
            st.rerun()


# -------------------------------------------------------------------
# Custom filters
# -------------------------------------------------------------------

st.sidebar.header("Custom Filters")

filters = {}

for key, settings in SLIDER_CONFIG.items():

    state_key = f"slider_{key}"

    if state_key not in st.session_state:
        st.session_state[state_key] = settings["min"]

    value = st.sidebar.slider(
        settings["label"],
        min_value=settings["min"],
        max_value=settings["max"],
        step=settings["step"],
        key=state_key,
    )

    # Only pass non-default values to the engine.
    if value != settings["min"]:
        filters[key] = value


# -------------------------------------------------------------------
# Active preset information
# -------------------------------------------------------------------

if st.session_state.active_preset:
    active_label = next(
        (
            label
            for label, preset_name in PRESETS.items()
            if preset_name == st.session_state.active_preset
        ),
        st.session_state.active_preset,
    )

    st.sidebar.success(
        f"Preset: {active_label}"
    )

    if st.sidebar.button(
        "Clear Preset",
        use_container_width=True,
    ):
        st.session_state.active_preset = None

        for key, settings in SLIDER_CONFIG.items():
            st.session_state[f"slider_{key}"] = settings["min"]

        st.rerun()


# -------------------------------------------------------------------
# Run screener
# -------------------------------------------------------------------

@st.cache_data(ttl=600)
def run_custom_screener(filters):
    engine = ScreenerEngine()

    try:
        engine.connect()
        return engine.screen(filters)
    finally:
        engine.close()


@st.cache_data(ttl=600)
def run_preset_screener(preset_name):
    engine = ScreenerEngine()

    try:
        engine.connect()
        return engine.run_preset(preset_name)
    finally:
        engine.close()


try:
    if st.session_state.active_preset:
        # Exact preset logic is preserved here.
        # This is important for presets such as Turnaround Watch,
        # which contain conditions not represented by the ten sliders.
        results = run_preset_screener(
            st.session_state.active_preset
        )
    else:
        results = run_custom_screener(filters)

except Exception as exc:
    st.error(f"Unable to run screener: {exc}")
    st.stop()


# -------------------------------------------------------------------
# Attach company names and sectors
# -------------------------------------------------------------------

if not results.empty:

    results = results.merge(
        companies[
            ["id", "company_name"]
        ],
        left_on="company_id",
        right_on="id",
        how="left",
    )

    results = results.merge(
        sectors[
            ["company_id", "sector"]
        ],
        on="company_id",
        how="left",
        suffixes=("", "_sector"),
    )

    results["sector"] = results["sector"].fillna(
        results.get("sector_sector")
    )


# -------------------------------------------------------------------
# Result count
# -------------------------------------------------------------------

st.divider()

st.subheader(
    f"{len(results)} companies match your filters"
)


# -------------------------------------------------------------------
# Summary metrics
# -------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Companies Found",
        len(results),
    )

with col2:
    if (
        not results.empty
        and "composite_quality_score" in results.columns
    ):
        avg_score = results[
            "composite_quality_score"
        ].mean()

        st.metric(
            "Average Composite Score",
            f"{avg_score:.1f}"
            if pd.notna(avg_score)
            else "N/A",
        )
    else:
        st.metric(
            "Average Composite Score",
            "N/A",
        )

with col3:
    if (
        not results.empty
        and "composite_quality_score" in results.columns
    ):
        max_score = results[
            "composite_quality_score"
        ].max()

        st.metric(
            "Highest Composite Score",
            f"{max_score:.1f}"
            if pd.notna(max_score)
            else "N/A",
        )
    else:
        st.metric(
            "Highest Composite Score",
            "N/A",
        )


# -------------------------------------------------------------------
# Results table
# -------------------------------------------------------------------

st.subheader("Screening Results")

display_columns = [
    "company_id",
    "company_name",
    "sector",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage",
    "composite_quality_score",
]

display_columns = [
    column
    for column in display_columns
    if column in results.columns
]

display_df = results[display_columns].copy()

display_df = display_df.rename(
    columns={
        "company_id": "Company",
        "company_name": "Company Name",
        "sector": "Sector",
        "return_on_equity_pct": "ROE %",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (Cr)",
        "revenue_cagr_5yr": "Revenue CAGR %",
        "pat_cagr_5yr": "PAT CAGR %",
        "operating_profit_margin_pct": "OPM %",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Dividend Yield %",
        "interest_coverage": "ICR",
        "composite_quality_score": "Composite Score",
    }
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# -------------------------------------------------------------------
# CSV download
# -------------------------------------------------------------------

csv_data = display_df.to_csv(
    index=False
)

st.download_button(
    label="Download Results as CSV",
    data=csv_data,
    file_name="nifty100_screener.csv",
    mime="text/csv",
)
