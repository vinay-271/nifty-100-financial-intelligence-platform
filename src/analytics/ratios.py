"""
Financial Ratio Engine
Sprint 2 - Day 08

Pure financial ratio functions.
Each function accepts numeric inputs and returns either
a float (rounded to 2 decimals) or None.
"""


def net_profit_margin(net_profit, sales):
    """
    Net Profit Margin (%)

    Formula:
        (Net Profit / Sales) * 100

    Returns:
        None if sales <= 0
    """

    if sales is None or sales <= 0:
        return None

    return round((net_profit / sales) * 100, 2)


def operating_profit_margin(operating_profit, sales):
    """
    Operating Profit Margin (%)

    Formula:
        (Operating Profit / Sales) * 100

    Returns:
        None if sales <= 0
    """

    if sales is None or sales <= 0:
        return None

    return round((operating_profit / sales) * 100, 2)


def return_on_equity(net_profit, equity_capital, reserves):
    """
    Return on Equity (%)

    Formula:
        Net Profit /
        (Equity Capital + Reserves)
        * 100

    Returns:
        None if equity <= 0
    """

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return round((net_profit / equity) * 100, 2)


def return_on_capital_employed(
    operating_profit,
    equity_capital,
    reserves,
    borrowings
):
    """
    Return on Capital Employed (%)

    Formula:
        EBIT /
        (Equity + Reserves + Borrowings)
        * 100

    NOTE:
        Using Operating Profit as EBIT.
    """

    capital = equity_capital + reserves + borrowings

    if capital <= 0:
        return None

    return round((operating_profit / capital) * 100, 2)


def return_on_assets(net_profit, total_assets):
    """
    Return on Assets (%)

    Formula:
        Net Profit /
        Total Assets
        * 100
    """

    if total_assets is None or total_assets <= 0:
        return None

    return round((net_profit / total_assets) * 100, 2)

def debt_to_equity(
    borrowings,
    equity_capital,
    reserves,
):
    """
    Debt-to-Equity Ratio

    Formula:
        Borrowings /
        (Equity Capital + Reserves)
    """

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return round(borrowings / equity, 2)


def interest_coverage(
    operating_profit,
    interest,
):
    """
    Interest Coverage Ratio

    Formula:
        Operating Profit / Interest
    """

    if interest is None or interest <= 0:
        return None

    return round(
        operating_profit / interest,
        2,
    )


def net_debt(
    borrowings,
    cash,
):
    """
    Net Debt

    Formula:
        Borrowings - Cash
    """

    if cash is None:
        cash = 0

    return round(
        borrowings - cash,
        2,
    )


def asset_turnover(
    sales,
    total_assets,
):
    """
    Asset Turnover

    Formula:
        Sales / Total Assets
    """

    if total_assets is None or total_assets <= 0:
        return None

    return round(
        sales / total_assets,
        2,
    )


def high_leverage_flag(
    debt_to_equity_ratio,
):
    """
    High Leverage

    True if D/E > 2
    """

    if debt_to_equity_ratio is None:
        return False

    return debt_to_equity_ratio > 2


def debt_free_label(
    borrowings,
):
    """
    Debt Free

    True if borrowings == 0
    """

    if borrowings is None:
        return False

    return borrowings == 0

def net_debt(borrowings, cash):
    """
    Net Debt = Borrowings - Cash

    NOTE:
        Current dataset does not contain a cash column.
        Function reserved for future use.
    """
    if cash is None:
        return None

    return round(borrowings - cash, 2)
