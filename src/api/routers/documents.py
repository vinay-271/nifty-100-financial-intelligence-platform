from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


TEARSHEET_DIR = Path(
    "output/tearsheets"
)

PORTFOLIO_PDF = Path(
    "reports/portfolio/portfolio_summary.pdf"
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get("/tearsheet/{ticker}")
def get_tearsheet(
    ticker: str,
):
    """Download a company's tearsheet."""

    ticker = ticker.upper()

    path = (
        TEARSHEET_DIR
        / f"{ticker}_tearsheet.pdf"
    )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"Tearsheet not found "
                f"for '{ticker}'"
            ),
        )

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=f"{ticker}_tearsheet.pdf",
    )


@router.get("/portfolio-summary")
def get_portfolio_summary():
    """Download the portfolio summary PDF."""

    if not PORTFOLIO_PDF.exists():
        raise HTTPException(
            status_code=404,
            detail="Portfolio summary PDF not found",
        )

    return FileResponse(
        path=PORTFOLIO_PDF,
        media_type="application/pdf",
        filename="portfolio_summary.pdf",
    )
