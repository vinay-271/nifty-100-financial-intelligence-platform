from src.screener.engine import ScreenerEngine


engine = ScreenerEngine(
    db_path="db/nifty100.db",
    config_path="config/screener_config.yaml",
)

engine.connect()
engine.load_config()
engine.load_data()

presets = [
    "quality_compounder",
    "value_pick",
    "growth_accelerator",
    "dividend_champion",
    "debt_free_blue_chip",
    "turnaround_watch",
]

print("\n=== Sprint 3 Day 16 — Preset Results ===")

for preset in presets:
    result = engine.run_preset(preset)

    print(f"{preset:25} : {len(result):2} companies")

engine.close()
