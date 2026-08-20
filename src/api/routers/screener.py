from pathlib import Path

import math
import yaml
from fastapi import APIRouter, HTTPException

from src.screener.engine import ScreenerEngine


CONFIG_PATH = Path(
    "config/screener_config.yaml"
)


router = APIRouter(
    prefix="/screener",
    tags=["Screener"],
)


@router.get("/presets")
def list_presets():
    """List available screener presets."""

    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        config = yaml.safe_load(file)

    presets = config.get(
        "presets",
        {},
    )

    return {
        "count": len(presets),
        "presets": list(
            presets.keys()
        ),
    }


@router.get("/preset/{preset_name}")
def run_preset(
    preset_name: str,
):
    """Run a configured screener preset."""

    engine = ScreenerEngine()

    try:
        engine.connect()
        engine.load_config()
        engine.load_data()

        if (
            preset_name
            not in engine.config.get(
                "presets",
                {},
            )
        ):
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Screener preset "
                    f"'{preset_name}' not found"
                ),
            )

        result = engine.run_preset(
            preset_name
        )

        if result is None:
            return {
                "preset": preset_name,
                "count": 0,
                "results": [],
            }

        records = make_json_safe(
            result.to_dict(
                orient="records"
            )
        )

        return {
            "preset": preset_name,
            "count": len(records),
            "results": records,
        }

    finally:
        engine.close()

def make_json_safe(records):
    """Convert pandas/NumPy values into JSON-safe values."""

    cleaned = []

    for record in records:
        item = {}

        for key, value in record.items():

            if value is None:
                item[key] = None

            elif isinstance(value, float) and math.isnan(value):
                item[key] = None

            elif hasattr(value, "item"):
                value = value.item()

                if isinstance(value, float) and math.isnan(value):
                    value = None

                item[key] = value

            else:
                item[key] = value

        cleaned.append(item)

    return cleaned
