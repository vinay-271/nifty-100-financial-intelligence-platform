import sqlite3

import pandas as pd
import pytest

from src.analytics.radar import RadarChartEngine


@pytest.fixture
def engine(tmp_path):
    engine = RadarChartEngine(
        db_path="db/nifty100.db",
        output_dir=tmp_path / "radar_charts",
    )

    engine.connect()

    yield engine

    engine.close()


def test_load_peer_data(engine):
    df = engine.load_peer_data()

    assert not df.empty
    assert "company_id" in df.columns
    assert "peer_group_name" in df.columns
    assert "metric" in df.columns
    assert "percentile_rank" in df.columns
    assert "composite_quality_score" in df.columns


def test_prepare_company_data(engine):
    df = engine.load_peer_data()

    result = engine.prepare_company_data(
        df,
        "HDFCBANK",
    )

    assert result is not None
    assert result["company_id"] == "HDFCBANK"

    assert len(result["values"]) == 8

    expected_axes = {
        "ROE",
        "ROCE",
        "NPM",
        "D/E",
        "FCF",
        "PAT CAGR",
        "Revenue CAGR",
        "Composite Score",
    }

    assert set(result["values"]) == expected_axes


def test_radar_values_are_normalized(engine):
    df = engine.load_peer_data()

    result = engine.prepare_company_data(
        df,
        "HDFCBANK",
    )

    for value in result["values"].values():
        assert 0 <= value <= 1


def test_peer_average_has_eight_axes(engine):
    df = engine.load_peer_data()

    result = engine.peer_average(
        df,
        "Private Banks",
        "HDFCBANK",
    )

    assert len(result) == 8

    for value in result.values():
        assert 0 <= value <= 1


def test_radar_chart_is_created(engine):
    df = engine.load_peer_data()

    company = engine.prepare_company_data(
        df,
        "HDFCBANK",
    )

    peer_average = engine.peer_average(
        df,
        "Private Banks",
        "HDFCBANK",
    )

    output = engine.create_chart(
        company,
        peer_average,
    )

    assert output.exists()
    assert output.suffix == ".png"


def test_generate_all_creates_92_charts(engine):
    charts = engine.generate_all()

    assert len(charts) == 92
    assert all(path.exists() for path in charts)

def test_unassigned_company_uses_nifty100_fallback(engine):
    peer_df = engine.load_peer_data()
    nifty_df = engine.load_nifty100_data()

    assigned = set(
        peer_df["company_id"].dropna().unique()
    )

    all_companies = set(
        nifty_df["company_id"].dropna().unique()
    )

    unassigned = all_companies - assigned

    assert len(unassigned) == 36

    company_id = sorted(unassigned)[0]

    result = engine.unassigned_company_data(
        nifty_df,
        company_id,
    )

    assert result is not None
    assert result["company_id"] == company_id
    assert result["peer_group_name"] == "Nifty 100 Average"
    assert len(result["values"]) == 8

    for value in result["values"].values():
        assert 0 <= value <= 1
