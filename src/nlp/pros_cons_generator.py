"""
NLP Pros / Cons Generator
Sprint 5 - Day 30

Generates rule-based investment pros and cons for all companies.

Output:
    output/pros_cons_generated.csv
"""

from pathlib import Path
import sqlite3

import pandas as pd


DB_PATH = Path("db/nifty100.db")
OUTPUT_PATH = Path("output/pros_cons_generated.csv")


PRO_RULES = {
    "PRO-01": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency.",
    "PRO-02": "Strong free cash flow generation over 5 years signals healthy business fundamentals.",
    "PRO-03": "Debt-free balance sheet provides financial flexibility and eliminates interest burden.",
    "PRO-04": "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum.",
    "PRO-05": "Operating profit margin above 25% indicates strong pricing power and cost discipline.",
    "PRO-06": "Net profit compounding at above 20% over 5 years creates significant shareholder value.",
    "PRO-07": "Very high interest coverage ratio reflects negligible financial stress from debt servicing.",
    "PRO-08": "Consistent dividend yield above 2% backed by positive free cash flow.",
    "PRO-09": "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding.",
    "PRO-10": "Return on equity improving for 3 consecutive years shows strengthening business quality.",
    "PRO-11": "Revenue growing slower than profits shows improving operating leverage and scale benefits.",
    "PRO-12": "Growing asset base funded by internal accruals reflects self-sustaining growth.",
}


CON_RULES = {
    "CON-01": "Debt-to-equity ratio of {value:.2f} is elevated for a non-financial company and warrants monitoring.",
    "CON-02": "Free cash flow negative for 3 consecutive years raises concern about cash generation quality.",
    "CON-03": "Operating margins declining for 3 consecutive years suggest pricing or cost pressure.",
    "CON-04": "Company reported a net loss in the most recent financial year.",
    "CON-05": "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss.",
    "CON-06": "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations.",
    "CON-07": "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable.",
    "CON-08": "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk.",
    "CON-09": "Earnings per share declining for 3 consecutive years reflects deteriorating profitability.",
    "CON-10": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital.",
    "CON-11": "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility.",
    "CON-12": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum.",
}


def load_data():
    """Load all datasets required by the rule engine."""

    with sqlite3.connect(DB_PATH) as conn:

        ratios = pd.read_sql(
            """
            SELECT *
            FROM financial_ratios
            """,
            conn,
        )

        pl = pd.read_sql(
            """
            SELECT *
            FROM profitandloss
            """,
            conn,
        )

        bs = pd.read_sql(
            """
            SELECT *
            FROM balancesheet
            """,
            conn,
        )

        cf = pd.read_sql(
            """
            SELECT *
            FROM cashflow
            """,
            conn,
        )

        market = pd.read_sql(
            """
            SELECT *
            FROM market_cap
            """,
            conn,
        )

        sectors = pd.read_sql(
            """
            SELECT company_id, sector
            FROM sectors
            """,
            conn,
        )

        companies = pd.read_sql(
            """
            SELECT *
            FROM companies
            """,
            conn,
        )

    return (
        companies,
        ratios,
        pl,
        bs,
        cf,
        market,
        sectors,
    )


