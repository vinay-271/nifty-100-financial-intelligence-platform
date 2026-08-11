import sqlite3
from pathlib import Path
import re

import pandas as pd
import yaml
from loguru import logger

from src.screener.composite import compute_composite_quality_score


class ScreenerEngine:

    def __init__(
        self,
        db_path="db/nifty100.db",
        config_path="config/screener_config.yaml",
    ):
        self.db_path = Path(db_path)
        self.config_path = Path(config_path)

        self.connection = None
        self.config = None
        self.data = None

    def connect(self):
        """Connect to SQLite database."""
        self.connection = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")

    def load_config(self):
        """Load analyst-editable screener configuration."""
        with open(self.config_path, "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)

        logger.info("Screener configuration loaded.")

    def load_data(self):
        """
        Load all screener metrics from the required database tables.
        """

        query = """
        SELECT
            fr.company_id,
            fr.year,

            fr.net_profit_margin_pct,
            fr.operating_profit_margin_pct,
            fr.return_on_equity_pct,
            fr.return_on_capital_employed_pct,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.asset_turnover,
            fr.free_cash_flow_cr,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.eps_cagr_5yr,
            fr.composite_quality_score,

            p.sales,
            p.net_profit,
            p.eps,
            p.dividend_payout,

            m.market_cap_cr,
            m.pe_ratio,
            m.pb_ratio,
            m.dividend_yield_pct,

            s.sector

        FROM financial_ratios fr

        LEFT JOIN profitandloss p
            ON fr.company_id = p.company_id
            AND fr.year = p.year

        LEFT JOIN market_cap m
            ON fr.company_id = m.company_id
            AND CAST(
                substr(fr.year, instr(fr.year, ' ') + 1, 4)
                AS INTEGER
            ) = CAST(m.year AS INTEGER)

        LEFT JOIN sectors s
            ON fr.company_id = s.company_id
        """

        self.data = pd.read_sql(query, self.connection)

        logger.info(
            f"Loaded {len(self.data)} screener records."
        )

        return self.data

    @staticmethod
    def _is_financials(row):
        """Return True when company belongs to Financials sector."""
        return (
            isinstance(row["sector"], str)
            and row["sector"].strip().lower() == "financials"
        )

    def apply_filter(self, df, metric, operator, threshold):
        """
        Apply one threshold filter.

        Supported operators:
            min / >=
            max / <=
            eq / ==
        """

        if metric not in df.columns:
            raise ValueError(
                f"Unknown screener metric: {metric}"
            )

        if operator in ("min", ">="):
            return df[df[metric] >= threshold]

        if operator in ("max", "<="):
            return df[df[metric] <= threshold]

        if operator in ("eq", "=="):
            return df[df[metric] == threshold]

        raise ValueError(
            f"Unsupported operator: {operator}"
        )

    def screen(self, filters=None):
        """
        Apply custom threshold filters.

        Example:

        filters = {
            "roe_min": 15,
            "debt_to_equity_max": 1.0,
            "free_cash_flow_min": 0,
        }
        """

        if self.data is None:
            self.load_data()

        result = self.latest_annual_data()

        if not filters:
            return self._sort_result(result)

        for filter_name, threshold in filters.items():

            if threshold is None:
                continue

            # -------------------------
            # ROE
            # -------------------------
            if filter_name == "roe_min":
                result = result[
                    result["return_on_equity_pct"] >= threshold
                ]

            # -------------------------
            # Debt-to-Equity
            # -------------------------
            elif filter_name == "debt_to_equity_max":

                # Financials are exempt from D/E screening.
                is_financials = result.apply(
                    self._is_financials,
                    axis=1,
                )

                passes_de = (
                    result["debt_to_equity"] <= threshold
                )

                result = result[
                    is_financials | passes_de
                ]

            # -------------------------
            # Free Cash Flow
            # -------------------------
            elif filter_name == "free_cash_flow_min":
                result = result[
                    result["free_cash_flow_cr"] >= threshold
                ]

            # -------------------------
            # Revenue CAGR
            # -------------------------
            elif filter_name == "revenue_cagr_5yr_min":
                result = result[
                    result["revenue_cagr_5yr"] >= threshold
                ]

            # -------------------------
            # PAT CAGR
            # -------------------------
            elif filter_name == "pat_cagr_5yr_min":
                result = result[
                    result["pat_cagr_5yr"] >= threshold
                ]

            # -------------------------
            # OPM
            # -------------------------
            elif filter_name == "opm_min":
                result = result[
                    result["operating_profit_margin_pct"] >= threshold
                ]

            # -------------------------
            # P/E
            # -------------------------
            elif filter_name == "pe_ratio_max":
                result = result[
                    result["pe_ratio"] <= threshold
                ]

            # -------------------------
            # P/B
            # -------------------------
            elif filter_name == "pb_ratio_max":
                result = result[
                    result["pb_ratio"] <= threshold
                ]

            # -------------------------
            # Dividend Yield
            # -------------------------
            elif filter_name == "dividend_yield_min":
                result = result[
                    result["dividend_yield_pct"] >= threshold
                ]

            # -------------------------
            # Interest Coverage
            # -------------------------
            elif filter_name == "icr_min":

                # Debt-free companies have no interest
                # obligation, therefore ICR = infinity.
                icr = result["interest_coverage"].fillna(float("inf"))

                result = result[
                    icr >= threshold
                ]

            # -------------------------
            # Market Cap
            # -------------------------
            elif filter_name == "market_cap_min":
                result = result[
                    result["market_cap_cr"] >= threshold
                ]

            # -------------------------
            # Net Profit
            # -------------------------
            elif filter_name == "net_profit_min":
                result = result[
                    result["net_profit"] >= threshold
                ]

            # -------------------------
            # EPS CAGR
            # -------------------------
            elif filter_name == "eps_cagr_min":
                result = result[
                    result["eps_cagr_5yr"] >= threshold
                ]

            # -------------------------
            # Asset Turnover
            # -------------------------
            elif filter_name == "asset_turnover_min":
                result = result[
                    result["asset_turnover"] >= threshold
                ]

            # -------------------------
            # Sales
            # -------------------------
            elif filter_name == "sales_min":
                result = result[
                    result["sales"] >= threshold
                ]

            elif filter_name == "dividend_payout_ratio_max":
                result = result[
                    result["dividend_payout"] <= threshold
                ]

            elif filter_name == "revenue_cagr_3yr_min":
                result = result[
                    result["revenue_cagr_3yr"] >= threshold
                ]

            elif filter_name == "debt_to_equity_declining":
                if threshold:
                    result = result[
                        result["debt_to_equity_declining"] == True
                    ]

            else:
                raise ValueError(
                    f"Unknown screener filter: {filter_name}"
                )

        return self._sort_result(result)

    @staticmethod
    def _sort_result(df):
        """Sort results by composite quality score."""
        if "composite_quality_score" in df.columns:
            return df.sort_values(
                by="composite_quality_score",
                ascending=False,
                na_position="last",
            ).reset_index(drop=True)

        return df.reset_index(drop=True)

    def run_preset(self, preset_name):
        """Run a configured preset."""
        if self.config is None:
            self.load_config()

        presets = self.config.get("presets", {})

        if preset_name not in presets:
            raise ValueError(
                f"Unknown preset: {preset_name}"
            )

        return self.screen(
            presets[preset_name]
        )

    def latest_annual_data(self):
        """
        Return the latest complete annual record for each company.

        Excludes:
        - TTM
        - 9m / partial-year records
        - other non-standard periods
        """

        if self.data is None:
            self.load_data()

        df = self.data.copy()

        # Keep only standard annual periods such as:
        # Mar 2024, Dec 2023, Sep 2024, Jun 2024
        annual_mask = df["year"].astype(str).str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )

        annual = df[annual_mask].copy()

        # Extract fiscal year
        annual["fiscal_year"] = (
            annual["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        # Month number allows correct comparison when companies
        # use different financial year-end months.
        month_map = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
        }

        annual["period_month"] = (
            annual["year"]
            .str[:3]
            .map(month_map)
        )

        annual = annual.sort_values(
            ["company_id", "fiscal_year", "period_month"]
        )

        # Latest annual record for each company
        latest = (
            annual
            .groupby("company_id", as_index=False)
            .tail(1)
            .copy()
        )

        latest = latest.drop(
            columns=["fiscal_year", "period_month"]
        )

        latest = self._add_revenue_cagr_3yr(latest)

        latest = self._add_debt_to_equity_trend(latest)

        logger.info(
            f"Latest annual screener universe: {len(latest)} companies."
        )

        return latest.reset_index(drop=True)

    def _add_revenue_cagr_3yr(self, df):
        """
        Calculate 3-year Revenue CAGR using annual sales data.

        Uses the latest annual sales and the sales value
        three fiscal years earlier for each company.
        """

        query = """
            SELECT
                company_id,
                year,
                sales
            FROM profitandloss
            """

        sales = pd.read_sql(query, self.connection)

        # Keep only standard annual periods.
        sales = sales[
            sales["year"].astype(str).str.match(
                r"^[A-Za-z]{3}\s\d{4}$"
            )
        ].copy()

        sales["fiscal_year"] = (
            sales["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        sales = sales.sort_values(
            ["company_id", "fiscal_year"]
        )

        latest = (
            sales
            .groupby("company_id", as_index=False)
            .tail(1)
            [["company_id", "fiscal_year", "sales"]]
            .rename(
                columns={
                    "fiscal_year": "latest_fiscal_year",
                    "sales": "latest_sales",
                }
            )
        )

        base = sales.rename(
            columns={
                "fiscal_year": "base_fiscal_year",
                "sales": "base_sales",
            }
        )

        latest = latest.merge(
            base[
                [
                    "company_id",
                    "base_fiscal_year",
                    "base_sales",
                ]
            ],
            left_on=[
                "company_id",
            ],
            right_on=[
                "company_id",
            ],
            how="left",
        )

        latest = latest[
            latest["base_fiscal_year"]
            == latest["latest_fiscal_year"] - 3
        ].copy()

        latest["revenue_cagr_3yr"] = (
            (
                latest["latest_sales"]
                / latest["base_sales"]
            ) ** (1 / 3) - 1
        ) * 100

        latest.loc[
            latest["base_sales"] <= 0,
            "revenue_cagr_3yr"
        ] = None

        cagr = latest[
            [
                "company_id",
                "revenue_cagr_3yr",
            ]
        ]

        return df.merge(
            cagr,
            on="company_id",
            how="left",
        )

    def _add_debt_to_equity_trend(self, df):
        """
        Determine whether the latest annual D/E is lower
        than the immediately preceding annual D/E.
        """

        query = """
            SELECT
                company_id,
                year,
                debt_to_equity
            FROM financial_ratios
        """

        history = pd.read_sql(query, self.connection)

        history = history[
            history["year"].astype(str).str.match(
                r"^[A-Za-z]{3}\s\d{4}$"
            )
        ].copy()

        history["fiscal_year"] = (
            history["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        history = history.sort_values(
            ["company_id", "fiscal_year"]
        )

        history["previous_debt_to_equity"] = (
            history
            .groupby("company_id")["debt_to_equity"]
            .shift(1)
        )

        latest = (
            history
            .groupby("company_id", as_index=False)
            .tail(1)
            .copy()
        )

        latest["debt_to_equity_declining"] = (
            latest["debt_to_equity"]
            < latest["previous_debt_to_equity"]
        )

        return df.merge(
            latest[
                [
                    "company_id",
                    "debt_to_equity_declining",
                ]
            ],
            on="company_id",
            how="left",
        )

    def _add_fcf_cagr_5yr(self, df):
        """
        Calculate 5-year FCF CAGR using financial_ratios.free_cash_flow_cr history.

        Uses the latest annual FCF and the FCF value
        five fiscal years earlier for each company.

        Returns None if base_fcf <= 0 or latest_fcf <= 0 (Sprint 2 CAGR convention).
        """

        query = """
            SELECT
                company_id,
                year,
                free_cash_flow_cr
            FROM financial_ratios
            """

        fcf = pd.read_sql(query, self.connection)

        # Keep only standard annual periods.
        annual_mask = fcf["year"].astype(str).str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )
        fcf = fcf[annual_mask].copy()

        fcf["fiscal_year"] = (
            fcf["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        fcf = fcf.sort_values(
            ["company_id", "fiscal_year"]
        )

        latest = (
            fcf
            .groupby("company_id", as_index=False)
            .tail(1)
            [["company_id", "fiscal_year", "free_cash_flow_cr"]]
            .rename(
                columns={
                    "fiscal_year": "latest_fiscal_year",
                    "free_cash_flow_cr": "latest_fcf",
                }
            )
        )

        base = fcf.rename(
            columns={
                "fiscal_year": "base_fiscal_year",
                "free_cash_flow_cr": "base_fcf",
            }
        )

        latest = latest.merge(
            base[
                [
                    "company_id",
                    "base_fiscal_year",
                    "base_fcf",
                ]
            ],
            left_on=[
                "company_id",
            ],
            right_on=[
                "company_id",
            ],
            how="left",
        )

        latest = latest[
            latest["base_fiscal_year"]
            == latest["latest_fiscal_year"] - 5
        ].copy()

        # Sprint 2 CAGR convention: None if base <= 0 OR latest <= 0
        latest["fcf_cagr_5yr"] = None
        valid_mask = (latest["base_fcf"] > 0) & (latest["latest_fcf"] > 0)
        latest.loc[valid_mask, "fcf_cagr_5yr"] = (
            (
                latest.loc[valid_mask, "latest_fcf"]
                / latest.loc[valid_mask, "base_fcf"]
            ) ** (1 / 5) - 1
        ) * 100

        cagr = latest[
            [
                "company_id",
                "fcf_cagr_5yr",
            ]
        ]

        return df.merge(
            cagr,
            on="company_id",
            how="left",
        )

    def _add_cfo_pat_ratio(self, df):
        """
        Calculate CFO/PAT ratio using latest annual operating cash flow
        and latest annual net profit.
        """

        # Get latest annual operating_activity from cashflow
        cfo_query = """
            SELECT
                company_id,
                year,
                operating_activity
            FROM cashflow
        """
        cfo = pd.read_sql(cfo_query, self.connection)

        annual_mask = cfo["year"].astype(str).str.match(
            r"^[A-Za-z]{3}\s\d{4}$"
        )
        cfo = cfo[annual_mask].copy()

        cfo["fiscal_year"] = (
            cfo["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        cfo = cfo.sort_values(["company_id", "fiscal_year"])

        latest_cfo = (
            cfo
            .groupby("company_id", as_index=False)
            .tail(1)
            [["company_id", "fiscal_year", "operating_activity"]]
            .rename(
                columns={
                    "fiscal_year": "latest_fiscal_year",
                    "operating_activity": "latest_cfo",
                }
            )
        )

        # Get latest annual net_profit from profitandloss
        pat_query = """
            SELECT
                company_id,
                year,
                net_profit
            FROM profitandloss
        """
        pat = pd.read_sql(pat_query, self.connection)

        pat = pat[
            pat["year"].astype(str).str.match(
                r"^[A-Za-z]{3}\s\d{4}$"
            )
        ].copy()

        pat["fiscal_year"] = (
            pat["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        pat = pat.sort_values(["company_id", "fiscal_year"])

        latest_pat = (
            pat
            .groupby("company_id", as_index=False)
            .tail(1)
            [["company_id", "fiscal_year", "net_profit"]]
            .rename(
                columns={
                    "fiscal_year": "latest_fiscal_year",
                    "net_profit": "latest_pat",
                }
            )
        )

        # Merge CFO and PAT on company_id
        ratio = latest_cfo.merge(latest_pat, on="company_id", how="left")

        ratio["cfo_pat_ratio"] = None
        valid_mask = (ratio["latest_pat"] != 0) & ratio["latest_cfo"].notna() & ratio["latest_pat"].notna()
        ratio.loc[valid_mask, "cfo_pat_ratio"] = (
            ratio.loc[valid_mask, "latest_cfo"]
            / ratio.loc[valid_mask, "latest_pat"]
        )

        return df.merge(
            ratio[["company_id", "cfo_pat_ratio"]],
            on="company_id",
            how="left",
        )

    def compute_composite_scores(self, df):
        """
        Compute composite quality scores for the latest annual universe.

        Adds:
        - fcf_cagr_5yr (from financial_ratios.free_cash_flow_cr history)
        - cfo_pat_ratio (latest annual CFO / latest annual PAT)
        - fcf_positive_flag (1 if latest free_cash_flow_cr > 0 else 0)
        - composite_quality_score (0-100, sector-relative, P10/P90 winsorised)

        Persists composite_quality_score to financial_ratios table.
        """
        # 1. Add FCF CAGR 5yr
        df = self._add_fcf_cagr_5yr(df)

        # 2. Add CFO/PAT ratio
        df = self._add_cfo_pat_ratio(df)

        # 3. Add FCF positive flag
        df["fcf_positive_flag"] = (df["free_cash_flow_cr"] > 0).astype(int)

        # 4. Compute composite scores
        df = compute_composite_quality_score(df)

        # 5. Persist to database
        self._persist_composite_scores(df)

        logger.info(
            f"Composite scores computed. Range: "
            f"{df['composite_quality_score'].min():.1f} - "
            f"{df['composite_quality_score'].max():.1f}"
        )

        return df

    def _persist_composite_scores(self, df):
        """
        Write composite_quality_score back to financial_ratios
        for the latest annual record of each company.
        """
        # Get the latest annual year for each company from the current data
        update_data = df[["company_id", "year", "composite_quality_score"]].copy()
        update_data = update_data.dropna(subset=["composite_quality_score"])

        if update_data.empty:
            logger.warning("No composite scores to persist.")
            return

        cursor = self.connection.cursor()

        for _, row in update_data.iterrows():
            cursor.execute(
                """
                UPDATE financial_ratios
                SET composite_quality_score = ?
                WHERE company_id = ? AND year = ?
                """,
                (row["composite_quality_score"], row["company_id"], row["year"])
            )

        self.connection.commit()
        logger.info(f"Persisted composite scores for {len(update_data)} records.")
