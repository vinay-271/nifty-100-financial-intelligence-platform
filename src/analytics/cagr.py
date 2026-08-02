from math import pow


def cagr(begin_value, end_value, years):
    """
    Compound Annual Growth Rate (%)

    Formula:
        ((Ending / Beginning) ** (1 / Years) - 1) * 100
    """

    if (
        begin_value is None
        or end_value is None
        or years is None
        or begin_value <= 0
        or end_value <= 0
        or years <= 0
    ):
        return None

    return round(
        (pow(end_value / begin_value, 1 / years) - 1) * 100,
        2,
    )


def sales_cagr(begin_sales, end_sales, years):
    return cagr(begin_sales, end_sales, years)


def profit_cagr(begin_profit, end_profit, years):
    return cagr(begin_profit, end_profit, years)


def eps_cagr(begin_eps, end_eps, years):
    return cagr(begin_eps, end_eps, years)


def book_value_cagr(begin_book_value, end_book_value, years):
    return cagr(begin_book_value, end_book_value, years)


def stock_price_cagr(begin_price, end_price, years):
    return cagr(begin_price, end_price, years)
