"""
Portfolio Summary PDF

Generates one page per company, ordered alphabetically
by ticker/company ID.
"""

from pathlib import Path
import sqlite3

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


DB_PATH = Path("db/nifty100.db")

OUTPUT_PATH = Path(
    "reports/portfolio/portfolio_summary.pdf"
)


KPI_COLUMNS = {
    "ROE": "return_on_equity_pct",
    "ROCE": "return_on_capital_employed_pct",
    "OPM": "operating_profit_margin_pct",
    "Revenue CAGR": "revenue_cagr_5yr",
    "PAT CAGR": "pat_cagr_5yr",
    "EPS CAGR": "eps_cagr_5yr",
}


def load_data():
    """Load company, sector and ratio data."""

    with sqlite3.connect(DB_PATH) as conn:

        companies = pd.read_sql(
            """
            SELECT
                id,
                company_name
            FROM companies
            """,
            conn,
        )

        sectors = pd.read_sql(
            """
            SELECT
                company_id,
                sector,
                industry
            FROM sectors
            """,
            conn,
        )

        ratios = pd.read_sql(
            """
            SELECT *
            FROM financial_ratios
            """,
            conn,
        )

    return (
        companies,
        sectors,
        ratios,
    )


def annual_only(df):
    """Remove TTM observations."""

    if df.empty:
        return df.copy()

    result = df.copy()

    result = result[
        ~result["year"]
        .astype(str)
        .str.upper()
        .eq("TTM")
    ]

    return result


def fiscal_year(value):
    """Extract fiscal year from strings such as Mar 2024."""

    try:
        return int(
            str(value)[-4:]
        )
    except (
        ValueError,
        TypeError,
    ):
        return None


def trend_arrow(previous, latest):
    """
    Determine trend direction.

    > +2%  -> ↑
    < -2%  -> ↓
    within ±2% -> →
    """

    if (
        pd.isna(previous)
        or pd.isna(latest)
    ):
        return "→"

    if previous == 0:
        if latest > 0:
            return "↑"
        if latest < 0:
            return "↓"
        return "→"

    change = (
        (latest - previous)
        / abs(previous)
        * 100
    )

    if change > 2:
        return "↑"

    if change < -2:
        return "↓"

    return "→"


def format_kpi(value):
    """Format KPI values for the PDF."""

    if pd.isna(value):
        return "N/A"

    return f"{float(value):.2f}%"


def build_company_record(
    company_id,
    companies,
    sectors,
    ratios,
):
    """Build the portfolio-page data for one company."""

    company_row = companies[
        companies["id"] == company_id
    ]

    if company_row.empty:
        return None

    company_row = company_row.iloc[0]

    sector_row = sectors[
        sectors["company_id"] == company_id
    ]

    sector = (
        sector_row.iloc[0]["sector"]
        if not sector_row.empty
        else "N/A"
    )

    company_ratios = ratios[
        ratios["company_id"] == company_id
    ].copy()

    company_ratios = annual_only(
        company_ratios
    )

    if company_ratios.empty:
        return {
            "company_id": company_id,
            "company_name": company_row[
                "company_name"
            ],
            "sector": sector,
            "latest_year": "N/A",
            "kpis": {},
        }

    company_ratios["fiscal_year"] = (
        company_ratios["year"]
        .apply(fiscal_year)
    )

    company_ratios = company_ratios.dropna(
        subset=["fiscal_year"]
    )

    company_ratios = company_ratios.sort_values(
        "fiscal_year"
    )

    latest = company_ratios.iloc[-1]

    previous = (
        company_ratios.iloc[-2]
        if len(company_ratios) >= 2
        else None
    )

    kpis = {}

    for label, column in KPI_COLUMNS.items():

        latest_value = latest.get(
            column
        )

        previous_value = (
            previous.get(column)
            if previous is not None
            else None
        )

        kpis[label] = {
            "value": latest_value,
            "trend": trend_arrow(
                previous_value,
                latest_value,
            ),
        }

    return {
        "company_id": company_id,
        "company_name": company_row[
            "company_name"
        ],
        "sector": sector,
        "latest_year": latest[
            "year"
        ],
        "kpis": kpis,
    }


def build_pdf():
    """Generate the complete portfolio summary PDF."""

    (
        companies,
        sectors,
        ratios,
    ) = load_data()

    company_ids = sorted(
        companies["id"]
        .astype(str)
        .tolist()
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="N100 Portfolio Summary",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PortfolioTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "PortfolioSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "PortfolioHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "PortfolioBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )

    story = []

    for index, company_id in enumerate(
        company_ids
    ):

        record = build_company_record(
            company_id,
            companies,
            sectors,
            ratios,
        )

        if record is None:
            continue

        story.append(
            Paragraph(
                record["company_name"],
                title_style,
            )
        )

        story.append(
            Paragraph(
                (
                    f"{record['company_id']} • "
                    f"{record['sector']} • "
                    f"{record['latest_year']}"
                ),
                subtitle_style,
            )
        )

        story.append(
            Paragraph(
                "Top 6 Financial KPIs",
                heading_style,
            )
        )

        header = [
            Paragraph(
                "<b>KPI</b>",
                body_style,
            ),
            Paragraph(
                "<b>Latest</b>",
                body_style,
            ),
            Paragraph(
                "<b>Trend</b>",
                body_style,
            ),
        ]

        rows = [header]

        for label, data in record[
            "kpis"
        ].items():

            rows.append(
                [
                    Paragraph(
                        label,
                        body_style,
                    ),
                    Paragraph(
                        format_kpi(
                            data["value"]
                        ),
                        body_style,
                    ),
                    Paragraph(
                        f"<font size='16'>"
                        f"{data['trend']}"
                        f"</font>",
                        body_style,
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                80 * mm,
                55 * mm,
                30 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.grey,
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        colors.lightgrey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.whitesmoke,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                ]
            )
        )

        story.append(table)

        story.append(
            Spacer(
                1,
                8 * mm,
            )
        )

        story.append(
            Paragraph(
                (
                    "Trend classification: "
                    "↑ improved • "
                    "↓ declined • "
                    "→ flat within ±2%"
                ),
                subtitle_style,
            )
        )

        if index < len(company_ids) - 1:
            story.append(
                PageBreak()
            )

    doc.build(story)

    return OUTPUT_PATH


if __name__ == "__main__":

    output = build_pdf()

    print(
        f"Generated: {output}"
    )
