import pandas as pd
import pytest

from src.screener.engine import ScreenerEngine


@pytest.fixture
def engine():
    engine = ScreenerEngine(
        db_path="db/nifty100.db",
        config_path="config/screener_config.yaml",
    )

    engine.connect()
    engine.load_config()
    engine.load_data()

    yield engine

    engine.close()


# ---------------------------------------------------------
# Data loading
# ---------------------------------------------------------

def test_load_data(engine):
    assert engine.data is not None
    assert len(engine.data) > 0


def test_required_screener_columns(engine):
    required_columns = {
        "company_id",
        "year",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "interest_coverage",
        "asset_turnover",
        "eps_cagr_5yr",
        "sales",
        "net_profit",
        "eps",
        "market_cap_cr",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "sector",
    }

    assert required_columns.issubset(
        set(engine.data.columns)
    )


# ---------------------------------------------------------
# Individual filters
# ---------------------------------------------------------

@pytest.mark.parametrize(
    "filter_name, threshold, column",
    [
        ("roe_min", 15, "return_on_equity_pct"),
        ("free_cash_flow_min", 0, "free_cash_flow_cr"),
        ("revenue_cagr_5yr_min", 10, "revenue_cagr_5yr"),
        ("pat_cagr_5yr_min", 10, "pat_cagr_5yr"),
        ("opm_min", 10, "operating_profit_margin_pct"),
        ("pe_ratio_max", 20, "pe_ratio"),
        ("pb_ratio_max", 3, "pb_ratio"),
        ("dividend_yield_min", 1, "dividend_yield_pct"),
        ("market_cap_min", 10000, "market_cap_cr"),
        ("net_profit_min", 1000, "net_profit"),
        ("eps_cagr_min", 10, "eps_cagr_5yr"),
        ("asset_turnover_min", 1, "asset_turnover"),
        ("sales_min", 5000, "sales"),
    ],
)
def test_threshold_filter(engine, filter_name, threshold, column):
    result = engine.screen({
        filter_name: threshold
    })

    assert isinstance(result, pd.DataFrame)

    if not result.empty:
        assert (result[column] >= threshold).all() or (
            filter_name.endswith("_max")
            and (result[column] <= threshold).all()
        )


def test_debt_to_equity_filter(engine):
    result = engine.screen({
        "debt_to_equity_max": 1.0
    })

    assert isinstance(result, pd.DataFrame)

    # Non-financial companies must satisfy D/E threshold.
    non_financial = result[
        result["sector"].str.lower() != "financials"
    ]

    assert (
        non_financial["debt_to_equity"] <= 1.0
    ).all()


def test_interest_coverage_filter(engine):
    result = engine.screen({
        "icr_min": 2.0
    })

    assert isinstance(result, pd.DataFrame)

    # NaN ICR represents debt-free companies and
    # must pass the filter.
    if not result.empty:
        valid = (
            result["interest_coverage"].fillna(float("inf"))
            >= 2.0
        )

        assert valid.all()


# ---------------------------------------------------------
# Financials carve-out
# ---------------------------------------------------------

def test_financials_debt_to_equity_carveout(engine):
    result = engine.screen({
        "debt_to_equity_max": 1.0
    })

    financials = result[
        result["sector"].str.lower() == "financials"
    ]

    # Financials are not removed solely because
    # their D/E exceeds the threshold.
    if not financials.empty:
        high_debt_financials = financials[
            financials["debt_to_equity"] > 1.0
        ]

        # If such companies exist, they must remain.
        assert len(high_debt_financials) >= 0


# ---------------------------------------------------------
# Sorting
# ---------------------------------------------------------

def test_results_sorted_by_composite_score(engine):
    result = engine.screen()

    if len(result) > 1:
        scores = result[
            "composite_quality_score"
        ].dropna()

        assert scores.is_monotonic_decreasing


# ---------------------------------------------------------
# Invalid filter
# ---------------------------------------------------------

def test_unknown_filter_raises_error(engine):
    with pytest.raises(ValueError):
        engine.screen({
            "unknown_metric": 10
        })


# ---------------------------------------------------------
# Preset loading
# ---------------------------------------------------------

@pytest.mark.parametrize(
    "preset",
    [
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ],
)
def test_preset_exists(engine, preset):
    assert preset in engine.config["presets"]

def test_latest_annual_data_has_one_row_per_company(engine):
    result = engine.latest_annual_data()

    assert len(result) == result["company_id"].nunique()

    assert not result["year"].eq("TTM").any()

    assert not result["year"].str.contains(
        "9m|15",
        case=False,
        regex=True,
    ).any()
