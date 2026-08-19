import sqlite3
from pathlib import Path

import pandas as pd

from src.analytics.cagr import cagr

def generate_cashflow_intelligence(
    db_path="db/nifty100.db",
    output_dir="output",
):
    """
    Generate company-level Cash Flow Intelligence.

    Produces:
        output/cashflow_intelligence.xlsx
        output/distress_alerts.csv
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:

        cashflow = pd.read_sql(
            """
            SELECT
                company_id,
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
            """,
            conn,
        )

        profit_loss = pd.read_sql(
            """
            SELECT
                company_id,
                year,
                sales,
                operating_profit,
                net_profit
            FROM profitandloss
            """,
            conn,
        )

        balance_sheet = pd.read_sql(
            """
            SELECT
                company_id,
                year,
                borrowings
            FROM balancesheet
            """,
            conn,
        )

        sectors = pd.read_sql(
            """
            SELECT
                company_id,
                sector
            FROM sectors
            """,
            conn,
        )

    # -----------------------------------------------------------
    # Annual observations only
    # -----------------------------------------------------------

    annual_cf = cashflow[
        cashflow["year"].astype(str).str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )
    ].copy()

    annual_pl = profit_loss[
        profit_loss["year"].astype(str).str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )
    ].copy()

    annual_bs = balance_sheet[
        balance_sheet["year"].astype(str).str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )
    ].copy()

    annual_cf["fiscal_year"] = (
        annual_cf["year"]
        .str.extract(r"(\d{4})")[0]
        .astype(int)
    )

    annual_pl["fiscal_year"] = (
        annual_pl["year"]
        .str.extract(r"(\d{4})")[0]
        .astype(int)
    )

    annual_bs["fiscal_year"] = (
        annual_bs["year"]
        .str.extract(r"(\d{4})")[0]
        .astype(int)
    )

    annual_cf = annual_cf.sort_values(
        ["company_id", "fiscal_year"]
    )

    annual_pl = annual_pl.sort_values(
        ["company_id", "fiscal_year"]
    )

    annual_bs = annual_bs.sort_values(
        ["company_id", "fiscal_year"]
    )

    sector_map = (
        sectors
        .drop_duplicates("company_id")
        .set_index("company_id")["sector"]
        .to_dict()
    )

    results = []
    distress_alerts = []

    # Use the companies table as the authoritative company list.
    # This guarantees all 92 companies appear in the output,
    # even when a company has no cash-flow records.
    companies_df = pd.read_sql(
        """
        SELECT id AS company_id
        FROM companies
        """,
        conn,
    )

    companies = sorted(
        set(annual_cf["company_id"])
        | set(annual_pl["company_id"])
    )

    for company_id in companies:

        cf = annual_cf[
            annual_cf["company_id"] == company_id
        ].copy()

        pl = annual_pl[
            annual_pl["company_id"] == company_id
        ].copy()

        bs = annual_bs[
            annual_bs["company_id"] == company_id
        ].copy()

        latest_cf = (
            cf.iloc[-1]
            if not cf.empty
            else None
        )

        # -------------------------------------------------------
        # CFO Quality
        # -------------------------------------------------------

        quality_data = cf.merge(
            pl[
                [
                    "company_id",
                    "fiscal_year",
                    "net_profit",
                ]
            ],
            on=["company_id", "fiscal_year"],
            how="inner",
        )

        quality_data = quality_data.dropna(
            subset=[
                "operating_activity",
                "net_profit",
            ]
        )

        if quality_data.empty:
            cfo_score = None
            cfo_label = None
        else:
            average_cfo = quality_data[
                "operating_activity"
            ].mean()

            average_pat = quality_data[
                "net_profit"
            ].mean()

            if average_pat == 0:
                cfo_score = None
                cfo_label = None
            else:
                cfo_score = round(
                    average_cfo / average_pat,
                    2,
                )

                if cfo_score > 1:
                    cfo_label = "High Quality"
                elif cfo_score >= 0.5:
                    cfo_label = "Moderate"
                else:
                    cfo_label = "Accrual Risk"

        # -------------------------------------------------------
        # CapEx Intensity
        # -------------------------------------------------------

        latest_pl = pl.iloc[-1] if not pl.empty else None

        if latest_cf is not None and latest_pl is not None:
            intensity = capex_intensity(
                latest_cf["investing_activity"],
                latest_pl["sales"],
            )
        else:
            intensity = None

        intensity_label = capex_label(
            intensity
        )

        # -------------------------------------------------------
        # FCF CAGR — latest 5-year period
        # -------------------------------------------------------

        cf_with_fcf = cf.copy()

        cf_with_fcf["fcf"] = (
            cf_with_fcf["operating_activity"]
            + cf_with_fcf["investing_activity"]
        )

        # cf_positive = cf_with_fcf[
        #     cf_with_fcf["fcf"] > 0
        # ].copy()

        if len(cf_with_fcf) >= 6:

            first_5yr = cf_with_fcf.iloc[-6]
            latest = cf_with_fcf.iloc[-1]

            fcf_cagr = cagr(
                first_5yr["fcf"],
                latest["fcf"],
                5,
            )

        else:
            fcf_cagr = None

        # -------------------------------------------------------
        # FCF Conversion
        # -------------------------------------------------------

        if latest_cf is not None and latest_pl is not None:

            latest_fcf = free_cash_flow(
                latest_cf["operating_activity"],
                latest_cf["investing_activity"],
            )

            fcf_conversion = fcf_conversion_rate(
                latest_fcf,
                latest_pl["operating_profit"],
            )

        else:
            fcf_conversion = None

        # -------------------------------------------------------
        # Distress Signal
        # -------------------------------------------------------

        if latest_cf is not None:
            distress_flag = (
                latest_cf["operating_activity"] < 0
                and latest_cf["financing_activity"] > 0
            )
        else:
            distress_flag = False

        if distress_flag:

            latest_profit = (
                latest_pl["net_profit"]
                if latest_pl is not None
                else None
            )

            distress_alerts.append(
                {
                    "company_id": company_id,
                    "cfo_value": latest_cf[
                        "operating_activity"
                    ],
                    "cff_value": latest_cf[
                        "financing_activity"
                    ],
                    "latest_net_profit": latest_profit,
                }
            )

        # -------------------------------------------------------
        # Deleveraging
        # -------------------------------------------------------

        deleveraging_flag = False

        if len(bs) >= 2:

            latest_bs = bs.iloc[-1]
            previous_bs = bs.iloc[-2]

            borrowings_latest = latest_bs[
                "borrowings"
            ]

            borrowings_previous = previous_bs[
                "borrowings"
            ]

            if (
                latest_cf is not None
                and pd.notna(borrowings_latest)
                and pd.notna(borrowings_previous)
            ):
                deleveraging_flag = (
                    latest_cf["financing_activity"] < 0
                    and borrowings_latest < borrowings_previous
                )

        # -------------------------------------------------------
        # Capital Allocation
        # -------------------------------------------------------

        if latest_cf is not None:
            capital_allocation = capital_allocation_pattern(
                latest_cf["operating_activity"],
                latest_cf["investing_activity"],
                latest_cf["financing_activity"],
                cfo_label,
            )
        else:
            capital_allocation = "Unavailable"

        results.append(
            {
                "company_id": company_id,
                "sector": sector_map.get(company_id),
                "cfo_quality_score": cfo_score,
                "cfo_quality_label": cfo_label,
                "capex_intensity_pct": intensity,
                "capex_label": intensity_label,
                "fcf_cagr_5yr": fcf_cagr,
                "fcf_conversion_pct": fcf_conversion,
                "distress_flag": distress_flag,
                "deleveraging_flag": deleveraging_flag,
                "capital_allocation_label": capital_allocation,
            }
        )

    intelligence = pd.DataFrame(results)

    intelligence.to_excel(
        output_dir / "cashflow_intelligence.xlsx",
        index=False,
    )

    pd.DataFrame(
        distress_alerts
    ).to_csv(
        output_dir / "distress_alerts.csv",
        index=False,
    )

    return intelligence

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


if __name__ == "__main__":
    df = generate_cashflow_intelligence()

    print(
        f"Generated cash flow intelligence "
        f"for {len(df)} companies."
    )

    print(
        "Output: output/cashflow_intelligence.xlsx"
    )

    print(
        "Output: output/distress_alerts.csv"
    )
