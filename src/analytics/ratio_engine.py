from pathlib import Path
import sqlite3

import pandas as pd
from loguru import logger

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage,
    asset_turnover,
    high_leverage_flag,
    debt_free_label,
)

from src.analytics.cagr import (
    sales_cagr,
    profit_cagr,
    eps_cagr,
    book_value_cagr,
    stock_price_cagr,
)

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality_score,
    capex_intensity,
    capex_label,
    fcf_conversion_rate,
    capital_allocation_pattern,
)


class RatioEngine:
    """
    Computes financial KPIs from SQLite data.
    """

    def __init__(self, database_path: str = "db/nifty100.db"):
        self.database_path = Path(database_path)
        self.connection = None

        self.edge_cases = []

    # -------------------------------------------------------
    # Database
    # -------------------------------------------------------

    def connect(self):

        self.connection = sqlite3.connect(self.database_path)

        logger.info(f"Connected to database: {self.database_path}")

    def close(self):

        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")

    # -------------------------------------------------------
    # Profitability Ratios
    # -------------------------------------------------------

    def profitability_ratios(self):

        logger.info("Computing profitability ratios...")

        query = """
        SELECT
            p.company_id,
            p.year,

            p.sales,
            p.operating_profit,
            p.opm_percentage,
            p.net_profit,

            b.equity_capital,
            b.reserves,
            b.borrowings,
            b.total_assets

        FROM profitandloss p

        LEFT JOIN balancesheet b

            ON p.company_id = b.company_id
           AND p.year = b.year
        """

        df = pd.read_sql(query, self.connection)

        results = []

        for _, row in df.iterrows():

            npm = net_profit_margin(
                row.net_profit,
                row.sales,
            )

            opm = operating_profit_margin(
                row.operating_profit,
                row.sales,
            )

            roe = return_on_equity(
                row.net_profit,
                row.equity_capital,
                row.reserves,
            )

            roce = return_on_capital_employed(
                row.operating_profit,
                row.equity_capital,
                row.reserves,
                row.borrowings,
            )

            roa = return_on_assets(
                row.net_profit,
                row.total_assets,
            )

            # ----------------------------------------
            # OPM Cross-check
            # ----------------------------------------

            stored = row.opm_percentage

            if (
                opm is not None
                and pd.notna(stored)
                and abs(opm - stored) > 1
            ):

                self.edge_cases.append({

                    "company_id": row.company_id,

                    "year": row.year,

                    "stored_opm": stored,

                    "computed_opm": opm,

                    "difference": round(abs(opm - stored), 2),

                })

            results.append({

                "company_id": row.company_id,

                "year": row.year,

                "net_profit_margin_pct": npm,

                "operating_profit_margin_pct": opm,

                "return_on_equity_pct": roe,

                "return_on_capital_employed_pct": roce,

                "return_on_assets_pct": roa,

            })

        logger.info(f"Computed {len(results)} profitability records.")

        return pd.DataFrame(results)

    # -------------------------------------------------------
    # Export Edge Cases
    # -------------------------------------------------------

    def export_edge_cases(
        self,
        output_path="data/output/opm_edge_cases.csv"
    ):

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        pd.DataFrame(
            self.edge_cases
        ).to_csv(
            output_path,
            index=False,
        )

        logger.info(
            f"Saved {len(self.edge_cases)} edge cases to {output_path}"
        )

    def save_profitability_ratios(
        self,
        df,
        output_path="data/output/profitability_ratios.csv"
    ):
        """
        Save computed profitability ratios.
        """

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        df.to_csv(
            output_path,
            index=False,
        )

        logger.info(
            f"Saved {len(df)} profitability ratios to {output_path}"
        )

    def leverage_efficiency_ratios(self):

        logger.info("Computing leverage & efficiency ratios...")

        query = """
            SELECT

                p.company_id,
                p.year,

                p.sales,
                p.operating_profit,
                p.interest,
                p.other_income,

                b.borrowings,
                b.equity_capital,
                b.reserves,
                b.total_assets,
                b.investments,

                s.sector

            FROM profitandloss p

            LEFT JOIN balancesheet b

                ON p.company_id = b.company_id
            AND p.year = b.year

            LEFT JOIN sectors s

                ON p.company_id = s.company_id
            """

        df = pd.read_sql(query, self.connection)

        results = []

        for _, row in df.iterrows():

            dte = debt_to_equity(
                row.borrowings,
                row.equity_capital,
                row.reserves,
            )

            ic = interest_coverage(
                row.operating_profit,
                row.other_income,
                row.interest,
            )

            at = asset_turnover(
                row.sales,
                row.total_assets,
            )

            # high = high_leverage_flag(dte)
            is_financial = (
                isinstance(row.sector, str)
                and row.sector.strip().lower() == "financials"
            )

            if is_financial:

                high = False

                if dte is not None and dte > 5:

                    logger.info(
                        f"{row.company_id} ({row.year}) - "
                        "High leverage flag suppressed for Financials sector."
                    )

            else:

                high = high_leverage_flag(dte)

            debt_free = debt_free_label(
                row.borrowings,
            )

            results.append({

                "company_id": row.company_id,

                "year": row.year,

                "debt_to_equity": dte,

                "interest_coverage": ic,

                "asset_turnover": at,

                "high_leverage_flag": high,

                "debt_free": debt_free,

            })

        logger.info(
            f"Computed {len(results)} leverage records."
        )

        return pd.DataFrame(results)

    def build_ratio_table(self):

        profitability = self.profitability_ratios()

        leverage = self.leverage_efficiency_ratios()

        growth = self.growth_ratios()

        cashflow = self.cashflow_ratios()

        ratios = (
            profitability
            .merge(
                leverage,
                on=["company_id", "year"],
                how="left",
            )
            .merge(
                growth,
                on=["company_id", "year"],
                how="left",
            )
            .merge(
                cashflow,
                on=["company_id", "year"],
                how="left",
            )
        )

        # -------------------------------------------------------
        # Fetch raw fields required for financial_ratios table
        # -------------------------------------------------------

        query = """
        SELECT

            p.company_id,
            p.year,

            p.eps,
            p.dividend_payout,

            c.book_value,

            b.borrowings,

            cf.operating_activity

        FROM profitandloss p

        LEFT JOIN companies c
            ON p.company_id = c.id

        LEFT JOIN balancesheet b
            ON p.company_id = b.company_id
        AND p.year = b.year

        LEFT JOIN cashflow cf
            ON p.company_id = cf.company_id
        AND p.year = cf.year
        """

        raw = pd.read_sql(query, self.connection)

        ratios = ratios.merge(
            raw,
            on=["company_id", "year"],
            how="left",
        )

        logger.info(
            f"Built ratio table ({len(ratios)} rows)."
        )

        return ratios

    def save_ratio_table(
    self,
    df,
    output_path="data/output/financial_ratios_computed.csv",
    ):

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        df.to_csv(
            output_path,
            index=False,
        )

        logger.info(
            f"Saved {len(df)} computed ratios to {output_path}"
        )

    def growth_ratios(self):

        logger.info("Computing growth ratios...")

        query = """
        SELECT

            p.company_id,
            p.year,

            p.sales,
            p.net_profit,
            p.eps,

            c.book_value,

            AVG(sp.adjusted_close) AS adjusted_close

        FROM profitandloss p

        LEFT JOIN companies c
            ON p.company_id = c.id

        LEFT JOIN stock_prices sp
            ON p.company_id = sp.company_id
        AND substr(sp.date, 1, 4) = substr(p.year, -4)

        GROUP BY

            p.company_id,
            p.year,
            p.sales,
            p.net_profit,
            p.eps,
            c.book_value

        ORDER BY
            p.company_id,
            p.year
        """

        df = pd.read_sql(query, self.connection)

        results = []

        for company, group in df.groupby("company_id"):

            group = group.sort_values("year").reset_index(drop=True)

            first = group.iloc[0]

            for i, row in group.iterrows():

                if i == 0:

                    sales_growth = None
                    profit_growth = None
                    eps_growth = None
                    book_growth = None
                    stock_growth = None

                else:

                    years = i

                    sales_growth = sales_cagr(
                        first.sales,
                        row.sales,
                        years,
                    )

                    profit_growth = profit_cagr(
                        first.net_profit,
                        row.net_profit,
                        years,
                    )

                    eps_growth = eps_cagr(
                        first.eps,
                        row.eps,
                        years,
                    )

                    book_growth = book_value_cagr(
                        first.book_value,
                        row.book_value,
                        years,
                    )

                    stock_growth = stock_price_cagr(
                        first.adjusted_close,
                        row.adjusted_close,
                        years,
                    )

                results.append({

                    "company_id": row.company_id,

                    "year": row.year,

                    "sales_cagr": sales_growth,

                    "profit_cagr": profit_growth,

                    "eps_cagr": eps_growth,

                    "book_value_cagr": book_growth,

                    "stock_price_cagr": stock_growth,

                })

        logger.info(
            f"Computed {len(results)} growth records."
        )

        return pd.DataFrame(results)

    def cashflow_ratios(self):

        logger.info("Computing cash flow KPIs...")

        query = """
        SELECT

            c.company_id,
            c.year,

            c.operating_activity,
            c.investing_activity,
            c.financing_activity,

            p.sales,
            p.net_profit,
            p.operating_profit

        FROM cashflow c

        LEFT JOIN profitandloss p

            ON c.company_id = p.company_id
        AND c.year = p.year

        ORDER BY
            c.company_id,
            c.year
        """

        df = pd.read_sql(query, self.connection)

        results = []
        allocation_rows = []

        for company, group in df.groupby("company_id"):

            group = group.sort_values("year").reset_index(drop=True)

            for i, row in group.iterrows():

                # ----------------------------
                # Free Cash Flow
                # ----------------------------

                fcf = free_cash_flow(
                    row.operating_activity,
                    row.investing_activity,
                )

                # ----------------------------
                # CFO Quality (Rolling 5-Year)
                # ----------------------------

                window = group.iloc[max(0, i - 4): i + 1]

                avg_cfo = window.operating_activity.mean()
                avg_pat = window.net_profit.mean()

                quality = cfo_quality_score(
                    avg_cfo,
                    avg_pat,
                )

                # ----------------------------
                # CapEx
                # ----------------------------

                intensity = capex_intensity(
                    row.investing_activity,
                    row.sales,
                )

                intensity_label = capex_label(
                    intensity,
                )

                # ----------------------------
                # FCF Conversion
                # ----------------------------

                conversion = fcf_conversion_rate(
                    fcf,
                    row.operating_profit,
                )

                # ----------------------------
                # Capital Allocation
                # ----------------------------

                pattern = capital_allocation_pattern(
                    row.operating_activity,
                    row.investing_activity,
                    row.financing_activity,
                    quality,
                )

                cfo_sign = "+" if row.operating_activity >= 0 else "-"
                cfi_sign = "+" if row.investing_activity >= 0 else "-"
                cff_sign = "+" if row.financing_activity >= 0 else "-"

                allocation_rows.append({

                    "company_id": row.company_id,

                    "year": row.year,

                    "cfo_sign": cfo_sign,

                    "cfi_sign": cfi_sign,

                    "cff_sign": cff_sign,

                    "pattern_label": pattern,

                })

                results.append({

                    "company_id": row.company_id,

                    "year": row.year,

                    "free_cash_flow": fcf,

                    "cfo_quality_score": quality,

                    "capex_intensity": intensity,

                    "capex_label": intensity_label,

                    "fcf_conversion_rate": conversion,

                    "capital_allocation_pattern": pattern,

                })

        # -----------------------------------
        # Export Capital Allocation CSV
        # -----------------------------------

        output_path = Path("data/output/capital_allocation.csv")

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        pd.DataFrame(
            allocation_rows
        ).to_csv(
            output_path,
            index=False,
        )

        logger.info(
            f"Saved {len(allocation_rows)} capital allocation records."
        )

        logger.info(
            f"Computed {len(results)} cash flow records."
        )

        return pd.DataFrame(results)

    def populate_financial_ratios(self):

        logger.info("Populating financial_ratios table...")

        ratios = self.build_ratio_table().copy()

        # -----------------------------------------
        # Rename columns to match DB schema
        # -----------------------------------------

        ratios = ratios.rename(columns={

            "free_cash_flow": "free_cash_flow_cr",
            "capex_intensity": "capex_cr",

            "eps": "earnings_per_share",
            "book_value": "book_value_per_share",
            "dividend_payout": "dividend_payout_ratio_pct",

            "borrowings": "total_debt_cr",
            "operating_activity": "cash_from_operations_cr",

            "sales_cagr": "revenue_cagr_5yr",
            "profit_cagr": "pat_cagr_5yr",
            "eps_cagr": "eps_cagr_5yr",

        })

        # -----------------------------------------
        # Composite Quality Score (placeholder)
        # -----------------------------------------

        ratios["composite_quality_score"] = None

        # -----------------------------------------
        # Keep only DB columns
        # -----------------------------------------

        ratios = ratios[[
            "company_id",
            "year",

            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "return_on_capital_employed_pct",

            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",

            "free_cash_flow_cr",
            "capex_cr",

            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",

            "total_debt_cr",
            "cash_from_operations_cr",

            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",

            "composite_quality_score",
        ]]

        # -----------------------------------------
        # Replace table contents
        # -----------------------------------------

        cursor = self.connection.cursor()

        cursor.execute("DELETE FROM financial_ratios")

        self.connection.commit()

        ratios.to_sql(
            "financial_ratios",
            self.connection,
            if_exists="append",
            index=False,
        )

        logger.info(
            f"Inserted {len(ratios)} rows into financial_ratios."
        )
