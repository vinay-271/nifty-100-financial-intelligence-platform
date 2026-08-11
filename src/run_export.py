from pathlib import Path

from src.screener.engine import ScreenerEngine
from src.screener.exporter import export_screener_output


def main():
    engine = ScreenerEngine()

    try:
        engine.connect()
        engine.load_config()
        engine.load_data()

        output_path = Path(
            "reports/nifty100_screener.xlsx"
        )

        export_screener_output(
            engine,
            engine.data,
            output_path,
        )

        print(
            f"Screener workbook generated: {output_path}"
        )

    finally:
        engine.close()


if __name__ == "__main__":
    main()
