import sqlite3
from pathlib import Path

import pandas as pd
from loguru import logger


class ValuationEngine:

    def __init__(
        self,
        db_path="db/nifty100.db",
        output_dir="output",
    ):
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)

        self.connection = None
        self.data = None
        self.valuation_summary = None

    # -----------------------------------------------------------
    # Database
    # -----------------------------------------------------------

    def connect(self):
        """Connect to SQLite database."""
        self.connection = sqlite3.connect(
            self.db_path
        )

        logger.info(
            f"Connected to database: {self.db_path}"
        )

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()

            logger.info(
                "Database connection closed."
            )

    # -----------------------------------------------------------
    # Load data
    # -----------------------------------------------------------

    def load_data(self):
        """
        Load latest market valuation data together
        with latest annual financial ratios and
        company / sector information.
        """

        market_query = """
        SELECT
            company_id,
            year,
            market_cap_cr,
            enterprise_value_cr,
            pe_ratio,
            pb_ratio,
            ev_ebitda
        FROM market_cap
        """

        market = pd.read_sql(
            market_query,
            self.connection,
        )

        if market.empty:
            raise ValueError(
                "No market_cap data available."
            )

        # Latest market-data year.
        market["year"] = pd.to_numeric(
            market["year"],
            errors="coerce",
        )

        latest_market_year = int(
            market["year"].max()
        )

        market = market[
            market["year"]
            == latest_market_year
        ].copy()

        logger.info(
            f"Using market valuation year "
            f"{latest_market_year}."
        )

        # -------------------------------------------------------
        # Financial ratios
        # -------------------------------------------------------

        ratios_query = """
        SELECT
            company_id,
            year,
            free_cash_flow_cr
        FROM financial_ratios
        """

        ratios = pd.read_sql(
            ratios_query,
            self.connection,
        )

        ratios = ratios[
            ratios["year"]
            .astype(str)
            .str.match(
                r"^[A-Za-z]{3}\s\d{4}$"
            )
        ].copy()

        if not ratios.empty:

            ratios["fiscal_year"] = (
                ratios["year"]
                .astype(str)
                .str.extract(
                    r"(\d{4})"
                )[0]
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
                .astype(str)
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

            ratios = (
                ratios
                .groupby(
                    "company_id",
                    as_index=False,
                )
                .tail(1)
                .copy()
            )

            ratios = ratios[
                [
                    "company_id",
                    "free_cash_flow_cr",
                ]
            ]

        # -------------------------------------------------------
        # Company master
        # -------------------------------------------------------

        companies_query = """
        SELECT
            id AS company_id,
            company_name
        FROM companies
        """

        companies = pd.read_sql(
            companies_query,
            self.connection,
        )

        # -------------------------------------------------------
        # Sector mapping
        # -------------------------------------------------------

        sectors_query = """
        SELECT
            company_id,
            sector
        FROM sectors
        """

        sectors = pd.read_sql(
            sectors_query,
            self.connection,
        )

        # -------------------------------------------------------
        # Merge
        # -------------------------------------------------------

        data = market.merge(
            companies,
            on="company_id",
            how="left",
        )

        data = data.merge(
            sectors,
            on="company_id",
            how="left",
        )

        data = data.merge(
            ratios,
            on="company_id",
            how="left",
        )

        self.data = data

        logger.info(
            f"Loaded valuation data for "
            f"{len(data)} companies."
        )

        return data

    # -----------------------------------------------------------
    # FCF Yield
    # -----------------------------------------------------------

    @staticmethod
    def compute_fcf_yield(df):
        """
        FCF Yield = FCF / Market Cap * 100.
        """

        market_cap = pd.to_numeric(
            df["market_cap_cr"],
            errors="coerce",
        )

        fcf = pd.to_numeric(
            df["free_cash_flow_cr"],
            errors="coerce",
        )

        df["fcf_yield_pct"] = (
            fcf
            .div(market_cap)
            .mul(100)
        )

        return df

    # -----------------------------------------------------------
    # Sector Median P/E
    # -----------------------------------------------------------

    @staticmethod
    def compute_sector_median_pe(df):
        """
        Compute latest-year median P/E for each sector.
        """

        sector_medians = (
            df.groupby("sector")[
                "pe_ratio"
            ]
            .median()
            .rename(
                "sector_median_pe"
            )
            .reset_index()
        )

        df = df.merge(
            sector_medians,
            on="sector",
            how="left",
        )

        return df

    # -----------------------------------------------------------
    # Historical 5-year Median P/E
    # -----------------------------------------------------------

    def compute_five_year_median_pe(self):
        """
        Compute the median P/E over the latest
        five available market-data years.
        """

        query = """
        SELECT
            company_id,
            year,
            pe_ratio
        FROM market_cap
        """

        historical = pd.read_sql(
            query,
            self.connection,
        )

        historical["year"] = pd.to_numeric(
            historical["year"],
            errors="coerce",
        )

        latest_year = int(
            historical["year"].max()
        )

        first_year = latest_year - 4

        historical = historical[
            historical["year"].between(
                first_year,
                latest_year,
            )
        ].copy()

        median_pe = (
            historical.groupby(
                "company_id"
            )["pe_ratio"]
            .median()
            .rename(
                "5yr_median_PE"
            )
            .reset_index()
        )

        return median_pe

    # -----------------------------------------------------------
    # Valuation flags
    # -----------------------------------------------------------

    @staticmethod
    def apply_valuation_flags(df):
        """
        Compare company P/E against sector median.

        > 1.5x sector median  -> Caution
        < 0.7x sector median  -> Discount
        otherwise              -> Fair
        """

        def classify(row):

            pe = row["pe_ratio"]
            sector_median = row[
                "sector_median_pe"
            ]

            if (
                pd.isna(pe)
                or pd.isna(sector_median)
                or sector_median <= 0
            ):
                return "Fair"

            if pe > sector_median * 1.5:
                return "Caution"

            if pe < sector_median * 0.7:
                return "Discount"

            return "Fair"

        df["flag"] = df.apply(
            classify,
            axis=1,
        )

        return df

    # -----------------------------------------------------------
    # P/E vs sector median
    # -----------------------------------------------------------

    @staticmethod
    def compute_pe_vs_sector(df):

        sector_median = pd.to_numeric(
            df["sector_median_pe"],
            errors="coerce",
        )

        pe = pd.to_numeric(
            df["pe_ratio"],
            errors="coerce",
        )

        df[
            "PE_vs_sector_median_pct"
        ] = (
            pe
            .div(sector_median)
            .sub(1)
            .mul(100)
        )

        return df

    # -----------------------------------------------------------
    # Build final output
    # -----------------------------------------------------------

    def build_summary(self):

        if self.data is None:
            self.load_data()

        df = self.data.copy()

        df = self.compute_fcf_yield(
            df
        )

        df = self.compute_sector_median_pe(
            df
        )

        median_pe = (
            self.compute_five_year_median_pe()
        )

        df = df.merge(
            median_pe,
            on="company_id",
            how="left",
        )

        df = self.compute_pe_vs_sector(
            df
        )

        df = self.apply_valuation_flags(
            df
        )

        # Required output columns.
        output = df[
            [
                "company_id",
                "company_name",
                "sector",
                "pe_ratio",
                "pb_ratio",
                "ev_ebitda",
                "fcf_yield_pct",
                "5yr_median_PE",
                "PE_vs_sector_median_pct",
                "flag",
            ]
        ].copy()

        output = output.rename(
            columns={
                "pe_ratio": "P/E",
                "pb_ratio": "P/B",
                "ev_ebitda": "EV/EBITDA",
            }
        )

        # Consistent ordering.
        output = output.sort_values(
            "company_id"
        ).reset_index(drop=True)

        self.valuation_summary = output

        return output

    # -----------------------------------------------------------
    # Export
    # -----------------------------------------------------------

    def export(self):

        if self.valuation_summary is None:
            self.build_summary()

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        excel_path = (
            self.output_dir
            / "valuation_summary.xlsx"
        )

        csv_path = (
            self.output_dir
            / "valuation_flags.csv"
        )

        self.valuation_summary.to_excel(
            excel_path,
            index=False,
        )

        flags = self.valuation_summary[
            self.valuation_summary["flag"].isin(
                [
                    "Caution",
                    "Discount",
                ]
            )
        ].copy()

        flags.to_csv(
            csv_path,
            index=False,
        )

        logger.info(
            f"Generated {excel_path}"
        )

        logger.info(
            f"Generated {csv_path}"
        )

        return (
            excel_path,
            csv_path,
        )

    # -----------------------------------------------------------
    # Complete pipeline
    # -----------------------------------------------------------

    def run(self):

        self.connect()

        try:

            self.load_data()

            summary = (
                self.build_summary()
            )

            self.export()

            return summary

        finally:

            self.close()


if __name__ == "__main__":

    engine = ValuationEngine()

    result = engine.run()

    print(
        "\nValuation summary:"
    )

    print(
        result.head(10).to_string(
            index=False
        )
    )

    print(
        f"\nTotal companies: {len(result)}"
    )

    print(
        "\nFlags:"
    )

    print(
        result["flag"]
        .value_counts()
        .to_string()
    )
