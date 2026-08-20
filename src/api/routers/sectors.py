import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException


DB_PATH = Path(
    "db/nifty100.db"
)


router = APIRouter(
    prefix="/sectors",
    tags=["Sectors"],
)


def get_connection():
    conn = sqlite3.connect(
        DB_PATH
    )
    conn.row_factory = sqlite3.Row
    return conn


@router.get("")
def list_sectors():
    """Return sector distribution."""

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                sector,
                COUNT(*) AS company_count
            FROM sectors
            GROUP BY sector
            ORDER BY company_count DESC
            """
        ).fetchall()

    finally:
        conn.close()

    return {
        "count": len(rows),
        "sectors": [
            dict(row)
            for row in rows
        ],
    }


@router.get("/{sector_name}")
def get_sector(
    sector_name: str,
):
    """Return companies belonging to a sector."""

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                company_id,
                sector,
                industry,
                weight_pct,
                market_cap_category
            FROM sectors
            WHERE LOWER(sector) = LOWER(?)
            ORDER BY company_id
            """,
            (sector_name,),
        ).fetchall()

    finally:
        conn.close()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Sector '{sector_name}' "
                f"not found"
            ),
        )

    return {
        "sector": sector_name,
        "company_count": len(rows),
        "companies": [
            dict(row)
            for row in rows
        ],
    }
