import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException


DB_PATH = Path(
    "db/nifty100.db"
)


router = APIRouter(
    prefix="/peers",
    tags=["Peers"],
)


def get_connection():
    conn = sqlite3.connect(
        DB_PATH
    )
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/{ticker}")
def get_peer_data(
    ticker: str,
):
    """Return peer percentile data for a company."""

    ticker = ticker.upper()

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM peer_percentiles
            WHERE company_id = ?
            """,
            (ticker,),
        ).fetchall()

    finally:
        conn.close()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No peer data found "
                f"for '{ticker}'"
            ),
        )

    return {
        "company_id": ticker,
        "records": [
            dict(row)
            for row in rows
        ],
    }
