"""
N100 financial clustering.

Clusters all companies into five financial archetypes using:
- ROE
- Debt-to-equity
- Revenue CAGR (5Y)
- FCF CAGR (5Y)
- Operating profit margin
"""

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


DB_PATH = Path("db/nifty100.db")

ELBOW_PATH = Path(
    "reports/elbow_plot.png"
)

OUTPUT_PATH = Path(
    "output/cluster_labels.csv"
)


FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


def load_data():
    """Load latest annual ratios and company sectors."""

    with sqlite3.connect(DB_PATH) as conn:

        ratios = pd.read_sql(
            """
            SELECT *
            FROM financial_ratios
            """,
            conn,
        )

        sectors = pd.read_sql(
            """
            SELECT
                company_id,
                sector
            FROM sectors
            """,
            conn,
        )

    return ratios, sectors


def annual_only(ratios):
    """Keep annual financial ratio observations."""

    result = ratios.copy()

    result = result[
        ~result["year"]
        .astype(str)
        .str.upper()
        .eq("TTM")
    ]

    return result


def latest_annual(ratios):
    """Return the latest annual ratio row for each company."""

    annual = annual_only(ratios)

    annual["fiscal_year"] = pd.to_numeric(
        annual["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    annual = annual.dropna(
        subset=["fiscal_year"]
    )

    annual = annual.sort_values(
        ["company_id", "fiscal_year"]
    )

    return (
        annual
        .drop_duplicates(
            "company_id",
            keep="last",
        )
        .copy()
    )


def add_sector(
    data,
    sectors,
):
    """Attach sector information to each company."""

    sector_map = (
        sectors
        .drop_duplicates("company_id")
        .set_index("company_id")["sector"]
    )

    data["sector"] = (
        data["company_id"]
        .map(sector_map)
    )

    return data


def impute_sector_medians(data):
    """
    Impute missing feature values using the
    median for that feature within the company sector.

    Falls back to the global median if a sector has
    no usable value for a feature.
    """

    result = data.copy()

    for feature in FEATURES:

        sector_medians = (
            result
            .groupby("sector")[feature]
            .transform("median")
        )

        global_median = result[
            feature
        ].median()

        result[feature] = (
            result[feature]
            .fillna(sector_medians)
            .fillna(global_median)
        )

    return result


def add_fcf_cagr(data):
    """
    Calculate 5-year FCF CAGR from historical annual FCF.

    CAGR is calculated only when both the starting and
    ending FCF values are positive.
    """

    ratios, _ = load_data()

    annual = annual_only(ratios)

    annual["fiscal_year"] = pd.to_numeric(
        annual["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    annual = annual.dropna(
        subset=["fiscal_year"]
    )

    annual["free_cash_flow_cr"] = pd.to_numeric(
        annual["free_cash_flow_cr"],
        errors="coerce",
    )

    annual = annual.sort_values(
        ["company_id", "fiscal_year"]
    )

    fcf_cagr = {}

    for company_id, group in annual.groupby(
        "company_id"
    ):
        group = group.dropna(
            subset=["free_cash_flow_cr"]
        )

        if group.empty:
            fcf_cagr[company_id] = None
            continue

        latest_year = group["fiscal_year"].max()
        target_year = latest_year - 5

        latest_rows = group[
            group["fiscal_year"] == latest_year
        ]

        previous_rows = group[
            group["fiscal_year"] == target_year
        ]

        if (
            latest_rows.empty
            or previous_rows.empty
        ):
            fcf_cagr[company_id] = None
            continue

        latest_fcf = latest_rows.iloc[-1][
            "free_cash_flow_cr"
        ]

        previous_fcf = previous_rows.iloc[-1][
            "free_cash_flow_cr"
        ]

        if (
            pd.notna(previous_fcf)
            and pd.notna(latest_fcf)
            and previous_fcf > 0
            and latest_fcf > 0
        ):
            cagr = (
                (
                    latest_fcf
                    / previous_fcf
                )
                ** (1 / 5)
                - 1
            ) * 100

            fcf_cagr[company_id] = cagr

        else:
            fcf_cagr[company_id] = None

    data["fcf_cagr_5yr"] = (
        data["company_id"]
        .map(fcf_cagr)
    )

    return data


def prepare_features(
    data,
):
    """Prepare and scale clustering features."""

    data = impute_sector_medians(
        data
    )

    scaler = StandardScaler()

    scaled = scaler.fit_transform(
        data[FEATURES]
    )

    return (
        data,
        scaler,
        scaled,
    )


def generate_elbow_plot(
    scaled_features,
):
    """Generate the KMeans elbow plot for k=2 through 10."""

    inertias = []

    ks = range(2, 11)

    for k in ks:

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10,
        )

        model.fit(
            scaled_features
        )

        inertias.append(
            model.inertia_
        )

    ELBOW_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        list(ks),
        inertias,
        marker="o",
    )

    plt.xlabel(
        "Number of clusters (k)"
    )

    plt.ylabel(
        "Inertia"
    )

    plt.title(
        "KMeans Elbow Analysis"
    )

    plt.xticks(
        list(ks)
    )

    plt.tight_layout()

    plt.savefig(
        ELBOW_PATH,
        dpi=150,
    )

    plt.close()

    return inertias


