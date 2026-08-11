import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger


class RadarChartEngine:

    METRIC_MAP = {
        "ROE": "roe",
        "ROCE": "roce",
        "NPM": "net_profit_margin",
        "D/E": "debt_to_equity",
        "FCF": "free_cash_flow",
        "PAT CAGR": "pat_cagr_5yr",
        "Revenue CAGR": "revenue_cagr_5yr",
    }

    def __init__(
        self,
        db_path="db/nifty100.db",
        output_dir="reports/radar_charts",
    ):
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.connection = None

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)

        logger.info(
            f"Connected to database: {self.db_path}"
        )

    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed.")

    def load_peer_data(self):
        """
        Load peer percentile data and composite score.
        """

        query = """
        SELECT
            pp.company_id,
            pp.peer_group_name,
            pp.metric,
            pp.percentile_rank,

            fr.composite_quality_score

        FROM peer_percentiles pp

        LEFT JOIN financial_ratios fr
            ON pp.company_id = fr.company_id
            AND pp.year = fr.year
        """

        df = pd.read_sql(
            query,
            self.connection,
        )

        return df

    def prepare_company_data(self, df, company_id):
        """
        Prepare the eight radar axes for one company.
        """

        company = df[
            df["company_id"] == company_id
        ].copy()

        if company.empty:
            return None

        peer_group = company[
            "peer_group_name"
        ].iloc[0]

        values = {}

        for axis, metric in self.METRIC_MAP.items():

            row = company[
                company["metric"] == metric
            ]

            if row.empty:
                values[axis] = 0.0
            else:
                values[axis] = (
                    row["percentile_rank"]
                    .iloc[0]
                )

        composite = company[
            "composite_quality_score"
        ].iloc[0]

        if pd.isna(composite):
            composite = 0.0

        values["Composite Score"] = (
            float(composite) / 100.0
        )

        return {
            "company_id": company_id,
            "peer_group_name": peer_group,
            "values": values,
        }

    def peer_average(self, df, peer_group, company_id):
        """
        Calculate peer-group average for each radar axis.
        """

        peer = df[
            df["peer_group_name"] == peer_group
        ].copy()

        averages = {}

        for axis, metric in self.METRIC_MAP.items():

            values = peer[
                peer["metric"] == metric
            ]["percentile_rank"]

            averages[axis] = (
                values.mean()
                if not values.empty
                else 0.0
            )

        # Composite score is not stored in peer_percentiles,
        # so calculate the peer average from financial_ratios.
        composite_query = """
        SELECT
            AVG(composite_quality_score) AS average_score
        FROM financial_ratios fr
        INNER JOIN peer_percentiles pp
            ON fr.company_id = pp.company_id
            AND fr.year = pp.year
        WHERE
            pp.peer_group_name = ?
        """

        composite = pd.read_sql(
            composite_query,
            self.connection,
            params=[peer_group],
        )

        average_score = composite[
            "average_score"
        ].iloc[0]

        averages["Composite Score"] = (
            float(average_score) / 100.0
            if pd.notna(average_score)
            else 0.0
        )

        return averages

    def create_chart(
        self,
        company_data,
        peer_average,
    ):
        """
        Create and save one radar chart.
        """

        company_id = company_data["company_id"]

        labels = list(
            company_data["values"].keys()
        )

        company_values = [
            company_data["values"][label]
            for label in labels
        ]

        peer_values = [
            peer_average[label]
            for label in labels
        ]

        num_axes = len(labels)

        angles = np.linspace(
            0,
            2 * np.pi,
            num_axes,
            endpoint=False,
        ).tolist()

        # Close both polygons.
        company_values += company_values[:1]
        peer_values += peer_values[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(
            figsize=(8, 8),
            subplot_kw={
                "polar": True
            },
        )

        ax.plot(
            angles,
            company_values,
            linewidth=2,
            label=company_id,
        )

        ax.fill(
            angles,
            company_values,
            alpha=0.20,
        )

        ax.plot(
            angles,
            peer_values,
            linestyle="--",
            linewidth=2,
            label="Peer Average",
        )

        ax.set_xticks(
            angles[:-1]
        )

        ax.set_xticklabels(
            labels,
            fontsize=10,
        )

        ax.set_ylim(
            0,
            1,
        )

        ax.set_yticks(
            [0.25, 0.50, 0.75, 1.00]
        )

        ax.set_yticklabels(
            ["25", "50", "75", "100"],
            fontsize=8,
        )

        ax.set_title(
            f"{company_id} — {company_data['peer_group_name']}",
            fontsize=13,
            pad=20,
        )

        ax.legend(
            loc="upper right",
            bbox_to_anchor=(1.25, 1.10),
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            self.output_dir
            / f"{company_id}_radar.png"
        )

        fig.savefig(
            output_path,
            dpi=150,
            bbox_inches="tight",
        )

        plt.close(fig)

        logger.info(
            f"Saved radar chart: {output_path}"
        )

        return output_path

    def generate_all(self):
        """
        Generate radar charts for all companies
        represented in peer_percentiles.
        """

        self.connect()

        try:
            df = self.load_peer_data()

            nifty100 = self.load_nifty100_data()

            assigned_companies = set(
                df["company_id"].dropna().unique()
            )

            all_companies = set(
                nifty100["company_id"].dropna().unique()
            )

            generated = []

            # -----------------------------------------
            # Companies with peer groups
            # -----------------------------------------

            for company_id in assigned_companies:

                company_data = self.prepare_company_data(
                    df,
                    company_id,
                )

                if company_data is None:
                    continue

                peer_avg = self.peer_average(
                    df,
                    company_data["peer_group_name"],
                    company_id,
                )

                path = self.create_chart(
                    company_data,
                    peer_avg,
                )

                generated.append(path)


            # -----------------------------------------
            # Companies without peer groups
            # -----------------------------------------

            unassigned = (
                all_companies - assigned_companies
            )

            nifty_average = self.nifty100_average(
                nifty100
            )

            for company_id in unassigned:

                company_data = (
                    self.unassigned_company_data(
                        nifty100,
                        company_id,
                    )
                )

                if company_data is None:
                    continue

                path = self.create_chart(
                    company_data,
                    nifty_average,
                )

                generated.append(path)

            logger.info(
                f"Generated {len(generated)} radar charts."
            )

            return generated

        finally:
            self.close()

    def load_nifty100_data(self):
        """
        Load latest annual financial data for the full Nifty 100
        universe for companies without a peer group.
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
            composite_quality_score
        FROM financial_ratios
        """

        df = pd.read_sql(
            query,
            self.connection,
        )

        df = df[
            df["year"].astype(str).str.match(
                r"^[A-Za-z]{3}\s\d{4}$"
            )
        ].copy()

        df["fiscal_year"] = (
            df["year"]
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        month_map = {
            "Jan": 1, "Feb": 2, "Mar": 3,
            "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9,
            "Oct": 10, "Nov": 11, "Dec": 12,
        }

        df["period_month"] = (
            df["year"]
            .str[:3]
            .map(month_map)
        )

        df = (
            df.sort_values(
                ["company_id", "fiscal_year", "period_month"]
            )
            .groupby("company_id", as_index=False)
            .tail(1)
            .reset_index(drop=True)
        )

        return df

    def unassigned_company_data(self, df, company_id):
        """
        Calculate global Nifty 100 percentile values for an
        unassigned company.
        """

        company = df[
            df["company_id"] == company_id
        ]

        if company.empty:
            return None

        company = company.iloc[0]

        values = {}

        for axis, column in {
            "ROE": "return_on_equity_pct",
            "ROCE": "return_on_capital_employed_pct",
            "NPM": "net_profit_margin_pct",
            "D/E": "debt_to_equity",
            "FCF": "free_cash_flow_cr",
            "PAT CAGR": "pat_cagr_5yr",
            "Revenue CAGR": "revenue_cagr_5yr",
        }.items():

            series = df[column]

            valid = series.notna()

            if not valid.any() or pd.isna(company[column]):
                values[axis] = 0.0
                continue

            ranks = series[valid].rank(
                method="min",
                ascending=True,
            )

            rank = ranks.loc[
                series[valid].index[
                    series[valid] == company[column]
                ]
            ].iloc[0]

            n = valid.sum()

            percentile = (
                (rank - 1) / (n - 1)
                if n > 1
                else 0.0
            )

            # Lower D/E is better.
            if axis == "D/E":
                percentile = 1 - percentile

            values[axis] = float(percentile)

        composite = company[
            "composite_quality_score"
        ]

        values["Composite Score"] = (
            float(composite) / 100
            if pd.notna(composite)
            else 0.0
        )

        return {
            "company_id": company_id,
            "peer_group_name": "Nifty 100 Average",
            "values": values,
        }

    def nifty100_average(self, df):
        """
        Calculate the Nifty 100 average radar profile.
        """

        averages = {}

        metric_columns = {
            "ROE": "return_on_equity_pct",
            "ROCE": "return_on_capital_employed_pct",
            "NPM": "net_profit_margin_pct",
            "D/E": "debt_to_equity",
            "FCF": "free_cash_flow_cr",
            "PAT CAGR": "pat_cagr_5yr",
            "Revenue CAGR": "revenue_cagr_5yr",
        }

        for axis, column in metric_columns.items():

            series = df[column]

            ranks = series.rank(
                method="min",
                ascending=True,
                pct=True,
            )

            percentile = ranks.mean()

            if axis == "D/E":
                percentile = 1 - percentile

            averages[axis] = float(percentile)

        averages["Composite Score"] = (
            df["composite_quality_score"].mean() / 100
        )

        return averages
