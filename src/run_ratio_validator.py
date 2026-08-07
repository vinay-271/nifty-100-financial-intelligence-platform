from src.analytics.ratio_validator import RatioValidator

validator = RatioValidator()

validator.connect()

validator.validate()

validator.close()

print("Ratio validation completed.")
