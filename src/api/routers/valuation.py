from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


OUTPUT_DIR = Path("output")


router = APIRouter(
    prefix="/valuation",
    tags=["Valuation"],
)


@router.get("/summary")
def valuation_summary():
    """Return the latest valuation summary."""

    path = OUTPUT_DIR / "valuation_summary.xlsx"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Valuation summary not found",
        )

    sheets = pd.read_excel(
        path,
        sheet_name=None,
    )

    result = {}

    for name, df in sheets.items():

        records = df.to_dict(
            orient="records"
        )

        cleaned = []

        for record in records:

            item = {}

            for key, value in record.items():

                if pd.isna(value):
                    item[key] = None

                elif hasattr(value, "item"):
                    item[key] = value.item()

                else:
                    item[key] = value

            cleaned.append(item)

        result[name] = cleaned

    return {
        "sheets": result
    }


@router.get("/flags")
def valuation_flags():
    """Return valuation flags."""

    path = OUTPUT_DIR / "valuation_flags.csv"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Valuation flags not found",
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
