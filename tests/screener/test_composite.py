import pytest
import pandas as pd
import numpy as np
from src.screener.composite import (
    winsorise_p10_p90,
    normalize_metric,
    compute_sector_relative_scores,
    compute_composite_quality_score,
    METRIC_DIRECTION,
    WEIGHTS,
    PROFITABILITY_WEIGHTS,
    CASH_QUALITY_WEIGHTS,
    GROWTH_WEIGHTS,
    LEVERAGE_WEIGHTS,
)


class TestWinsorisation:
    def test_winsorise_clips_at_p10_p90(self):
        s = pd.Series(range(100))
        w = winsorise_p10_p90(s)
        # pandas quantile uses interpolation, so p10=9.9, p90=89.1
        assert w.min() == pytest.approx(9.9)
        assert w.max() == pytest.approx(89.1)

    def test_winsorise_preserves_nan(self):
        s = pd.Series([1, 2, np.nan, 99, 100])
        w = winsorise_p10_p90(s)
        assert pd.isna(w.iloc[2])


class TestNormalization:
    def test_normalize_higher_is_better(self):
        s = pd.Series([10, 20, 30, 40, 50])
        n = normalize_metric(s, higher_is_better=True)
        # After clipping to [0, 100], all values must be in range
        assert n.between(0, 100).all()
        # Min should map to 0, max to 100
        assert n.min() == 0
        assert n.max() == 100

    def test_normalize_lower_is_better_inverts(self):
        s = pd.Series([10, 20, 30, 40, 50])
        n = normalize_metric(s, higher_is_better=False)
        # Should be inverted and clipped to [0, 100]
        assert n.between(0, 100).all()
        assert n.min() == 0
        assert n.max() == 100
        # Original min (10) should become max, original max (50) should become min
        assert n.iloc[0] > n.iloc[4]

    def test_normalize_missing_becomes_zero(self):
        s = pd.Series([10, 20, np.nan, 40, 50])
        n = normalize_metric(s, higher_is_better=True)
        assert n.iloc[2] == 0  # NaN -> 0

    def test_normalize_no_variance_returns_50(self):
        s = pd.Series([10, 10, 10, 10])
        n = normalize_metric(s, higher_is_better=True)
        assert (n == 50).all()

    def test_values_below_p10_get_zero(self):
        # Values at/below P10 should map to 0
        s = pd.Series(list(range(100)))
        n = normalize_metric(s, higher_is_better=True)
        # Original values 0-9 should all map to 0
        assert (n.iloc[:10] == 0).all()

    def test_values_above_p90_get_100(self):
        # Values at/above P90 should map to 100
        s = pd.Series(list(range(100)))
        n = normalize_metric(s, higher_is_better=True)
        # Original values 90-99 should all map to 100
        assert (n.iloc[90:] == 100).all()


class TestSectorRelative:
    def test_sector_relative_different_scores_same_metric(self):
        df = pd.DataFrame({
            "sector": ["Tech", "Tech", "Bank", "Bank"],
            "metric": [10, 20, 10, 20],
        })
        result = compute_sector_relative_scores(df, ["metric"])
        # Within each sector, same spread -> same normalized scores
        assert result.loc[0, "metric_score"] == result.loc[2, "metric_score"]
        assert result.loc[1, "metric_score"] == result.loc[3, "metric_score"]

    def test_no_sector_falls_back_to_global(self):
        df = pd.DataFrame({
            "sector": ["Tech", None, "Bank"],
            "metric": [10, 20, 30],
        })
        result = compute_sector_relative_scores(df, ["metric"])
        # No sector -> uses global normalization
        assert not pd.isna(result.loc[1, "metric_score"])


