"""
Capital Allocation Report
Sprint 5 - Day 32

Consumes the historical capital allocation output generated
by RatioEngine and produces:
    - Latest-year pattern distribution
    - Year-over-year pattern changes
"""

from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/output/capital_allocation.csv")
OUTPUT_DIR = Path("output")

DISTRIBUTION_PATH = OUTPUT_DIR / "capital_allocation_distribution.csv"
CHANGES_PATH = OUTPUT_DIR / "pattern_changes.csv"


def extract_fiscal_year(value):
    """Extract numeric fiscal year from strings such as Mar 2024 or Sep 2024."""
    if pd.isna(value):
        return None

    match = pd.Series([str(value)]).str.extract(r"(\d{4})")[0].iloc[0]

    if pd.isna(match):
        return None

    return int(match)


def load_capital_allocation():
    """Load and validate the historical capital allocation dataset."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Capital allocation file not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = {
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df = df.copy()

    df["fiscal_year"] = df["year"].apply(
        extract_fiscal_year
    )

    df = df.dropna(
        subset=["company_id", "fiscal_year"]
    )

    df["fiscal_year"] = df["fiscal_year"].astype(int)

    return df


def latest_records(df):
    """Return the latest capital allocation record for each company."""

    return (
        df.sort_values(
            ["company_id", "fiscal_year"]
        )
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )


def generate_distribution(df):
    """Generate latest-year capital allocation distribution."""

    latest = latest_records(df)

    distribution = (
        latest["pattern_label"]
        .value_counts()
        .rename_axis("pattern_label")
        .reset_index(name="company_count")
    )

    distribution["percentage"] = (
        distribution["company_count"]
        / len(latest)
        * 100
    ).round(2)

    distribution = distribution.sort_values(
        "company_count",
        ascending=False,
    ).reset_index(drop=True)

    return distribution


def generate_pattern_changes(df):
    """
    Compare the latest two capital allocation records
    for every company.

    Only actual pattern changes are included.
    """

    df = df.sort_values(
        ["company_id", "fiscal_year"]
    ).copy()

    df["previous_pattern"] = (
        df.groupby("company_id")["pattern_label"]
        .shift(1)
    )

    df["previous_year"] = (
        df.groupby("company_id")["year"]
        .shift(1)
    )

    latest = (
        df.groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    changes = latest[
        latest["previous_pattern"].notna()
        & (
            latest["previous_pattern"]
            != latest["pattern_label"]
        )
    ].copy()

    changes = changes.rename(
        columns={
            "year": "latest_year",
            "pattern_label": "latest_pattern",
        }
    )

    changes = changes[
        [
            "company_id",
            "previous_year",
            "previous_pattern",
            "latest_year",
            "latest_pattern",
        ]
    ]

    return changes.sort_values(
        "company_id"
    ).reset_index(drop=True)


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_capital_allocation()

    print(
        f"Loaded {len(df)} capital allocation records."
    )

    print(
        f"Companies represented: "
        f"{df['company_id'].nunique()}"
    )

    # ---------------------------------------------
    # Latest-year distribution
    # ---------------------------------------------

    distribution = generate_distribution(df)

    distribution.to_csv(
        DISTRIBUTION_PATH,
        index=False,
    )

    print()
    print("Latest-year distribution:")
    print(
        distribution.to_string(index=False)
    )

    print()
    print(
        f"Distribution output: "
        f"{DISTRIBUTION_PATH}"
    )

    # ---------------------------------------------
    # Pattern changes
    # ---------------------------------------------

    changes = generate_pattern_changes(df)

    changes.to_csv(
        CHANGES_PATH,
        index=False,
    )

    print()
    print(
        f"Pattern changes detected: "
        f"{len(changes)}"
    )

    print(
        f"Pattern changes output: "
        f"{CHANGES_PATH}"
    )

    # ---------------------------------------------
    # Validation
    # ---------------------------------------------

    print()

    latest = latest_records(df)

    print(
        f"Latest records: "
        f"{len(latest)}"
    )

    print(
        f"Companies without capital allocation history: "
        f"{92 - len(latest)}"
    )

    if len(latest) != 91:
        raise SystemExit(
            "Unexpected latest company count."
        )

    print()
    print("Day 32 capital allocation report complete.")


if __name__ == "__main__":
    main()
