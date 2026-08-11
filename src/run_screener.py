#!/usr/bin/env python
"""Sprint 3 Day 17 — Screener Runner.

Orchestrates the screener engine, composite scoring, and Excel export.
"""

from pathlib import Path
from loguru import logger

from src.screener.engine import ScreenerEngine
from src.screener.exporter import export_screener_output
from src.constants import PROJECT_ROOT


def main():
    logger.info("=" * 60)
    logger.info("Starting Screener Engine (Day 17)")
    logger.info("=" * 60)

    engine = ScreenerEngine()
    engine.connect()
    engine.load_config()
    engine.load_data()

    df = engine.latest_annual_data()
    logger.info(f"Latest annual universe: {len(df)} companies")

    logger.info("Computing composite quality scores...")
    df = engine.compute_composite_scores(df)
    logger.info(
        f"Composite scores computed. Range: "
        f"{df['composite_quality_score'].min():.1f} - "
        f"{df['composite_quality_score'].max():.1f}"
    )

    output_dir = PROJECT_ROOT / "output"
    output_path = output_dir / "screener_output.xlsx"
    logger.info(f"Exporting to {output_path}...")
    export_screener_output(engine, df, output_path)

    logger.info(f"Screener output written to {output_path}")

    engine.close()

    logger.success("Day 17 complete — Screener output generated successfully")


if __name__ == "__main__":
    main()