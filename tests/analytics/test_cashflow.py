from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    capex_label,
    fcf_conversion_rate,
    capital_allocation_pattern,
)


# --------------------------------------------------
# Free Cash Flow
# --------------------------------------------------

def test_free_cash_flow_positive():
    assert free_cash_flow(1000, -300) == 700.00


def test_free_cash_flow_negative():
    assert free_cash_flow(200, -500) == -300.00


def test_free_cash_flow_none():
    assert free_cash_flow(None, -200) is None


# --------------------------------------------------
# CFO Quality
# --------------------------------------------------

def test_cfo_quality_high():
    assert cfo_quality_score(120, 100) == "High Quality"


def test_cfo_quality_moderate():
    assert cfo_quality_score(70, 100) == "Moderate"


def test_cfo_quality_accrual():
    assert cfo_quality_score(30, 100) == "Accrual Risk"


def test_cfo_quality_zero_pat():
    assert cfo_quality_score(100, 0) is None


# --------------------------------------------------
# CapEx Intensity
# --------------------------------------------------

def test_capex_intensity():
    assert capex_intensity(-50, 1000) == 5.00


def test_capex_zero_sales():
    assert capex_intensity(-50, 0) is None


# --------------------------------------------------
# CapEx Labels
# --------------------------------------------------

def test_capex_asset_light():
    assert capex_label(2.5) == "Asset Light"


def test_capex_moderate():
    assert capex_label(5.5) == "Moderate"


def test_capex_capital_intensive():
    assert capex_label(15) == "Capital Intensive"


# --------------------------------------------------
# FCF Conversion
# --------------------------------------------------

def test_fcf_conversion():
    assert fcf_conversion_rate(400, 500) == 80.00


def test_fcf_conversion_zero_profit():
    assert fcf_conversion_rate(100, 0) is None


# --------------------------------------------------
# Capital Allocation
# --------------------------------------------------

def test_pattern_reinvestor():
    assert (
        capital_allocation_pattern(100, -50, -25)
        == "Reinvestor"
    )


def test_pattern_shareholder_returns():
    assert (
        capital_allocation_pattern(
            100,
            -50,
            -25,
            "High Quality",
        )
        == "Shareholder Returns"
    )


def test_pattern_liquidating_assets():
    assert (
        capital_allocation_pattern(
            100,
            50,
            -10,
        )
        == "Liquidating Assets"
    )


def test_pattern_distress():
    assert (
        capital_allocation_pattern(
            -100,
            50,
            50,
        )
        == "Distress Signal"
    )


def test_pattern_growth_debt():
    assert (
        capital_allocation_pattern(
            -100,
            -50,
            40,
        )
        == "Growth Funded by Debt"
    )


def test_pattern_cash_accumulator():
    assert (
        capital_allocation_pattern(
            100,
            50,
            25,
        )
        == "Cash Accumulator"
    )


def test_pattern_pre_revenue():
    assert (
        capital_allocation_pattern(
            -100,
            -50,
            -25,
        )
        == "Pre-Revenue"
    )


def test_pattern_mixed():
    assert (
        capital_allocation_pattern(
            100,
            -50,
            25,
        )
        == "Mixed"
    )
