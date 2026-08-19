"""
Batch financial tearsheet generation.

Generates a PDF tearsheet for every company in the
Nifty 100 database and records success/failure.
"""

import json
import pymupdf
from pathlib import Path
import sqlite3
import time

import pandas as pd

from src.reports.tearsheet import (
    generate_pdf,
)


DB_PATH = Path("db/nifty100.db")

OUTPUT_DIR = Path(
    "output/tearsheets"
)

REPORT_PATH = Path(
    "output/tearsheet_generation_report.csv"
)

SUMMARY_PATH = Path(
    "output/tearsheet_generation_summary.json"
)

def load_company_ids():
    """Load all company IDs from the database."""

    with sqlite3.connect(DB_PATH) as conn:

        companies = pd.read_sql(
            """
            SELECT id
            FROM companies
            """,
            conn,
        )

    return (
        companies["id"]
        .astype(str)
        .tolist()
    )

def validate_pdf(
    pdf_path,
    company_id,
):
    """
    Validate a generated tearsheet PDF.

    Checks:
    - file exists
    - file is non-empty
    - PDF can be opened
    - exactly 2 pages
    - company ID appears in PDF text
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        return False, "PDF file does not exist"

    if pdf_path.stat().st_size == 0:
        return False, "PDF file is empty"

    try:
        document = pymupdf.open(
            str(pdf_path)
        )

    except Exception as exc:
        return False, (
            f"PDF could not be opened: {exc}"
        )

    try:

        page_count = len(document)

        if page_count != 2:
            return False, (
                f"Expected 2 pages, "
                f"found {page_count}"
            )

        text = ""

        for page in document:
            text += page.get_text()

        if company_id not in text:
            return False, (
                "Company ID not found in PDF text"
            )

        return True, "OK"

    finally:
        document.close()


def generate_all():
    """Generate tearsheets for all companies."""

    company_ids = load_company_ids()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    total = len(company_ids)

    print(
        f"Companies to process: {total}"
    )

    for index, company_id in enumerate(
        company_ids,
        start=1,
    ):

        print(
            f"[{index}/{total}] "
            f"{company_id}...",
            end=" ",
        )

        start = time.perf_counter()

        try:

            output_path = generate_pdf(
                company_id
            )

            elapsed = (
                time.perf_counter()
                - start
            )

            output_path = Path(
                output_path
            )

            valid, validation_message = (
                validate_pdf(
                    output_path,
                    company_id,
                )
            )

            elapsed = (
                time.perf_counter()
                - start
            )

            results.append(
                {
                    "company_id": company_id,
                    "status": (
                        "SUCCESS"
                        if valid
                        else "INVALID"
                    ),
                    "output_path": str(
                        output_path
                    ),
                    "file_size_bytes": (
                        output_path.stat().st_size
                        if output_path.exists()
                        else 0
                    ),
                    "generation_time_sec": round(
                        elapsed,
                        3,
                    ),
                    "validation": validation_message,
                    "error": "",
                }
            )

            if valid:
                print(
                    f"OK ({elapsed:.2f}s)"
                )
            else:
                print(
                    f"INVALID: "
                    f"{validation_message}"
                )

        except Exception as exc:

            elapsed = (
                time.perf_counter()
                - start
            )

            results.append(
                {
                    "company_id": company_id,
                    "status": "FAILED",
                    "output_path": "",
                    "file_size_bytes": 0,
                    "generation_time_sec": round(
                        elapsed,
                        3,
                    ),
                    "error": repr(exc),
                    "validation": "",
                }
            )

            print(
                f"FAILED: {exc}"
            )

    df = pd.DataFrame(results)

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        REPORT_PATH,
        index=False,
    )

    summary = {
        "total_companies": int(len(df)),
        "successful": int(
            (df["status"] == "SUCCESS").sum()
        ),
        "invalid": int(
            (df["status"] == "INVALID").sum()
        ),
        "failed": int(
            (df["status"] == "FAILED").sum()
        ),
        "success_rate_pct": round(
            (
                (df["status"] == "SUCCESS").sum()
                / len(df)
                * 100
            ),
            2,
        ),
        "validation_rate_pct": round(
            (
                (
                    df["status"]
                    .isin(["SUCCESS"])
                    .sum()
                )
                / len(df)
                * 100
            ),
            2,
        ),
    }

    SUMMARY_PATH.write_text(
        json.dumps(
            summary,
            indent=4,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "========================================"
    )
    print(
        "Batch generation complete"
    )
    print(
        "========================================"
    )

    print(
        f"Total:   {len(df)}"
    )

    print(
        f"Success: "
        f"{(df.status == 'SUCCESS').sum()}"
    )

    print(
        f"Invalid: "
        f"{(df.status == 'INVALID').sum()}"
    )

    print(
        f"Failed:  "
        f"{(df.status == 'FAILED').sum()}"
    )

    print(
        f"Report:  {REPORT_PATH}"
    )

    print(
        f"Summary: {SUMMARY_PATH}"
    )
    return df


if __name__ == "__main__":

    generate_all()
