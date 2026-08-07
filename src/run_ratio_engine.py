from src.analytics.ratio_engine import RatioEngine

engine = RatioEngine()

engine.connect()

ratios = engine.build_ratio_table()

engine.save_ratio_table(ratios)

engine.populate_financial_ratios()

engine.export_edge_cases()

engine.close()

print("Ratio Engine completed successfully.")
