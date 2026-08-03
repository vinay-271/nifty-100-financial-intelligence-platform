import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage,
    net_debt,
    asset_turnover,
    high_leverage_flag,
    debt_free_label,
)


# --------------------------------------------------
# Net Profit Margin
# --------------------------------------------------

def test_net_profit_margin_normal():
    assert net_profit_margin(20, 100) == 20.00


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(20, 0) is None


# --------------------------------------------------
# Operating Profit Margin
# --------------------------------------------------

def test_operating_profit_margin_normal():
    assert operating_profit_margin(25, 100) == 25.00


def test_operating_profit_margin_zero_sales():
    assert operating_profit_margin(25, 0) is None


# --------------------------------------------------
# Return on Equity
# --------------------------------------------------

def test_roe_normal():
    assert return_on_equity(100, 200, 300) == 20.00


def test_roe_negative_equity():
    assert return_on_equity(100, -100, 50) is None


# --------------------------------------------------
# Return on Capital Employed
# --------------------------------------------------

def test_roce_normal():
    assert return_on_capital_employed(
        100,
        200,
        300,
        500
    ) == 10.00


def test_roce_zero_capital():
    assert return_on_capital_employed(
        100,
        0,
        0,
        0
    ) is None


# --------------------------------------------------
# Return on Assets
# --------------------------------------------------

def test_roa_normal():
    assert return_on_assets(100, 1000) == 10.00


def test_roa_zero_assets():
    assert return_on_assets(100, 0) is None


# --------------------------------------------------
# Additional Edge Cases
# --------------------------------------------------

def test_negative_net_profit_margin():
    assert net_profit_margin(-10, 100) == -10.00


def test_negative_roa():
    assert return_on_assets(-50, 1000) == -5.00

# --------------------------------------------------
# Debt to Equity
# --------------------------------------------------

def test_debt_to_equity_normal():
    assert debt_to_equity(300, 100, 200) == 1.00


def test_debt_to_equity_zero_equity():
    assert debt_to_equity(300, 0, 0) is None


def test_debt_to_equity_negative_equity():
    assert debt_to_equity(300, -100, 50) is None


# --------------------------------------------------
# Interest Coverage
# --------------------------------------------------

def test_interest_coverage_normal():
    assert interest_coverage(
        1000,
        200,
        100,
    ) == 12.00


def test_interest_coverage_zero_interest():
    assert interest_coverage(
        1000,
        100,
        0,
    ) is None


def test_interest_coverage_negative_interest():
    assert interest_coverage(
        1000,
        100,     # other_income
        -20      # interest
    ) is None


# --------------------------------------------------
# Net Debt
# --------------------------------------------------

def test_net_debt_normal():
    assert net_debt(borrowings=500,investments=200,) == 300.00


def test_net_debt_missing_cash():
    assert net_debt(500, None) is None


# --------------------------------------------------
# Asset Turnover
# --------------------------------------------------

def test_asset_turnover_normal():
    assert asset_turnover(1000, 500) == 2.00


def test_asset_turnover_zero_assets():
    assert asset_turnover(1000, 0) is None


def test_asset_turnover_negative_assets():
    assert asset_turnover(1000, -100) is None


# --------------------------------------------------
# High Leverage Flag
# --------------------------------------------------

def test_high_leverage_true():
    assert high_leverage_flag(2.5) is True


def test_high_leverage_false():
    assert high_leverage_flag(1.5) is False


def test_high_leverage_none():
    assert high_leverage_flag(None) is False


# --------------------------------------------------
# Debt Free Label
# --------------------------------------------------

def test_debt_free_true():
    assert debt_free_label(0) is True


def test_debt_free_false():
    assert debt_free_label(100) is False


def test_debt_free_none():
    assert debt_free_label(None) is False


def test_net_debt_normal():
    assert net_debt(500, 200) == 300.00


def test_net_debt_none():
    assert net_debt(None, 200) is None
