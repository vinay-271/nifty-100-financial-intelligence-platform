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

            b.borrowings,
            b.equity_capital,
            b.reserves,
            b.total_assets

        FROM profitandloss p

        LEFT JOIN balancesheet b

            ON p.company_id = b.company_id
        AND p.year = b.year
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
                row.interest,
            )

            at = asset_turnover(
                row.sales,
                row.total_assets,
            )

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