def annual_only(df):
    """Keep annual financial records and sort chronologically."""

    if df.empty:
        return df.copy()

    result = df[
        df["year"]
        .astype(str)
        .str.match(r"^[A-Za-z]{3}\s\d{4}$")
    ].copy()

    result["fiscal_year"] = (
        result["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .astype(int)
    )

    return result.sort_values("fiscal_year")


def latest_row(df):
    """Return latest annual observation."""

    annual = annual_only(df)

    if annual.empty:
        return None

    return annual.iloc[-1]


def confidence_from_strength(
    strength,
    minimum=61,
    maximum=95,
):
    """
    Convert a normalized signal strength in [0, 1]
    into confidence percentage.
    """

    strength = max(0.0, min(1.0, strength))

    return round(
        minimum
        + strength * (maximum - minimum),
        2,
    )


def add_result(
    results,
    company_id,
    result_type,
    rule_id,
    text,
    confidence,
):
    """Append a result only when confidence exceeds 60%."""

    if confidence <= 60:
        return

    results.append(
        {
            "company_id": company_id,
            "type": result_type,
            "rule_id": rule_id,
            "text": text,
            "confidence_pct": round(
                confidence,
                2,
            ),
        }
    )


def generate_for_company(
    company_id,
    ratios,
    pl,
    bs,
    cf,
    market,
    sector,
):
    """Evaluate all configured rules for one company."""

    results = []

    company_ratios = ratios[
        ratios["company_id"] == company_id
    ]

    company_pl = pl[
        pl["company_id"] == company_id
    ]

    company_bs = bs[
        bs["company_id"] == company_id
    ]

    company_cf = cf[
        cf["company_id"] == company_id
    ]

    company_market = market[
        market["company_id"] == company_id
    ]

    annual_ratios = annual_only(
        company_ratios
    )

    annual_pl = annual_only(
        company_pl
    )

    annual_bs = annual_only(
        company_bs
    )

    annual_cf = annual_only(
        company_cf
    )

    latest_ratios = latest_row(
        company_ratios
    )

    latest_pl = latest_row(
        company_pl
    )

    latest_bs = latest_row(
        company_bs
    )

    latest_cf = latest_row(
        company_cf
    )

    latest_market = (
        company_market.sort_values("year").iloc[-1]
        if not company_market.empty
        else None
    )

    # -----------------------------------------------------------
    # PRO-01 — ROE > 20% sustained for 3+ years
    # -----------------------------------------------------------

    if not annual_ratios.empty:
        roe = pd.to_numeric(
            annual_ratios[
                "return_on_equity_pct"
            ],
            errors="coerce",
        ).dropna()

        if len(roe) >= 3:
            recent = roe.tail(3)

            if (recent > 20).all():

                strength = min(
                    1.0,
                    float(
                        (recent.mean() - 20)
                        / 20
                    ),
                )

                add_result(
                    results,
                    company_id,
                    "pro",
                    "PRO-01",
                    PRO_RULES["PRO-01"],
                    confidence_from_strength(
                        strength
                    ),
                )

    # -----------------------------------------------------------
    # PRO-02 — FCF positive for 5+ consecutive years
    # -----------------------------------------------------------

    if not annual_ratios.empty:

        fcf = pd.to_numeric(
            annual_ratios[
                "free_cash_flow_cr"
            ],
            errors="coerce",
        ).dropna()

        if len(fcf) >= 5:

            consecutive = 0

            for value in reversed(
                fcf.tolist()
            ):
                if value > 0:
                    consecutive += 1
                else:
                    break

            if consecutive >= 5:

                strength = min(
                    1.0,
                    consecutive / 10,
                )

                add_result(
                    results,
                    company_id,
                    "pro",
                    "PRO-02",
                    PRO_RULES["PRO-02"],
                    confidence_from_strength(
                        strength
                    ),
                )

    # -----------------------------------------------------------
    # PRO-03 — Debt-free
    # -----------------------------------------------------------

    if latest_ratios is not None:

        de = latest_ratios.get(
            "debt_to_equity"
        )

        if pd.notna(de) and de == 0:

            add_result(
                results,
                company_id,
                "pro",
                "PRO-03",
                PRO_RULES["PRO-03"],
                95,
            )

    # -----------------------------------------------------------
    # PRO-04 — Revenue CAGR > 15%
    # -----------------------------------------------------------

    if latest_ratios is not None:

        value = latest_ratios.get(
            "revenue_cagr_5yr"
        )

        if pd.notna(value) and value > 15:

            strength = min(
                1.0,
                (float(value) - 15) / 15,
            )

            add_result(
                results,
                company_id,
                "pro",
                "PRO-04",
                PRO_RULES["PRO-04"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # PRO-05 — OPM > 25%
    # -----------------------------------------------------------

    if latest_ratios is not None:

        opm = latest_ratios.get(
            "operating_profit_margin_pct"
        )

        if pd.notna(opm) and opm > 25:

            strength = min(
                1.0,
                (float(opm) - 25) / 25,
            )

            add_result(
                results,
                company_id,
                "pro",
                "PRO-05",
                PRO_RULES["PRO-05"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # PRO-06 — PAT CAGR > 20%
    # -----------------------------------------------------------

    if latest_ratios is not None:

        value = latest_ratios.get(
            "pat_cagr_5yr"
        )

        if pd.notna(value) and value > 20:

            strength = min(
                1.0,
                (float(value) - 20) / 20,
            )

            add_result(
                results,
                company_id,
                "pro",
                "PRO-06",
                PRO_RULES["PRO-06"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # PRO-07 — ICR > 10 OR debt free
    # -----------------------------------------------------------

    if latest_ratios is not None:

        icr = latest_ratios.get(
            "interest_coverage"
        )

        de = latest_ratios.get(
            "debt_to_equity"
        )

        if (
            pd.notna(icr)
            and icr > 10
        ):

            strength = min(
                1.0,
                (float(icr) - 10) / 20,
            )

            add_result(
                results,
                company_id,
                "pro",
                "PRO-07",
                PRO_RULES["PRO-07"],
                confidence_from_strength(
                    strength
                ),
            )

        elif (
            pd.notna(de)
            and de == 0
        ):

            add_result(
                results,
                company_id,
                "pro",
                "PRO-07",
                PRO_RULES["PRO-07"],
                90,
            )

    # -----------------------------------------------------------
    # PRO-08 — Dividend yield > 2% + positive FCF
    # -----------------------------------------------------------

    if (
        latest_market is not None
        and latest_ratios is not None
    ):

        dividend_yield = latest_market.get(
            "dividend_yield_pct"
        )

        fcf = latest_ratios.get(
            "free_cash_flow_cr"
        )

        if (
            pd.notna(dividend_yield)
            and dividend_yield > 2
            and pd.notna(fcf)
            and fcf > 0
        ):

            strength = min(
                1.0,
                (float(dividend_yield) - 2) / 3,
            )

            add_result(
                results,
                company_id,
                "pro",
                "PRO-08",
                PRO_RULES["PRO-08"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # PRO-09 — EPS CAGR > 15%
    # -----------------------------------------------------------

    if latest_ratios is not None:

        value = latest_ratios.get(
            "eps_cagr_5yr"
        )

        if pd.notna(value) and value > 15:

            strength = min(
                1.0,
                (float(value) - 15) / 15,
            )

            add_result(
                results,
                company_id,
                "pro",
                "PRO-09",
                PRO_RULES["PRO-09"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # PRO-10 — ROE improving for 3 years
    # -----------------------------------------------------------

    if len(annual_ratios) >= 3:

        roe = pd.to_numeric(
            annual_ratios[
                "return_on_equity_pct"
            ],
            errors="coerce",
        ).dropna()

        if len(roe) >= 3:

            recent = roe.tail(3)

            if (
                recent.iloc[0]
                < recent.iloc[1]
                < recent.iloc[2]
            ):

                strength = min(
                    1.0,
                    float(
                        (
                            recent.iloc[-1]
                            - recent.iloc[0]
                        )
                        / max(
                            abs(recent.iloc[0]),
                            1,
                        )
                    ),
                )

                add_result(
                    results,
                    company_id,
                    "pro",
                    "PRO-10",
                    PRO_RULES["PRO-10"],
                    confidence_from_strength(
                        strength
                    ),
                )

    # -----------------------------------------------------------
    # PRO-11 — Revenue CAGR < PAT CAGR
    # -----------------------------------------------------------

    if latest_ratios is not None:

        revenue_cagr = latest_ratios.get(
            "revenue_cagr_5yr"
        )

        pat_cagr = latest_ratios.get(
            "pat_cagr_5yr"
        )

        if (
            pd.notna(revenue_cagr)
            and pd.notna(pat_cagr)
            and pat_cagr > revenue_cagr
        ):

            strength = min(
                1.0,
                float(
                    pat_cagr - revenue_cagr
                ) / 20,
            )

            add_result(
                results,
                company_id,
                "pro",
                "PRO-11",
                PRO_RULES["PRO-11"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # PRO-12 — Assets growing + debt declining
    # -----------------------------------------------------------

    if len(annual_bs) >= 2:

        assets = pd.to_numeric(
            annual_bs["total_assets"],
            errors="coerce",
        )

        debt = pd.to_numeric(
            annual_bs["borrowings"],
            errors="coerce",
        )

        if (
            assets.iloc[-1] > assets.iloc[-2]
            and debt.iloc[-1] < debt.iloc[-2]
        ):

            add_result(
                results,
                company_id,
                "pro",
                "PRO-12",
                PRO_RULES["PRO-12"],
                80,
            )

        # ---------------------------------------------------------
        # PRO-13: Positive Financial Trend
        # ---------------------------------------------------------

        pro_13 = pro_13_positive_financial_trend(
            ratios,
            cashflow=cf,
        )

        if pro_13 is not None:
            results.append(
                {
                    "company_id": company_id,
                    "type": "pro",
                    **pro_13,
                }
            )

    # ===========================================================
    # CONS
    # ===========================================================

    # -----------------------------------------------------------
    # CON-01 — D/E > 2 for non-financial
    # -----------------------------------------------------------

    if latest_ratios is not None:

        de = latest_ratios.get(
            "debt_to_equity"
        )

        if (
            pd.notna(de)
            and de > 2
            and sector != "Financials"
        ):

            strength = min(
                1.0,
                (float(de) - 2) / 3,
            )

            add_result(
                results,
                company_id,
                "con",
                "CON-01",
                CON_RULES["CON-01"].format(
                    value=float(de)
                ),
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # CON-02 — FCF negative for 3 consecutive years
    # -----------------------------------------------------------

    if not annual_ratios.empty:

        fcf = pd.to_numeric(
            annual_ratios[
                "free_cash_flow_cr"
            ],
            errors="coerce",
        ).dropna()

        if len(fcf) >= 3:
            if has_consecutive(
                fcf.tolist(),
                lambda x: x < 0,
                3,
            ):
                add_result(
                    results,
                    company_id,
                    "con",
                    "CON-02",
                    CON_RULES["CON-02"],
                    90,
                )

    # -----------------------------------------------------------
    # CON-03 — OPM declining 3 years
    # -----------------------------------------------------------

    if len(annual_ratios) >= 3:

        opm = pd.to_numeric(
            annual_ratios[
                "operating_profit_margin_pct"
            ],
            errors="coerce",
        ).dropna()

        if len(opm) >= 3:

            recent = opm.tail(3)

            if (
                recent.iloc[0]
                > recent.iloc[1]
                > recent.iloc[2]
            ):

                add_result(
                    results,
                    company_id,
                    "con",
                    "CON-03",
                    CON_RULES["CON-03"],
                    85,
                )

    # -----------------------------------------------------------
    # CON-04 — Net loss latest year
    # -----------------------------------------------------------

    if latest_pl is not None:

        net_profit = latest_pl.get(
            "net_profit"
        )

        if (
            pd.notna(net_profit)
            and net_profit < 0
        ):

            add_result(
                results,
                company_id,
                "con",
                "CON-04",
                CON_RULES["CON-04"],
                95,
            )

    # -----------------------------------------------------------
    # CON-05 — Revenue declining for 2 years
    # -----------------------------------------------------------

    if len(annual_pl) >= 3:

        sales = pd.to_numeric(
            annual_pl["sales"],
            errors="coerce",
        ).dropna()

        if len(sales) >= 3:

            recent = sales.tail(3)

            if (
                recent.iloc[0]
                > recent.iloc[1]
                > recent.iloc[2]
            ):

                add_result(
                    results,
                    company_id,
                    "con",
                    "CON-05",
                    CON_RULES["CON-05"],
                    85,
                )

    # -----------------------------------------------------------
    # CON-06 — ICR < 1.5
    # -----------------------------------------------------------

    if latest_ratios is not None:

        icr = latest_ratios.get(
            "interest_coverage"
        )

        if pd.notna(icr) and icr < 1.5:

            strength = min(
                1.0,
                (1.5 - float(icr)) / 1.5,
            )

            add_result(
                results,
                company_id,
                "con",
                "CON-06",
                CON_RULES["CON-06"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # CON-07 — Dividend payout > 100%
    # -----------------------------------------------------------

    if latest_ratios is not None:

        payout = latest_ratios.get(
            "dividend_payout_ratio_pct"
        )

        if pd.notna(payout) and payout > 100:

            strength = min(
                1.0,
                (float(payout) - 100) / 100,
            )

            add_result(
                results,
                company_id,
                "con",
                "CON-07",
                CON_RULES["CON-07"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # CON-08 — D/E rising 3 years
    # -----------------------------------------------------------

    if len(annual_ratios) >= 3:

        de = pd.to_numeric(
            annual_ratios[
                "debt_to_equity"
            ],
            errors="coerce",
        ).dropna()

        if len(de) >= 3:

            recent = de.tail(3)

            if (
                recent.iloc[0]
                < recent.iloc[1]
                < recent.iloc[2]
            ):

                add_result(
                    results,
                    company_id,
                    "con",
                    "CON-08",
                    CON_RULES["CON-08"],
                    85,
                )

    # -----------------------------------------------------------
    # CON-09 — EPS declining 3 years
    # -----------------------------------------------------------

    if len(annual_pl) >= 3:

        eps = pd.to_numeric(
            annual_pl["eps"],
            errors="coerce",
        ).dropna()

        if len(eps) >= 3:

            recent = eps.tail(3)

            if (
                recent.iloc[0]
                > recent.iloc[1]
                > recent.iloc[2]
            ):

                add_result(
                    results,
                    company_id,
                    "con",
                    "CON-09",
                    CON_RULES["CON-09"],
                    85,
                )

    # -----------------------------------------------------------
    # CON-10 — ROCE < 10%
    # -----------------------------------------------------------

    if latest_ratios is not None:

        roce = latest_ratios.get(
            "return_on_capital_employed_pct"
        )

        if pd.notna(roce) and roce < 10:

            strength = min(
                1.0,
                (10 - float(roce)) / 10,
            )

            add_result(
                results,
                company_id,
                "con",
                "CON-10",
                CON_RULES["CON-10"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # CON-11 — Net Debt > 3x EBITDA
    # -----------------------------------------------------------

    if (
        latest_bs is not None
        and latest_market is not None
    ):

        borrowings = latest_bs.get(
            "borrowings"
        )

        cash = latest_bs.get(
            "other_asset"
        )

        ev_ebitda = latest_market.get(
            "ev_ebitda"
        )

        # EV/EBITDA = EV / EBITDA
        # Therefore EBITDA ≈ EV / EV/EBITDA.
        enterprise_value = latest_market.get(
            "enterprise_value_cr"
        )

        if (
            pd.notna(borrowings)
            and pd.notna(enterprise_value)
            and pd.notna(ev_ebitda)
            and ev_ebitda > 0
        ):

            ebitda = (
                enterprise_value
                / ev_ebitda
            )

            net_debt = (
                float(borrowings)
                - float(cash)
                if pd.notna(cash)
                else float(borrowings)
            )

            if (
                ebitda > 0
                and net_debt > 3 * ebitda
            ):

                strength = min(
                    1.0,
                    (
                        net_debt / ebitda - 3
                    ) / 3,
                )

                add_result(
                    results,
                    company_id,
                    "con",
                    "CON-11",
                    CON_RULES["CON-11"],
                    confidence_from_strength(
                        strength
                    ),
                )

    # -----------------------------------------------------------
    # CON-12 — Revenue CAGR < 5%
    # -----------------------------------------------------------

    if latest_ratios is not None:

        revenue_cagr = latest_ratios.get(
            "revenue_cagr_5yr"
        )

        if (
            pd.notna(revenue_cagr)
            and revenue_cagr < 5
        ):

            strength = min(
                1.0,
                (5 - float(revenue_cagr)) / 5,
            )

            add_result(
                results,
                company_id,
                "con",
                "CON-12",
                CON_RULES["CON-12"],
                confidence_from_strength(
                    strength
                ),
            )

    # -----------------------------------------------------------
    # CON-FALLBACK — No existing con rule triggered
    # -----------------------------------------------------------

    if not any(
        result["type"] == "con"
        for result in results
    ):
        add_result(
            results,
            company_id,
            "con",
            "CON-FALLBACK",
            (
                "Current financial indicators do not show "
                "a material weakness, but continued monitoring "
                "is warranted as conditions can change."
            ),
            65,
        )

    return results


def generate():
    """Generate pros and cons for all companies."""

    (
        companies,
        ratios,
        pl,
        bs,
        cf,
        market,
        sectors,
    ) = load_data()

    results = []

    sector_map = (
        sectors
        .drop_duplicates("company_id")
        .set_index("company_id")["sector"]
        .to_dict()
    )

    for company_id in companies["id"]:

        sector = sector_map.get(
            company_id
        )

        company_results = generate_for_company(
            company_id,
            ratios,
            pl,
            bs,
            cf,
            market,
            sector,
        )

        results.extend(
            company_results
        )

    result_df = pd.DataFrame(
        results,
        columns=[
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct",
        ],
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    return result_df


def validate_output(result_df, companies):
    """Verify the Sprint 5 requirement of at least one pro and con."""

    company_ids = set(
        companies["id"]
    )

    generated_ids = set(
        result_df["company_id"]
    )

    missing_companies = (
        company_ids - generated_ids
    )

    pro_counts = (
        result_df[
            result_df["type"] == "pro"
        ]
        .groupby("company_id")
        .size()
    )

    con_counts = (
        result_df[
            result_df["type"] == "con"
        ]
        .groupby("company_id")
        .size()
    )

    missing_pro = [
        company
        for company in company_ids
        if pro_counts.get(company, 0) == 0
    ]

    missing_con = [
        company
        for company in company_ids
        if con_counts.get(company, 0) == 0
    ]

    print(
        f"Companies: {len(company_ids)}"
    )

    print(
        f"Companies represented: "
        f"{len(generated_ids)}"
    )

    print(
        f"Missing companies: "
        f"{len(missing_companies)}"
    )

    print(
        f"Missing pros: "
        f"{len(missing_pro)}"
    )

    print(
        f"Missing cons: "
        f"{len(missing_con)}"
    )

    if missing_companies:
        print(
            "Missing company IDs:",
            sorted(missing_companies),
        )

    if missing_pro:
        print(
            "Companies without pros:",
            sorted(missing_pro),
        )

    if missing_con:
        print(
            "Companies without cons:",
            sorted(missing_con),
        )

    return (
        not missing_companies
        and not missing_pro
        and not missing_con
    )

def has_consecutive(values, predicate, count):
    streak = 0

    for value in values:
        if predicate(value):
            streak += 1

            if streak >= count:
                return True
        else:
            streak = 0

    return False

def has_strictly_decreasing(values, count):
    values = list(values)

    for i in range(len(values) - count + 1):
        window = values[i:i + count]

        if all(
            window[j] > window[j + 1]
            for j in range(len(window) - 1)
        ):
            return True

    return False


def pro_13_positive_financial_trend(
    ratios,
    cashflow=None,
):
    """
    PRO-13: Positive Financial Trend

    Requires at least 2 independent financial metrics
    to show material improvement over the latest 3
    annual observations.

    Signals:
        ROE  : +5 percentage points
        D/E  : -0.20
        ICR  : +20%
        OPM  : +3 percentage points
        FCF  : +20%, positive values only
    """

    annual = annual_only(ratios)

    if annual.empty:
        return None

    annual = annual.sort_values("fiscal_year")

    if len(annual) < 3:
        return None

    recent = annual.tail(3)

    oldest = recent.iloc[0]
    latest = recent.iloc[-1]

    signals = []

    # ---------------------------------------------------------
    # ROE improvement
    # ---------------------------------------------------------

    roe_old = oldest.get("return_on_equity_pct")
    roe_new = latest.get("return_on_equity_pct")

    if (
        pd.notna(roe_old)
        and pd.notna(roe_new)
        and roe_new - roe_old >= 5
    ):
        signals.append("ROE")

    # ---------------------------------------------------------
    # Debt-to-equity reduction
    # ---------------------------------------------------------

    de_old = oldest.get("debt_to_equity")
    de_new = latest.get("debt_to_equity")

    if (
        pd.notna(de_old)
        and pd.notna(de_new)
        and de_old - de_new >= 0.20
    ):
        signals.append("D/E")

    # ---------------------------------------------------------
    # Interest coverage improvement
    # ---------------------------------------------------------

    icr_old = oldest.get("interest_coverage")
    icr_new = latest.get("interest_coverage")

    if (
        pd.notna(icr_old)
        and pd.notna(icr_new)
        and icr_old > 0
        and icr_new >= icr_old * 1.20
    ):
        signals.append("ICR")

    # ---------------------------------------------------------
    # Operating margin improvement
    # ---------------------------------------------------------

    opm_old = oldest.get(
        "operating_profit_margin_pct"
    )
    opm_new = latest.get(
        "operating_profit_margin_pct"
    )

    if (
        pd.notna(opm_old)
        and pd.notna(opm_new)
        and opm_new - opm_old >= 3
    ):
        signals.append("OPM")

    # ---------------------------------------------------------
    # FCF improvement
    # ---------------------------------------------------------

    fcf_old = oldest.get("free_cash_flow_cr")
    fcf_new = latest.get("free_cash_flow_cr")

    if (
        pd.notna(fcf_old)
        and pd.notna(fcf_new)
        and fcf_old > 0
        and fcf_new > fcf_old
        and fcf_new >= fcf_old * 1.20
    ):
        signals.append("FCF")

    # ---------------------------------------------------------
    # Require at least 2 independent signals
    # ---------------------------------------------------------

    if len(signals) < 2:
        return None

    # Confidence based on signal count.
    confidence = min(
        95,
        60 + (len(signals) - 2) * 10
    )

    return {
        "rule_id": "PRO-13",
        "text": (
            "Recent improvement across multiple financial "
            "metrics indicates strengthening business "
            "fundamentals and financial resilience."
        ),
        "confidence_pct": confidence,
    }

if __name__ == "__main__":

    (
        companies,
        *_,
    ) = load_data()

    result = generate()

    valid = validate_output(
        result,
        companies,
    )

    print()
    print(
        f"Generated {len(result)} pros/cons."
    )

    print(
        f"Output: {OUTPUT_PATH}"
    )

    if not valid:
        raise SystemExit(
            "Pros/cons validation failed."
        )

