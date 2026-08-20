"""
Day 37 — Cluster Profiling & Statistics

Analyzes the fixed KMeans assignments produced by
src.analytics.clustering.

Does NOT rerun KMeans.
"""

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


DB_PATH = Path("db/nifty100.db")

CLUSTER_PATH = Path(
    "output/cluster_labels.csv"
)

PROFILE_PATH = Path(
    "output/cluster_profiles.csv"
)

OUTLIER_PATH = Path(
    "output/cluster_outliers.csv"
)

PORTFOLIO_PATH = Path(
    "output/portfolio_statistics.csv"
)

HEATMAP_PATH = Path(
    "reports/cluster_correlation_heatmap.png"
)


FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


FEATURE_LABELS = {
    "return_on_equity_pct": "ROE",
    "debt_to_equity": "D/E",
    "revenue_cagr_5yr": "Revenue CAGR 5Y",
    "fcf_cagr_5yr": "FCF CAGR 5Y",
    "operating_profit_margin_pct": "OPM",
}


def load_cluster_labels():
    """Load the fixed Day 36 cluster assignments."""

    return pd.read_csv(
        CLUSTER_PATH
    )


def load_latest_ratios():
    """Load latest annual financial ratios."""

    with sqlite3.connect(DB_PATH) as conn:

        ratios = pd.read_sql(
            """
            SELECT *
            FROM financial_ratios
            """,
            conn,
        )

    ratios = ratios[
        ~ratios["year"]
        .astype(str)
        .str.upper()
        .eq("TTM")
    ].copy()

    ratios["fiscal_year"] = pd.to_numeric(
        ratios["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    ratios = ratios.dropna(
        subset=["fiscal_year"]
    )

    ratios = ratios.sort_values(
        ["company_id", "fiscal_year"]
    )

    return (
        ratios
        .drop_duplicates(
            "company_id",
            keep="last",
        )
        .copy()
    )


def calculate_fcf_cagr():
    """
    Reproduce the Day 36 FCF CAGR definition.

    CAGR is calculated only when both the starting
    and ending FCF are positive.
    """

    with sqlite3.connect(DB_PATH) as conn:

        ratios = pd.read_sql(
            """
            SELECT
                company_id,
                year,
                free_cash_flow_cr
            FROM financial_ratios
            """,
            conn,
        )

    ratios = ratios[
        ~ratios["year"]
        .astype(str)
        .str.upper()
        .eq("TTM")
    ].copy()

    ratios["fiscal_year"] = pd.to_numeric(
        ratios["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    ratios["free_cash_flow_cr"] = pd.to_numeric(
        ratios["free_cash_flow_cr"],
        errors="coerce",
    )

    ratios = ratios.dropna(
        subset=["fiscal_year"]
    )

    ratios = ratios.sort_values(
        ["company_id", "fiscal_year"]
    )

    results = []

    for company_id, group in ratios.groupby(
        "company_id"
    ):

        group = group.dropna(
            subset=["free_cash_flow_cr"]
        )

        if group.empty:
            results.append(
                {
                    "company_id": company_id,
                    "fcf_cagr_5yr": None,
                }
            )
            continue

        latest_year = int(
            group["fiscal_year"].max()
        )

        start_year = latest_year - 5

        latest = group[
            group["fiscal_year"]
            == latest_year
        ]

        previous = group[
            group["fiscal_year"]
            == start_year
        ]

        if (
            latest.empty
            or previous.empty
        ):
            results.append(
                {
                    "company_id": company_id,
                    "fcf_cagr_5yr": None,
                }
            )
            continue

        latest_fcf = latest.iloc[-1][
            "free_cash_flow_cr"
        ]

        previous_fcf = previous.iloc[-1][
            "free_cash_flow_cr"
        ]

        if (
            pd.notna(latest_fcf)
            and pd.notna(previous_fcf)
            and latest_fcf > 0
            and previous_fcf > 0
        ):

            cagr = (
                (
                    latest_fcf
                    / previous_fcf
                )
                ** (1 / 5)
                - 1
            ) * 100

        else:
            cagr = None

        results.append(
            {
                "company_id": company_id,
                "fcf_cagr_5yr": cagr,
            }
        )

    return pd.DataFrame(
        results
    )


def prepare_data():
    """Combine cluster labels with latest financial metrics."""

    labels = load_cluster_labels()

    ratios = load_latest_ratios()

    fcf = calculate_fcf_cagr()

    data = labels.merge(
        ratios[
            [
                "company_id",
                *[
                    feature
                    for feature in FEATURES
                    if feature != "fcf_cagr_5yr"
                ],
            ]
        ],
        on="company_id",
        how="left",
    )

    data = data.merge(
        fcf,
        on="company_id",
        how="left",
    )

    # Reproduce Day 36 sector-median imputation.
    with sqlite3.connect(DB_PATH) as conn:

        sectors = pd.read_sql(
            """
            SELECT
                company_id,
                sector
            FROM sectors
            """,
            conn,
        )

    data = data.merge(
        sectors.drop_duplicates(
            "company_id"
        ),
        on="company_id",
        how="left",
    )

    for feature in FEATURES:

        sector_median = (
            data
            .groupby("sector")[feature]
            .transform("median")
        )

        global_median = data[
            feature
        ].median()

        data[feature] = (
            data[feature]
            .fillna(sector_median)
            .fillna(global_median)
        )

    return data


def profile_clusters(data):
    """Generate mean/median cluster profiles."""

    rows = []

    for cluster_id, group in data.groupby(
        "cluster_id"
    ):

        row = {
            "cluster_id": cluster_id,
            "company_count": len(group),
        }

        for feature in FEATURES:

            row[
                f"{feature}_mean"
            ] = group[
                feature
            ].mean()

            row[
                f"{feature}_median"
            ] = group[
                feature
            ].median()

            row[
                f"{feature}_min"
            ] = group[
                feature
            ].min()

            row[
                f"{feature}_max"
            ] = group[
                feature
            ].max()

        rows.append(row)

    return pd.DataFrame(
        rows
    ).sort_values(
        "cluster_id"
    )


def generate_cluster_names(profiles):
    """
    Assign descriptive names based on observed
    cluster financial characteristics.
    """

    names = {}

    for _, row in profiles.iterrows():

        cluster_id = int(
            row["cluster_id"]
        )

        roe = row[
            "return_on_equity_pct_mean"
        ]

        de = row[
            "debt_to_equity_mean"
        ]

        revenue = row[
            "revenue_cagr_5yr_mean"
        ]

        fcf = row[
            "fcf_cagr_5yr_mean"
        ]

        opm = row[
            "operating_profit_margin_pct_mean"
        ]

        # Extreme ROE cluster
        if roe > 1000:
            name = (
                "Extreme-ROE Businesses"
            )

        # Exceptional growth / base-effect cluster
        elif revenue > 1000:
            name = (
                "Exceptional Growth / Base Effect"
            )

        # Highly leveraged cluster
        elif de >= 3:
            name = (
                "Highly Leveraged"
            )

        # High-margin + strong FCF growth
        elif (
            opm >= 50
            and de < 1
            and fcf > 10
        ):
            name = (
                "High-Margin Growth"
            )

        # Remaining central cluster
        else:
            name = (
                "Core / Balanced Businesses"
            )

        names[cluster_id] = name

    return names

def add_cluster_names(
    data,
    profiles,
):
    """Attach descriptive names to the cluster assignments."""

    names = generate_cluster_names(
        profiles
    )

    data["cluster_name"] = (
        data["cluster_id"]
        .map(names)
    )

    return data, names


def generate_outlier_report(
    data
):
    """
    Identify extreme observations using the IQR method.

    An observation is flagged when any clustering feature
    lies outside Q1 - 1.5*IQR or Q3 + 1.5*IQR.
    """

    rows = []

    for feature in FEATURES:

        q1 = data[
            feature
        ].quantile(0.25)

        q3 = data[
            feature
        ].quantile(0.75)

        iqr = q3 - q1

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        mask = (
            (data[feature] < lower)
            | (data[feature] > upper)
        )

        for _, row in data[
            mask
        ].iterrows():

            rows.append(
                {
                    "company_id": row[
                        "company_id"
                    ],
                    "cluster_id": row[
                        "cluster_id"
                    ],
                    "feature": FEATURE_LABELS[
                        feature
                    ],
                    "value": row[
                        feature
                    ],
                    "lower_bound": lower,
                    "upper_bound": upper,
                }
            )

    return pd.DataFrame(
        rows
    )


def generate_correlation_heatmap(
    data
):
    """Generate correlation heatmap of clustering features."""

    matrix = data[
        FEATURES
    ].rename(
        columns=FEATURE_LABELS
    ).corr()

    HEATMAP_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(9, 7)
    )

    sns.heatmap(
        matrix,
        annot=True,
        fmt=".2f",
        square=True,
        linewidths=0.5,
    )

    plt.title(
        "N100 Financial Feature Correlation"
    )

    plt.tight_layout()

    plt.savefig(
        HEATMAP_PATH,
        dpi=150,
    )

    plt.close()


def generate_portfolio_statistics(
    data
):
    """Generate overall portfolio-level statistics."""

    rows = []

    for feature in FEATURES:

        values = data[
            feature
        ]

        rows.append(
            {
                "metric": FEATURE_LABELS[
                    feature
                ],
                "mean": values.mean(),
                "median": values.median(),
                "minimum": values.min(),
                "maximum": values.max(),
                "std_dev": values.std(),
            }
        )

    return pd.DataFrame(
        rows
    )


def save_outputs(
    data,
    profiles,
    outliers,
    portfolio_stats,
):
    """Write all Day 37 outputs."""

    OUTPUT_PATHS = [
        PROFILE_PATH,
        OUTLIER_PATH,
        PORTFOLIO_PATH,
    ]

    for path in OUTPUT_PATHS:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    profiles.to_csv(
        PROFILE_PATH,
        index=False,
    )

    outliers.to_csv(
        OUTLIER_PATH,
        index=False,
    )

    portfolio_stats.to_csv(
        PORTFOLIO_PATH,
        index=False,
    )

    # Update cluster labels with final descriptive names.
    data[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].to_csv(
        CLUSTER_PATH,
        index=False,
    )


def generate():
    """Run the complete Day 37 analysis."""

    data = prepare_data()

    print(
        f"Companies analyzed: "
        f"{data['company_id'].nunique()}"
    )

    profiles = profile_clusters(
        data
    )

    data, names = add_cluster_names(
        data,
        profiles,
    )

    outliers = generate_outlier_report(
        data
    )

    generate_correlation_heatmap(
        data
    )

    portfolio_stats = (
        generate_portfolio_statistics(
            data
        )
    )

    save_outputs(
        data,
        profiles,
        outliers,
        portfolio_stats,
    )

    return (
        data,
        profiles,
        outliers,
        portfolio_stats,
    )


if __name__ == "__main__":

    (
        data,
        profiles,
        outliers,
        portfolio_stats,
    ) = generate()

    print()
    print(
        "========================================"
    )
    print(
        "Day 37 cluster analysis complete"
    )
    print(
        "========================================"
    )

    print()
    print(
        "Cluster distribution:"
    )

    print(
        data[
            [
                "cluster_id",
                "cluster_name",
            ]
        ]
        .drop_duplicates()
        .merge(
            data.groupby(
                "cluster_id"
            ).size().rename(
                "company_count"
            ),
            on="cluster_id",
        )
        .sort_values(
            "cluster_id"
        )
        .to_string(
            index=False
        )
    )

    print()
    print(
        "Outlier observations:",
        len(outliers),
    )

    print()
    print(
        f"Profile: {PROFILE_PATH}"
    )

    print(
        f"Outliers: {OUTLIER_PATH}"
    )

    print(
        f"Portfolio statistics: "
        f"{PORTFOLIO_PATH}"
    )

    print(
        f"Heatmap: {HEATMAP_PATH}"
    )
