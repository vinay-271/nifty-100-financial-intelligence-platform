import sqlite3
from pathlib import Path

import pandas as pd
from loguru import logger


class PeerEngine:

    METRICS = {
        "roe": "return_on_equity_pct",
        "roce": "return_on_capital_employed_pct",
        "net_profit_margin": "net_profit_margin_pct",
        "debt_to_equity": "debt_to_equity",
        "free_cash_flow": "free_cash_flow_cr",
        "pat_cagr_5yr": "pat_cagr_5yr",
        "revenue_cagr_5yr": "revenue_cagr_5yr",
        "eps_cagr_5yr": "eps_cagr_5yr",
        "interest_coverage": "interest_coverage",
        "asset_turnover": "asset_turnover",
    }

    def __init__(
        self,
        db_path="db/nifty100.db",
        peer_groups_path="data/raw/supporting/peer_groups.xlsx",
    ):
        self.db_path = Path(db_path)
        self.peer_groups_path = Path(peer_groups_path)

        self.connection = None
        self.peer_groups = None
        self.data = None

    def connect(self):
        """Connect to SQLite database."""
        self.connection = sqlite3.connect(self.db_path)

        logger.info(
            f"Connected to database: {self.db_path}"
        )

    def close(self):
        """Close SQLite connection."""
        if self.connection:
            self.connection.close()

            logger.info(
                "Database connection closed."
            )

    def load_peer_groups(self):
        """
        Load authoritative peer-group mapping from
        peer_groups.xlsx.
        """

        self.peer_groups = pd.read_excel(
            self.peer_groups_path
        )

        required = {
            "company_id",
            "peer_group_name",
            "is_benchmark",
        }

        missing = required - set(
            self.peer_groups.columns
        )

        if missing:
            raise ValueError(
                f"Missing peer-group columns: {missing}"
            )

        self.peer_groups = self.peer_groups[
            [
                "company_id",
                "peer_group_name",
                "is_benchmark",
            ]
        ].copy()

        logger.info(
            f"Loaded {len(self.peer_groups)} peer assignments "
            f"across {self.peer_groups['peer_group_name'].nunique()} groups."
        )

        return self.peer_groups

    def load_data(self):
        """
        Load the latest annual financial ratio record
        for every company.
        """

        query = """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            return_on_capital_employed_pct,
            net_profit_margin_pct,
            debt_to_equity,
            free_cash_flow_cr,
            pat_cagr_5yr,
            revenue_cagr_5yr,
            eps_cagr_5yr,
            interest_coverage,
            asset_turnover
        FROM financial_ratios
        """

        ratios = pd.read_sql(
            query,
            self.connection,
        )

        # Keep standard annual periods only.
        ratios = ratios[
            ratios["year"].astype(str).str.match(
                r"^[A-Za-z]{3}\s\d{4}$"
            )
        ].copy()

        ratios["fiscal_year"] = (
            ratios["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

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

        ratios["period_month"] = (
            ratios["year"]
            .str[:3]
            .map(month_map)
        )

        ratios = ratios.sort_values(
            [
                "company_id",
                "fiscal_year",
                "period_month",
            ]
        )

        # Use latest complete annual observation.
        self.data = (
            ratios
            .groupby("company_id", as_index=False)
            .tail(1)
            .drop(
                columns=[
                    "fiscal_year",
                    "period_month",
                ]
            )
            .reset_index(drop=True)
        )

        logger.info(
            f"Loaded latest annual ratios for "
            f"{len(self.data)} companies."
        )

        return self.data

    @staticmethod
    def _percent_rank(series):
        """
        SQL-compatible PERCENT_RANK:

            (rank - 1) / (n - 1)

        Ties receive the same rank.
        """

        result = pd.Series(
            index=series.index,
            dtype="float64",
        )

        valid = series.notna()

        if valid.sum() == 0:
            return result

        if valid.sum() == 1:
            result.loc[valid] = 0.0
            return result

        ranks = (
            series.loc[valid]
            .rank(
                method="min",
                ascending=True,
            )
        )

        result.loc[valid] = (
            (ranks - 1)
            / (valid.sum() - 1)
        )

        return result

    def compute_percentiles(self):
        """
        Compute percentile rankings for all peer groups
        and all configured metrics.
        """

        if self.peer_groups is None:
            self.load_peer_groups()

        if self.data is None:
            self.load_data()

        df = self.peer_groups.merge(
            self.data,
            on="company_id",
            how="left",
        )

        results = []

        for metric_name, column in self.METRICS.items():

            working = df[
                [
                    "company_id",
                    "peer_group_name",
                    "year",
                    column,
                ]
            ].copy()

            working = working.rename(
                columns={
                    column: "value"
                }
            )

            # Rank within each peer group.
            working["percentile_rank"] = (
                working
                .groupby("peer_group_name")["value"]
                .transform(
                    self._percent_rank
                )
            )

            # D/E: lower is better.
            if metric_name == "debt_to_equity":
                working["percentile_rank"] = (
                    1
                    - working["percentile_rank"]
                )

            working["metric"] = metric_name

            results.append(
                working[
                    [
                        "company_id",
                        "peer_group_name",
                        "metric",
                        "value",
                        "percentile_rank",
                        "year",
                    ]
                ]
            )

        result = pd.concat(
            results,
            ignore_index=True,
        )

        logger.info(
            f"Computed {len(result)} peer percentile records."
        )

        return result

    def save_to_database(self, percentiles):
        """
        Replace peer_percentiles table with the
        newly computed rankings.
        """

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS peer_percentiles (
                id INTEGER PRIMARY KEY,
                company_id TEXT NOT NULL,
                peer_group_name TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL,
                percentile_rank REAL,
                year TEXT
            )
            """
        )

        self.connection.execute(
            "DELETE FROM peer_percentiles"
        )

        percentiles.to_sql(
            "peer_percentiles",
            self.connection,
            if_exists="append",
            index=False,
        )

        self.connection.commit()

        logger.info(
            f"Saved {len(percentiles)} records "
            f"to peer_percentiles."
        )

    def run(self):
        """Run the complete peer percentile pipeline."""

        self.connect()

        try:
            self.load_peer_groups()
            self.load_data()

            percentiles = (
                self.compute_percentiles()
            )

            self.save_to_database(
                percentiles
            )

            return percentiles

        finally:
            self.close()
