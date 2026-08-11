import sqlite3

import pandas as pd
import pytest

from src.analytics.peer import PeerEngine


@pytest.fixture
def engine():
    engine = PeerEngine(
        db_path="db/nifty100.db",
        peer_groups_path="data/raw/supporting/peer_groups.xlsx",
    )

    engine.connect()
    engine.load_peer_groups()
    engine.load_data()

    yield engine

    engine.close()


# ---------------------------------------------------------
# Peer-group loading
# ---------------------------------------------------------

def test_peer_groups_load(engine):
    assert engine.peer_groups is not None
    assert len(engine.peer_groups) == 56

    assert (
        engine.peer_groups["peer_group_name"].nunique()
        == 11
    )


def test_all_peer_groups_have_companies(engine):
    counts = (
        engine.peer_groups
        .groupby("peer_group_name")
        .size()
    )

    assert (counts > 0).all()


# ---------------------------------------------------------
# Metric configuration
# ---------------------------------------------------------

def test_ten_metrics_configured(engine):
    assert len(engine.METRICS) == 10


def test_required_metrics_present(engine):
    expected = {
        "roe",
        "roce",
        "net_profit_margin",
        "debt_to_equity",
        "free_cash_flow",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "eps_cagr_5yr",
        "interest_coverage",
        "asset_turnover",
    }

    assert set(engine.METRICS.keys()) == expected


# ---------------------------------------------------------
# Percentile calculation
# ---------------------------------------------------------

def test_percentiles_have_expected_row_count(engine):
    result = engine.compute_percentiles()

    assert len(result) == 560


def test_percentile_range(engine):
    result = engine.compute_percentiles()

    valid = result["percentile_rank"].dropna()

    assert (valid >= 0).all()
    assert (valid <= 1).all()


def test_all_metrics_present(engine):
    result = engine.compute_percentiles()

    assert result["metric"].nunique() == 10


def test_all_peer_groups_present(engine):
    result = engine.compute_percentiles()

    assert (
        result["peer_group_name"].nunique()
        == 11
    )


# ---------------------------------------------------------
# D/E inverse ranking
# ---------------------------------------------------------

def test_debt_to_equity_is_inverse_ranked(engine):
    result = engine.compute_percentiles()

    de = result[
        result["metric"] == "debt_to_equity"
    ].copy()

    for group in de["peer_group_name"].unique():

        group_data = de[
            de["peer_group_name"] == group
        ].dropna(subset=["value"])

        if len(group_data) < 2:
            continue

        lowest = group_data.loc[
            group_data["value"].idxmin()
        ]

        highest = group_data.loc[
            group_data["value"].idxmax()
        ]

        assert (
            lowest["percentile_rank"]
            >= highest["percentile_rank"]
        )


# ---------------------------------------------------------
# Database persistence
# ---------------------------------------------------------

def test_peer_percentiles_table_exists(engine):
    result = engine.compute_percentiles()

    engine.save_to_database(result)

    tables = pd.read_sql(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'peer_percentiles'
        """,
        engine.connection,
    )

    assert len(tables) == 1


def test_peer_percentiles_row_count(engine):
    result = engine.compute_percentiles()

    engine.save_to_database(result)

    count = pd.read_sql(
        """
        SELECT COUNT(*) AS count
        FROM peer_percentiles
        """,
        engine.connection,
    ).iloc[0, 0]

    assert count == 560


# ---------------------------------------------------------
# Required schema
# ---------------------------------------------------------

def test_peer_percentiles_schema(engine):
    result = engine.compute_percentiles()

    engine.save_to_database(result)

    schema = pd.read_sql(
        """
        PRAGMA table_info(peer_percentiles)
        """,
        engine.connection,
    )

    columns = set(schema["name"])

    expected = {
        "company_id",
        "peer_group_name",
        "metric",
        "value",
        "percentile_rank",
        "year",
    }

    assert expected.issubset(columns)
