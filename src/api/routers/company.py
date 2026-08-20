from pathlib import Path
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlite3 import Connection


DB_PATH = Path("db/nifty100.db")
TEARSHEET_DIR = Path("output/tearsheets")


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


def get_db():
    """Create a database connection for one request."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()


def rows_to_dict(rows):
    """Convert SQLite rows into JSON-compatible dictionaries."""

    return [dict(row) for row in rows]


def get_company(
    ticker: str,
    conn: Connection,
):
    """Return the company record or raise 404."""

    row = conn.execute(
        """
        SELECT *
        FROM companies
        WHERE id = ?
        """,
        (ticker.upper(),),
    ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company '{ticker.upper()}' not found",
        )

    return dict(row)


@router.get("/{ticker}")
def company_profile(
    ticker: str,
    conn: Connection = Depends(get_db),
):
    """Return company profile and sector information."""

    company = get_company(
        ticker,
        conn,
    )

    sector = conn.execute(
        """
        SELECT *
        FROM sectors
        WHERE company_id = ?
        """,
        (ticker.upper(),),
    ).fetchone()

    result = {
        "company": company,
        "sector": (
            dict(sector)
            if sector is not None
            else None
        ),
    }

    return result


@router.get("/{ticker}/profit-loss")
def company_profit_loss(
    ticker: str,
    conn: Connection = Depends(get_db),
):
    """Return historical profit and loss data."""

    get_company(
        ticker,
        conn,
    )

    rows = conn.execute(
        """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker.upper(),),
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No profit and loss data found "
                f"for '{ticker.upper()}'"
            ),
        )

    return {
        "company_id": ticker.upper(),
        "records": rows_to_dict(rows),
    }


@router.get("/{ticker}/balance-sheet")
def company_balance_sheet(
    ticker: str,
    conn: Connection = Depends(get_db),
):
    """Return historical balance sheet data."""

    get_company(
        ticker,
        conn,
    )

    rows = conn.execute(
        """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker.upper(),),
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No balance sheet data found "
                f"for '{ticker.upper()}'"
            ),
        )

    return {
        "company_id": ticker.upper(),
        "records": rows_to_dict(rows),
    }


@router.get("/{ticker}/cash-flow")
def company_cash_flow(
    ticker: str,
    conn: Connection = Depends(get_db),
):
    """Return historical cash flow data."""

    get_company(
        ticker,
        conn,
    )

    rows = conn.execute(
        """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker.upper(),),
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No cash flow data found "
                f"for '{ticker.upper()}'"
            ),
        )

    return {
        "company_id": ticker.upper(),
        "records": rows_to_dict(rows),
    }


@router.get("/{ticker}/ratios")
def company_ratios(
    ticker: str,
    conn: Connection = Depends(get_db),
):
    """Return historical financial ratios."""

    get_company(
        ticker,
        conn,
    )

    rows = conn.execute(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
        """,
        (ticker.upper(),),
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No financial ratio data found "
                f"for '{ticker.upper()}'"
            ),
        )

    return {
        "company_id": ticker.upper(),
        "records": rows_to_dict(rows),
    }


@router.get("/{ticker}/tearsheet")
def company_tearsheet(
    ticker: str,
):
    """Serve the already-generated company tearsheet PDF."""

    ticker = ticker.upper()

    pdf_path = (
        TEARSHEET_DIR
        / f"{ticker}_tearsheet.pdf"
    )

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Tearsheet not found "
                f"for '{ticker}'"
            ),
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=(
            f"{ticker}_tearsheet.pdf"
        ),
    )
