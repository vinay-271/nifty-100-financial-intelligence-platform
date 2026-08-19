import re
from pathlib import Path
import sqlite3

import pandas as pd
from loguru import logger

DB_PATH = Path("db/nifty100.db")
VALIDATION_PATH = Path("output/cagr_validation.csv")


INPUT_PATH = Path("data/raw/core/analysis.xlsx")
OUTPUT_PATH = Path("output/analysis_parsed.csv")
FAILURE_PATH = Path("output/parse_failures.csv")


TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]

PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*([\d.]+)%"
)


def parse_metric(value):
    """
    Parse values such as:

        10 Years: 21%
        5 Years: 24%
        3 Years: 17%

    Returns:
        (period_years, value_pct)

    Returns (None, None) when the value does not
    match the required pattern.
    """

    if pd.isna(value):
        return None, None

    text = str(value).strip()

    match = PATTERN.search(text)

    if not match:
        return None, None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


def run_parser():
    """Parse analysis.xlsx and generate structured CSV outputs."""

    logger.info(
        f"Reading analysis workbook: {INPUT_PATH}"
    )

    # The workbook contains a title row above the actual header.
    df = pd.read_excel(
        INPUT_PATH,
        header=1,
    )

    required_columns = [
        "company_id",
        *TARGET_FIELDS,
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    parsed_records = []
    failures = []

    for _, row in df.iterrows():

        company_id = row["company_id"]

        for metric_type in TARGET_FIELDS:

            raw_value = row[metric_type]

            period_years, value_pct = parse_metric(
                raw_value
            )

            if period_years is None:
                failures.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "raw_value": raw_value,
                    }
                )
                continue

            parsed_records.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": period_years,
                    "value_pct": value_pct,
                }
            )

    parsed_df = pd.DataFrame(
        parsed_records,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failure_df = pd.DataFrame(
        failures,
        columns=[
            "company_id",
            "metric_type",
            "raw_value",
        ],
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    parsed_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    failure_df.to_csv(
        FAILURE_PATH,
        index=False,
    )

    logger.info(
        f"Parsed records: {len(parsed_df)}"
    )

    logger.info(
        f"Parse failures: {len(failure_df)}"
    )

    logger.info(
        f"Saved parsed output: {OUTPUT_PATH}"
    )

    logger.info(
        f"Saved failures: {FAILURE_PATH}"
    )

    logger.info(
        f"Saved failures: {FAILURE_PATH}"
    )

    validate_cagrs(parsed_df)

    return parsed_df, failure_df

def validate_cagrs(parsed_df):
    """
    Cross-validate parsed 5-year CAGR values against the
    5-year CAGR values stored by the Ratio Engine.

    Divergence is calculated as relative percentage difference:

        abs(parsed - computed) / abs(computed) * 100

    Values with divergence > 5% are flagged for manual review.
    """

    five_year = parsed_df[
        parsed_df["period_years"] == 5
    ].copy()

    if five_year.empty:
        logger.warning(
            "No 5-year CAGR records available for validation."
        )
        return pd.DataFrame()

    metric_mapping = {
        "compounded_sales_growth": "revenue_cagr_5yr",
        "compounded_profit_growth": "pat_cagr_5yr",
    }

    validation_records = []

    with sqlite3.connect(DB_PATH) as conn:

        ratio_df = pd.read_sql(
            """
            SELECT
                company_id,
                year,
                revenue_cagr_5yr,
                pat_cagr_5yr
            FROM financial_ratios
            """,
            conn,
        )

    # Keep annual records only.
    ratio_df = ratio_df[
        ratio_df["year"]
        .astype(str)
        .str.match(r"^[A-Za-z]{3}\s\d{4}$")
    ].copy()

    for _, row in five_year.iterrows():

        metric_type = row["metric_type"]

        if metric_type not in metric_mapping:
            continue

        computed_column = metric_mapping[
            metric_type
        ]

        company_rows = ratio_df[
            ratio_df["company_id"]
            == row["company_id"]
        ]

        if company_rows.empty:

            validation_records.append(
                {
                    "company_id": row["company_id"],
                    "metric_type": metric_type,
                    "parsed_value_pct": row["value_pct"],
                    "computed_value_pct": None,
                    "divergence_pct": None,
                    "review_required": True,
                    "reason": (
                        "Company not found "
                        "in financial_ratios"
                    ),
                }
            )

            continue

        # Use the latest annual value with a valid
        # computed 5-year CAGR.
        company_rows = company_rows[
            company_rows[computed_column].notna()
        ].copy()

        if company_rows.empty:

            validation_records.append(
                {
                    "company_id": row["company_id"],
                    "metric_type": metric_type,
                    "parsed_value_pct": row["value_pct"],
                    "computed_value_pct": None,
                    "divergence_pct": None,
                    "review_required": True,
                    "reason": (
                        "Computed CAGR unavailable"
                    ),
                }
            )

            continue

        # Extract fiscal year and select latest annual observation.
        company_rows["fiscal_year"] = (
            company_rows["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        latest = company_rows.loc[
            company_rows["fiscal_year"].idxmax()
        ]

        computed_value = float(
            latest[computed_column]
        )

        parsed_value = float(
            row["value_pct"]
        )

        if computed_value == 0:

            divergence = (
                0.0
                if parsed_value == 0
                else float("inf")
            )

        else:

            divergence = (
                abs(
                    parsed_value
                    - computed_value
                )
                / abs(computed_value)
                * 100
            )

        review_required = (
            divergence > 5.0
        )

        validation_records.append(
            {
                "company_id": row["company_id"],
                "metric_type": metric_type,
                "parsed_value_pct": parsed_value,
                "computed_value_pct": computed_value,
                "divergence_pct": round(
                    divergence,
                    2,
                ),
                "review_required": review_required,
                "reason": (
                    "Divergence > 5%"
                    if review_required
                    else "OK"
                ),
            }
        )

    validation_df = pd.DataFrame(
        validation_records
    )

    validation_df.to_csv(
        VALIDATION_PATH,
        index=False,
    )

    logger.info(
        f"CAGR validation records: "
        f"{len(validation_df)}"
    )

    logger.info(
        f"Manual reviews required: "
        f"{validation_df['review_required'].sum()}"
    )

    return validation_df

if __name__ == "__main__":
    run_parser()
