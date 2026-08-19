"""
Company Financial Tearsheet
Sprint 3 - Day 33

Generates a 2-page PDF financial tearsheet
for an individual Nifty 100 company.
"""

from pathlib import Path
import sqlite3

import pandas as pd

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from reportlab.platypus import Image

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.enums import TA_LEFT
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
OUTPUT_DIR = Path("output/tearsheets")


def load_company_data(company_id):
    """Load all data required for a company tearsheet."""

    with sqlite3.connect(DB_PATH) as conn:

        company = pd.read_sql(
            """
            SELECT *
            FROM companies
            WHERE id = ?
            """,
            conn,
            params=[company_id],
        )

        sectors = pd.read_sql(
            """
            SELECT *
            FROM sectors
            WHERE company_id = ?
            """,
            conn,
            params=[company_id],
        )

        ratios = pd.read_sql(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
            """,
            conn,
            params=[company_id],
        )

        profit_loss = pd.read_sql(
            """
            SELECT *
            FROM profitandloss
            WHERE company_id = ?
            ORDER BY year
            """,
            conn,
            params=[company_id],
        )

        balance_sheet = pd.read_sql(
            """
            SELECT *
            FROM balancesheet
            WHERE company_id = ?
            ORDER BY year
            """,
            conn,
            params=[company_id],
        )

        cashflow = pd.read_sql(
            """
            SELECT *
            FROM cashflow
            WHERE company_id = ?
            ORDER BY year
            """,
            conn,
            params=[company_id],
        )

    return {
        "company": company,
        "sector": sectors,
        "ratios": ratios,
        "profit_loss": profit_loss,
        "balance_sheet": balance_sheet,
        "cashflow": cashflow,
    }


def load_pros_cons(company_id):
    """Load generated pros and cons."""

    path = Path("output/pros_cons_generated.csv")

    if not path.exists():
        return pd.DataFrame(
            columns=[
                "company_id",
                "type",
                "rule_id",
                "text",
                "confidence_pct",
            ]
        )

    df = pd.read_csv(path)

    return df[df["company_id"] == company_id].copy()


def load_capital_allocation(company_id):
    """Load historical capital allocation patterns."""

    path = Path(
        "data/output/capital_allocation.csv"
    )

    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return df[
        df["company_id"] == company_id
    ].copy()


def normalize_year(value):
    """
    Normalize financial year labels.

    Examples:
        Mar 2024 -> 2024
        Mar-24  -> 2024
        Sep 2024 -> 2024
    """

    if pd.isna(value):
        return None

    text = str(value)

    try:
        year = int(text[-4:])

        if 1900 <= year <= 2100:
            return year
    except ValueError:
        pass

    try:
        year = int(text[-2:])

        if year < 50:
            return 2000 + year

        return 1900 + year

    except ValueError:
        return None


def prepare_data(data):
    """Normalize and prepare financial datasets."""

    for key in [
        "ratios",
        "profit_loss",
        "balance_sheet",
        "cashflow",
    ]:
        df = data[key].copy()

        if "year" in df.columns:
            df["fiscal_year"] = df[
                "year"
            ].apply(normalize_year)

        data[key] = df

    return data


def latest_annual(df):
    """Return latest annual observation, excluding TTM."""

    if df.empty:
        return None

    annual = df[
        ~df["year"]
        .astype(str)
        .str.upper()
        .eq("TTM")
    ].copy()

    if annual.empty:
        return None

    annual = annual.sort_values(
        "fiscal_year"
    )

    return annual.iloc[-1]


def build_tearsheet_data(company_id):
    """Build the complete data model for the PDF."""

    data = load_company_data(company_id)

    data = prepare_data(data)

    pros_cons = load_pros_cons(company_id)

    capital_allocation = (
        load_capital_allocation(company_id)
    )

    latest_ratios = latest_annual(
        data["ratios"]
    )

    latest_pl = latest_annual(
        data["profit_loss"]
    )

    latest_bs = latest_annual(
        data["balance_sheet"]
    )

    return {
        "company": data["company"],
        "sector": data["sector"],
        "ratios": data["ratios"],
        "profit_loss": data["profit_loss"],
        "balance_sheet": data["balance_sheet"],
        "cashflow": data["cashflow"],
        "pros_cons": pros_cons,
        "capital_allocation": capital_allocation,
        "latest_ratios": latest_ratios,
        "latest_pl": latest_pl,
        "latest_bs": latest_bs,
    }

def build_kpis(data):
    """Extract the headline KPIs for the latest annual period."""

    ratios = data["latest_ratios"]

    if ratios is None:
        return {}

    return {
        "ROE": ratios.get("return_on_equity_pct"),
        "ROCE": ratios.get(
            "return_on_capital_employed_pct"
        ),
        "OPM": ratios.get(
            "operating_profit_margin_pct"
        ),
        "Revenue CAGR": ratios.get(
            "revenue_cagr_5yr"
        ),
        "PAT CAGR": ratios.get(
            "pat_cagr_5yr"
        ),
        "EPS CAGR": ratios.get(
            "eps_cagr_5yr"
        ),
    }

def format_pct(value):
    """Format a percentage value."""

    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.2f}%"

def create_financial_charts(data, company_id):
    """Create temporary PNG charts for the tearsheet."""

    chart_dir = OUTPUT_DIR / "charts"
    chart_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    ratios = data["ratios"].copy()
    pl = data["profit_loss"].copy()

    # ---------------------------------------------------------
    # Revenue + Net Profit
    # ---------------------------------------------------------

    financial = pl[
        ~pl["year"]
        .astype(str)
        .str.upper()
        .eq("TTM")
    ].copy()

    financial = financial.sort_values(
        "fiscal_year"
    ).tail(10)

    revenue_path = (
        chart_dir
        / f"{company_id}_financial_trend.png"
    )

    fig, ax = plt.subplots(
        figsize=(7.2, 2.8)
    )

    ax.plot(
        financial["fiscal_year"],
        financial["sales"],
        marker="o",
        label="Revenue",
    )

    ax.plot(
        financial["fiscal_year"],
        financial["net_profit"],
        marker="o",
        label="Net Profit",
    )

    ax.set_title(
        "Revenue & Net Profit Trend"
    )

    ax.set_xlabel("Fiscal Year")
    ax.set_ylabel("₹ Crore")

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
        loc="upper left",
    )

    fig.tight_layout()

    fig.savefig(
        revenue_path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    # ---------------------------------------------------------
    # ROE + ROCE
    # ---------------------------------------------------------

    ratio_history = ratios[
        ~ratios["year"]
        .astype(str)
        .str.upper()
        .eq("TTM")
    ].copy()

    ratio_history = ratio_history.sort_values(
        "fiscal_year"
    ).tail(10)

    returns_path = (
        chart_dir
        / f"{company_id}_returns_trend.png"
    )

    fig, ax = plt.subplots(
        figsize=(7.2, 2.8)
    )

    ax.plot(
        ratio_history["fiscal_year"],
        ratio_history[
            "return_on_equity_pct"
        ],
        marker="o",
        label="ROE",
    )

    ax.plot(
        ratio_history["fiscal_year"],
        ratio_history[
            "return_on_capital_employed_pct"
        ],
        marker="o",
        label="ROCE",
    )

    ax.set_title(
        "ROE & ROCE Trend"
    )

    ax.set_xlabel("Fiscal Year")
    ax.set_ylabel("%")

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend(
        frameon=False,
        loc="best",
    )

    fig.tight_layout()

    fig.savefig(
        returns_path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)

    return (
        revenue_path,
        returns_path,
    )

def build_balance_sheet_summary(data):
    """Extract latest annual balance-sheet values."""

    bs = data["latest_bs"]

    if bs is None:
        return {}

    return {
        "Equity Capital": bs.get("equity_capital"),
        "Reserves": bs.get("reserves"),
        "Borrowings": bs.get("borrowings"),
        "Other Liabilities": bs.get(
            "other_liabilities"
        ),
        "Total Assets": bs.get("total_assets"),
    }


def build_cashflow_summary(data):
    """Extract latest annual cash-flow values."""

    cf = data["cashflow"]

    if cf.empty:
        return {}

    annual = cf[
        ~cf["year"]
        .astype(str)
        .str.upper()
        .str.contains("TTM")
    ].copy()

    if annual.empty:
        return {}

    annual = annual.sort_values(
        "fiscal_year"
    )

    latest = annual.iloc[-1]

    return {
        "CFO": latest.get(
            "operating_activity"
        ),
        "CFI": latest.get(
            "investing_activity"
        ),
        "CFF": latest.get(
            "financing_activity"
        ),
        "Net Cash Flow": latest.get(
            "net_cash_flow"
        ),
    }


def build_capital_allocation_summary(data):
    """Get the latest capital-allocation pattern."""

    allocation = data[
        "capital_allocation"
    ].copy()

    if allocation.empty:
        return None

    allocation["fiscal_year"] = (
        allocation["year"]
        .apply(normalize_year)
    )

    allocation = allocation.dropna(
        subset=["fiscal_year"]
    )

    if allocation.empty:
        return None

    allocation = allocation.sort_values(
        "fiscal_year"
    )

    return allocation.iloc[-1][
        "pattern_label"
    ]

def capital_allocation_description(pattern):
    """Return a human-readable explanation."""

    descriptions = {
        "Shareholder Returns":
            "Strong operating cash generation is being "
            "combined with investment and shareholder "
            "cash outflows.",

        "Reinvestor":
            "Operating cash is being reinvested into the "
            "business while financing cash flow remains "
            "negative.",

        "Liquidating Assets":
            "Operating cash is positive while investing "
            "cash flow is positive, indicating cash "
            "generation from asset/investment activity.",

        "Growth Funded by Debt":
            "Investment spending is being supported by "
            "external financing.",

        "Cash Accumulator":
            "Positive cash generation across operating, "
            "investing and financing activities indicates "
            "cash accumulation.",

        "Distress Signal":
            "Negative operating cash flow combined with "
            "positive financing activity warrants close "
            "monitoring.",

        "Pre-Revenue":
            "Cash flows are negative across operating, "
            "investing and financing activities.",

        "Mixed":
            "The company shows a mixed capital-allocation "
            "pattern across operating, investing and "
            "financing activities.",

        "Other":
            "The latest cash-flow pattern does not match "
            "a primary capital-allocation classification.",
    }

    return descriptions.get(
        pattern,
        "Capital-allocation pattern unavailable.",
    )

def generate_pdf(company_id):
    """Generate a 2-page company tearsheet."""

    data = build_tearsheet_data(company_id)
    kpis = build_kpis(data)

    financial_chart, returns_chart = (
        create_financial_charts(
            data,
            company_id,
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    company_name = data[
        "company"
    ].iloc[0]["company_name"]

    logo_path = create_logo(
        data["company"].iloc[0],
        company_id,
    )

    output_path = (
        OUTPUT_DIR
        / f"{company_id}_tearsheet.pdf"
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"{company_name} Financial Tearsheet",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TearsheetTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "TearsheetSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=10,
    )

    header_name_style = ParagraphStyle(
        "HeaderName",
        parent=styles["Normal"],
        fontSize=18,
        leading=21,
    )

    header_subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        textColor=colors.grey,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=14,
        spaceBefore=6,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "TearsheetBody",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )

    story = []

    # ---------------------------------------------------------
    # PAGE 1 — HEADER
    # ---------------------------------------------------------

    sector = data["sector"]

    if not sector.empty:
        sector_name = sector.iloc[0]["sector"]
        industry = sector.iloc[0]["industry"]
        subtitle = f"{sector_name} • {industry}"
    else:
        subtitle = "Nifty 100 Company"

    header_text = Table(
        [
            [
                Paragraph(
                    company_name,
                    header_name_style,
                ),
                Paragraph(
                    subtitle,
                    header_subtitle_style,
                ),
            ]
        ],
        colWidths=[
            115 * mm,
            60 * mm,
        ],
    )

    header_text.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    if logo_path is not None:

        logo = Image(
            str(logo_path),
            width=16 * mm,
            height=16 * mm,
        )

        header = Table(
            [
                [
                    logo,
                    header_text,
                ]
            ],
            colWidths=[
                20 * mm,
                155 * mm,
            ],
        )

        header.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                ]
            )
        )

        story.append(header)

    else:

        story.append(header_text)

    story.append(
        Paragraph(
            "Financial Snapshot",
            heading_style,
        )
    )

    # KPI cards represented as a table for now.
    kpi_data = []

    items = list(kpis.items())

    for i in range(0, len(items), 3):

        row = []

        for name, value in items[i:i + 3]:

            row.append(
                Paragraph(
                    f"<b>{name}</b><br/>"
                    f"<font size='13'>"
                    f"{format_pct(value)}"
                    f"</font>",
                    body_style,
                )
            )

        while len(row) < 3:
            row.append("")

        kpi_data.append(row)

    kpi_table = Table(
        kpi_data,
        colWidths=[
            58 * mm,
            58 * mm,
            58 * mm,
        ],
    )

    kpi_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(kpi_table)

    story.append(Spacer(1, 8 * mm))

    # ---------------------------------------------------------
    # PAGE 2 PLACEHOLDER
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Financial History",
            heading_style,
        )
    )

    story.append(
        Image(
            str(financial_chart),
            width=175 * mm,
            height=68 * mm,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        Image(
            str(returns_chart),
            width=175 * mm,
            height=68 * mm,
        )
    )

    story.append(PageBreak())

    # =========================================================
    # PAGE 2 — INVESTMENT INTELLIGENCE
    # =========================================================

    balance = build_balance_sheet_summary(data)
    cashflow = build_cashflow_summary(data)
    capital_pattern = (
        build_capital_allocation_summary(data)
    )

    story.append(
        Paragraph(
            "Investment Intelligence",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"{company_id} • Latest Annual Financials",
            subtitle_style,
        )
    )

    # ---------------------------------------------------------
    # BALANCE SHEET
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Balance Sheet",
            heading_style,
        )
    )

    balance_items = [
        ("Equity Capital", balance.get("Equity Capital")),
        ("Reserves", balance.get("Reserves")),
        ("Borrowings", balance.get("Borrowings")),
        ("Other Liabilities", balance.get("Other Liabilities")),
        ("Total Assets", balance.get("Total Assets")),
    ]

    balance_table = Table(
        [
            [
                Paragraph(
                    f"<b>{name}</b><br/>"
                    f"{format_cr(value)}",
                    body_style,
                )
                for name, value in balance_items
            ]
        ],
        colWidths=[
            35 * mm,
            35 * mm,
            35 * mm,
            35 * mm,
            35 * mm,
        ],
    )

    balance_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(balance_table)

    # ---------------------------------------------------------
    # CASH FLOW
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Cash Flow",
            heading_style,
        )
    )

    cashflow_items = [
        ("CFO", cashflow.get("CFO")),
        ("CFI", cashflow.get("CFI")),
        ("CFF", cashflow.get("CFF")),
        ("Net Cash Flow", cashflow.get("Net Cash Flow")),
    ]

    cashflow_table = Table(
        [
            [
                Paragraph(
                    f"<b>{name}</b><br/>"
                    f"{format_cr(value)}",
                    body_style,
                )
                for name, value in cashflow_items
            ]
        ],
        colWidths=[
            43.75 * mm,
            43.75 * mm,
            43.75 * mm,
            43.75 * mm,
        ],
    )

    cashflow_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(cashflow_table)

    story.append(
        Spacer(1, 4 * mm)
    )

    # ---------------------------------------------------------
    # PROS / CONS
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Pros & Cons",
            heading_style,
        )
    )

    pros = data["pros_cons"][
        data["pros_cons"]["type"] == "pro"
    ]

    cons = data["pros_cons"][
        data["pros_cons"]["type"] == "con"
    ]

    max_items = max(
        len(pros),
        len(cons),
    )

    pros_text = []

    for _, row in pros.iterrows():
        pros_text.append(
            f"✓ {row['text']}"
        )

    cons_text = []

    for _, row in cons.iterrows():
        cons_text.append(
            f"! {row['text']}"
        )

    pros_paragraph = "<br/><br/>".join(
        pros_text[:6]
    ) or "No material positives identified."

    cons_paragraph = "<br/><br/>".join(
        cons_text[:6]
    ) or "No material weaknesses identified."

    pros_cons_table = Table(
        [
            [
                Paragraph(
                    "<b>PROS</b><br/><br/>"
                    + pros_paragraph,
                    body_style,
                ),
                Paragraph(
                    "<b>CONS</b><br/><br/>"
                    + cons_paragraph,
                    body_style,
                ),
            ]
        ],
        colWidths=[
            87.5 * mm,
            87.5 * mm,
        ],
    )

    pros_cons_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.25,
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
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

    story.append(pros_cons_table)

    story.append(
        Spacer(1, 4 * mm)
    )

    # ---------------------------------------------------------
    # CAPITAL ALLOCATION
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "Capital Allocation",
            heading_style,
        )
    )

    allocation_text = (
        capital_pattern
        if capital_pattern is not None
        else "Unavailable"
    )

    allocation_table = Table(
        [
            [
                Paragraph(
                    f"<b>Latest Pattern</b><br/>"
                    f"<font size='14'>"
                    f"{allocation_text}"
                    f"</font>",
                    body_style,
                )
            ]
        ],
        colWidths=[175 * mm],
    )

    allocation_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
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

    story.append(allocation_table)

    doc.build(story)

    return output_path

def format_cr(value):
    """Format ₹ crore values."""

    if value is None or pd.isna(value):
        return "N/A"

    return f"Rs. {float(value):,.0f} Cr"

def create_logo(company_row, company_id):
    """Create a ReportLab logo if the company logo is available."""

    logo_url = company_row.get("company_logo")

    if not logo_url or pd.isna(logo_url):
        return None

    try:
        import requests

        response = requests.get(
            logo_url,
            timeout=5,
        )

        if response.status_code != 200:
            return None

        logo_path = (
            OUTPUT_DIR
            / "charts"
            / f"{company_id}_logo.png"
        )

        logo_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        logo_path.write_bytes(
            response.content
        )

        return logo_path

    except Exception:
        return None

# if __name__ == "__main__":

#     output = generate_pdf("TCS")

#     print(
#         f"Generated: {output}"
#     )

if __name__ == "__main__":

    companies = [
        "TCS",
        "BHEL",
        "JINDALSTEL",
        "RELIANCE",
        "ATGL",
    ]

    for company_id in companies:

        print(
            f"\nGenerating {company_id}..."
        )

        try:

            output = generate_pdf(
                company_id
            )

            print(
                f"Generated: {output}"
            )

        except Exception as exc:

            print(
                f"FAILED: {company_id}"
            )

            print(
                repr(exc)
            )
