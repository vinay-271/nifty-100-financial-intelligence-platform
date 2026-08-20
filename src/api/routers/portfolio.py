from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


OUTPUT_DIR = Path("output")


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


@router.get("/statistics")
def portfolio_statistics():
    """Return portfolio-level statistics."""

    path = OUTPUT_DIR / "portfolio_statistics.csv"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Portfolio statistics not found",
        )

    df = pd.read_csv(path)

    return {
        "count": len(df),
        "records": df.where(
            pd.notna(df),
            None,
        ).to_dict(
            orient="records"
        ),
    }


@router.get("/clusters")
def portfolio_clusters():
    """Return portfolio cluster labels."""

    path = OUTPUT_DIR / "cluster_labels.csv"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Cluster labels not found",
        )

    df = pd.read_csv(path)

    return {
        "count": len(df),
        "records": df.where(
            pd.notna(df),
            None,
        ).to_dict(
            orient="records"
        ),
    }
