import numpy as np
import pandas as pd
from typing import Dict, List, Optional


WEIGHTS = {
    "profitability": 0.35,
    "cash_quality": 0.30,
    "growth": 0.20,
    "leverage": 0.15,
}

PROFITABILITY_WEIGHTS = {
    "return_on_equity_pct": 0.15,
    "return_on_capital_employed_pct": 0.10,
    "net_profit_margin_pct": 0.10,
}

CASH_QUALITY_WEIGHTS = {
    "fcf_cagr_5yr": 0.15,
    "cfo_pat_ratio": 0.10,
    "fcf_positive_flag": 0.05,
}

GROWTH_WEIGHTS = {
    "revenue_cagr_5yr": 0.10,
    "pat_cagr_5yr": 0.10,
}

LEVERAGE_WEIGHTS = {
    "debt_to_equity": 0.10,
    "interest_coverage": 0.05,
}

METRIC_DIRECTION = {
    "return_on_equity_pct": True,
    "return_on_capital_employed_pct": True,
    "net_profit_margin_pct": True,
    "fcf_cagr_5yr": True,
    "cfo_pat_ratio": True,
    "fcf_positive_flag": True,
    "revenue_cagr_5yr": True,
    "pat_cagr_5yr": True,
    "debt_to_equity": False,
    "interest_coverage": True,
}

ALL_METRICS = list(METRIC_DIRECTION.keys())


def winsorise_p10_p90(series: pd.Series) -> pd.Series:
    p10 = series.quantile(0.10)
    p90 = series.quantile(0.90)
    return series.clip(lower=p10, upper=p90)


def normalize_metric(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    # Handle infinity values (debt-free ICR = inf) before winsorisation
    # They should get the maximum score for higher-is-better metrics
    # Convert to float to safely check for inf
    series_float = pd.to_numeric(series, errors='coerce')
    has_inf = np.isinf(series_float)
    
    winsorized = winsorise_p10_p90(series)
    p10 = winsorized.quantile(0.10)
    p90 = winsorized.quantile(0.90)

    if p90 == p10:
        normalized = pd.Series(50.0, index=series.index)
    else:
        normalized = (winsorized - p10) / (p90 - p10) * 100

    if not higher_is_better:
        normalized = 100 - normalized

    # Clip to [0, 100] to prevent interpolation edge effects
    normalized = normalized.clip(lower=0, upper=100)

    # Inf values (debt-free) get max score for higher-is-better
    if higher_is_better:
        normalized.loc[has_inf] = 100.0
    else:
        normalized.loc[has_inf] = 0.0

    normalized = normalized.fillna(0)
    return normalized


def compute_sector_relative_scores(
    df: pd.DataFrame,
    metric_cols: List[str],
    sector_col: str = "sector"
) -> pd.DataFrame:
    result = df.copy()

    for metric in metric_cols:
        higher_is_better = METRIC_DIRECTION.get(metric, True)

        global_norm = normalize_metric(df[metric], higher_is_better)

        sector_norm = df.groupby(sector_col)[metric].transform(
            lambda x: normalize_metric(x, higher_is_better)
        )

        result[f"{metric}_score"] = sector_norm.fillna(global_norm)

    return result


def compute_composite_quality_score(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    # Debt-free companies: interest_coverage = NaN -> treat as infinity
    # This must happen before winsorisation/normalization so they get max score
    if "interest_coverage" in result.columns:
        result["interest_coverage"] = result["interest_coverage"].fillna(float("inf"))

    all_metrics = list(METRIC_DIRECTION.keys())
    result = compute_sector_relative_scores(result, all_metrics)

    is_financials = result["sector"].str.lower() == "financials"
    if "debt_to_equity_score" in result.columns:
        result.loc[is_financials, "debt_to_equity_score"] = 50.0

    prof_score = sum(
        result[f"{m}_score"] * w
        for m, w in PROFITABILITY_WEIGHTS.items()
    )
    cash_score = sum(
        result[f"{m}_score"] * w
        for m, w in CASH_QUALITY_WEIGHTS.items()
    )
    growth_score = sum(
        result[f"{m}_score"] * w
        for m, w in GROWTH_WEIGHTS.items()
    )
    lev_score = sum(
        result[f"{m}_score"] * w
        for m, w in LEVERAGE_WEIGHTS.items()
    )

    result["composite_quality_score"] = (
        prof_score * WEIGHTS["profitability"] +
        cash_score * WEIGHTS["cash_quality"] +
        growth_score * WEIGHTS["growth"] +
        lev_score * WEIGHTS["leverage"]
    ).round(1)

    return result