class TestCompositeScore:
    def test_composite_range_0_100(self):
        # Build minimal valid dataframe
        df = pd.DataFrame({
            "sector": ["Tech"] * 5,
            **{m: np.random.uniform(0, 20, 5) for m in METRIC_DIRECTION.keys()},
        })
        df["fcf_positive_flag"] = 1
        result = compute_composite_quality_score(df)
        scores = result["composite_quality_score"]
        assert scores.between(0, 100).all()

    def test_financials_de_component_neutral(self):
        df = pd.DataFrame({
            "sector": ["Financials", "Tech"],
            **{m: [10, 10] for m in METRIC_DIRECTION.keys()},
        })
        df["fcf_positive_flag"] = 1
        result = compute_composite_quality_score(df)
        # Financials D/E score should be 50
        assert result.loc[0, "debt_to_equity_score"] == 50.0

    def test_weights_sum_to_100(self):
        total = (WEIGHTS["profitability"] + WEIGHTS["cash_quality"] +
                 WEIGHTS["growth"] + WEIGHTS["leverage"])
        assert abs(total - 1.0) < 0.001

        assert abs(sum(PROFITABILITY_WEIGHTS.values()) - WEIGHTS["profitability"]) < 0.001
        assert abs(sum(CASH_QUALITY_WEIGHTS.values()) - WEIGHTS["cash_quality"]) < 0.001
        assert abs(sum(GROWTH_WEIGHTS.values()) - WEIGHTS["growth"]) < 0.001
        assert abs(sum(LEVERAGE_WEIGHTS.values()) - WEIGHTS["leverage"]) < 0.001

    def test_metric_directions_correct(self):
        # Profitability metrics: higher is better
        assert METRIC_DIRECTION["return_on_equity_pct"] is True
        assert METRIC_DIRECTION["return_on_capital_employed_pct"] is True
        assert METRIC_DIRECTION["net_profit_margin_pct"] is True

        # Cash quality: higher is better
        assert METRIC_DIRECTION["fcf_cagr_5yr"] is True
        assert METRIC_DIRECTION["cfo_pat_ratio"] is True
        assert METRIC_DIRECTION["fcf_positive_flag"] is True

        # Growth: higher is better
        assert METRIC_DIRECTION["revenue_cagr_5yr"] is True
        assert METRIC_DIRECTION["pat_cagr_5yr"] is True

        # Leverage: D/E lower is better, ICR higher is better
        assert METRIC_DIRECTION["debt_to_equity"] is False
        assert METRIC_DIRECTION["interest_coverage"] is True

    def test_composite_score_rounded_to_1_decimal(self):
        df = pd.DataFrame({
            "sector": ["Tech"] * 3,
            **{m: [10.0, 15.0, 20.0] for m in METRIC_DIRECTION.keys()},
        })
        df["fcf_positive_flag"] = 1
        result = compute_composite_quality_score(df)
        scores = result["composite_quality_score"]
        for s in scores:
            # Check that score has at most 1 decimal place
            assert round(s, 1) == s

    def test_missing_metric_component_score_zero(self):
        df = pd.DataFrame({
            "sector": ["Tech"] * 3,
            **{m: [10.0, 15.0, np.nan] for m in METRIC_DIRECTION.keys()},
        })
        df["fcf_positive_flag"] = 1
        result = compute_composite_quality_score(df)
        # The row with NaN should still get a composite score (component = 0)
        assert not pd.isna(result["composite_quality_score"]).any()

    def test_debt_free_icr_handling(self):
        # When interest_coverage is NaN (debt-free), it should be treated as infinity
        df = pd.DataFrame({
            "sector": ["Tech", "Tech"],
            **{m: [10.0, 10.0] for m in METRIC_DIRECTION.keys()},
        })
        df["fcf_positive_flag"] = 1
        # Simulate debt-free: interest_coverage = NaN
        df.loc[0, "interest_coverage"] = np.nan
        df.loc[1, "interest_coverage"] = 10.0
        result = compute_composite_quality_score(df)
        # Both should get valid scores
        assert not pd.isna(result["composite_quality_score"]).any()
        # The debt-free company's ICR component should be MAX (100)
        assert result.loc[0, "interest_coverage_score"] == 100.0
        # The company with finite ICR should have lower score
        assert result.loc[1, "interest_coverage_score"] < 100.0

    def test_composite_score_stays_in_bounds(self):
        # Even with extreme values, composite must stay in [0, 100]
        df = pd.DataFrame({
            "sector": ["Tech"] * 10,
            **{m: np.random.uniform(-1000, 1000, 10) for m in METRIC_DIRECTION.keys()},
        })
        df["fcf_positive_flag"] = 1
        result = compute_composite_quality_score(df)
        scores = result["composite_quality_score"]
        assert scores.between(0, 100).all()
        # Also check component scores are in bounds
        for m in METRIC_DIRECTION.keys():
            col = f"{m}_score"
            if col in result.columns:
                assert result[col].between(0, 100).all()