def run_kmeans(
    scaled_features,
):
    """Run reproducible five-cluster KMeans."""

    model = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=10,
    )

    labels = model.fit_predict(
        scaled_features
    )

    return model, labels


def distance_from_centroid(
    model,
    scaled_features,
    labels,
):
    """Calculate each company's distance from its assigned centroid."""

    centroids = model.cluster_centers_

    distances = []

    for row, label in zip(
        scaled_features,
        labels,
    ):

        centroid = centroids[
            label
        ]

        distance = (
            (
                (row - centroid) ** 2
            ).sum()
            ** 0.5
        )

        distances.append(
            distance
        )

    return distances


def assign_cluster_names(
    data,
):
    """
    Assign temporary descriptive names based on
    cluster financial profiles.

    These names are intentionally deterministic and
    should be reviewed after inspecting cluster profiles.
    """

    profiles = (
        data
        .groupby("cluster_id")[FEATURES]
        .mean()
    )

    names = {}

    # Rank clusters using an overall financial-quality
    # score derived from the standardized profile.
    score = (
        profiles[
            [
                "return_on_equity_pct",
                "revenue_cagr_5yr",
                "fcf_cagr_5yr",
                "operating_profit_margin_pct",
            ]
        ]
        .rank(pct=True)
        .mean(axis=1)
        -
        profiles[
            "debt_to_equity"
        ].rank(
            pct=True
        )
    )

    ordered = (
        score
        .sort_values(
            ascending=False
        )
        .index
        .tolist()
    )

    default_names = [
        "High-Quality Compounders",
        "Emerging Growth",
        "Defensive / Balanced",
        "Value Cyclicals",
        "Distressed / Turnaround",
    ]

    for cluster_id, name in zip(
        ordered,
        default_names,
    ):
        names[cluster_id] = name

    return names


def generate():
    """Run the complete clustering pipeline."""

    ratios, sectors = load_data()

    data = latest_annual(
        ratios
    )

    data = add_sector(
        data,
        sectors,
    )

    data = add_fcf_cagr(
        data
    )

    # Preserve all companies represented in ratios.
    # The final acceptance gate requires 92 companies.
    print(
        f"Companies before imputation: "
        f"{data['company_id'].nunique()}"
    )

    data, scaler, scaled = (
        prepare_features(data)
    )

    print(
        "Missing feature values after "
        "sector-median imputation:"
    )

    print(
        data[FEATURES]
        .isna()
        .sum()
    )

    generate_elbow_plot(
        scaled
    )

    model, labels = run_kmeans(
        scaled
    )

    data["cluster_id"] = labels

    data["distance_from_centroid"] = (
        distance_from_centroid(
            model,
            scaled,
            labels,
        )
    )

    cluster_names = (
        assign_cluster_names(
            data
        )
    )

    data["cluster_name"] = (
        data["cluster_id"]
        .map(cluster_names)
    )

    output = data[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].copy()

    output[
        "distance_from_centroid"
    ] = output[
        "distance_from_centroid"
    ].round(6)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    return (
        output,
        data,
        model,
    )


if __name__ == "__main__":

    output, data, model = generate()

    print()
    print(
        "========================================"
    )
    print(
        "KMeans clustering complete"
    )
    print(
        "========================================"
    )

    print(
        f"Companies: "
        f"{len(output)}"
    )

    print(
        f"Clusters: "
        f"{output['cluster_id'].nunique()}"
    )

    print()
    print(
        "Cluster distribution:"
    )

    print(
        output[
            "cluster_name"
        ].value_counts()
    )

    print()
    print(
        f"Elbow plot: "
        f"{ELBOW_PATH}"
    )

    print(
        f"Labels: "
        f"{OUTPUT_PATH}"
    )
