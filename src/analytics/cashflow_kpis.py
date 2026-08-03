"""
Cash Flow KPI Engine
Sprint 2 - Day 11

Pure cash flow KPI functions.
All functions return either:
- float
- string
- None
"""


def free_cash_flow(
    operating_activity,
    investing_activity,
):
    """
    Free Cash Flow (FCF)

    Formula:
        Operating Activity + Investing Activity

    Note:
        Investing activity is usually negative.
        Negative FCF is allowed.
    """

    if operating_activity is None or investing_activity is None:
        return None

    return round(
        operating_activity + investing_activity,
        2,
    )


def cfo_quality_score(
    average_cfo,
    average_pat,
):
    """
    CFO Quality Score

    Formula:
        Average CFO / Average PAT

    Labels

        > 1.0
            High Quality

        0.5 - 1.0
            Moderate

        < 0.5
            Accrual Risk
    """

    if (
        average_pat is None
        or average_pat == 0
    ):
        return None

    ratio = average_cfo / average_pat

    if ratio > 1:
        return "High Quality"

    if ratio >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def capex_intensity(
    investing_activity,
    sales,
):
    """
    CapEx Intensity (%)

    Formula

        abs(Investing Activity)
        -----------------------
              Sales

    *100
    """

    if (
        sales is None
        or sales <= 0
    ):
        return None

    return round(
        abs(investing_activity) / sales * 100,
        2,
    )


def capex_label(
    intensity,
):
    """
    CapEx Classification

        <3
            Asset Light

        3-8
            Moderate

        >8
            Capital Intensive
    """

    if intensity is None:
        return None

    if intensity < 3:
        return "Asset Light"

    if intensity <= 8:
        return "Moderate"

    return "Capital Intensive"


def fcf_conversion_rate(
    free_cash_flow_value,
    operating_profit,
):
    """
    FCF Conversion

    Formula

        FCF
        ---
        Operating Profit

    *100
    """

    if (
        operating_profit is None
        or operating_profit == 0
    ):
        return None

    return round(
        free_cash_flow_value
        / operating_profit
        * 100,
        2,
    )


def capital_allocation_pattern(
    cfo,
    cfi,
    cff,
    cfo_quality=None,
):
    """
    Capital Allocation Pattern

    Pattern Mapping

    (+,-,-)
        Reinvestor

    (+,-,-) + High Quality
        Shareholder Returns

    (+,+,-)
        Liquidating Assets

    (-,+,+)
        Distress Signal

    (-,-,+)
        Growth Funded by Debt

    (+,+,+)
        Cash Accumulator

    (-,-,-)
        Pre-Revenue

    (+,-,+)
        Mixed
    """

    signs = (
        "+" if cfo >= 0 else "-",
        "+" if cfi >= 0 else "-",
        "+" if cff >= 0 else "-",
    )

    if signs == ("+", "-", "-"):

        if cfo_quality == "High Quality":
            return "Shareholder Returns"

        return "Reinvestor"

    if signs == ("+", "+", "-"):
        return "Liquidating Assets"

    if signs == ("-", "+", "+"):
        return "Distress Signal"

    if signs == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if signs == ("+", "+", "+"):
        return "Cash Accumulator"

    if signs == ("-", "-", "-"):
        return "Pre-Revenue"

    if signs == ("+", "-", "+"):
        return "Mixed"

    return "Other"
