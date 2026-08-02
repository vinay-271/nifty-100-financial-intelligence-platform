from src.etl.validator import DataValidator

validator = DataValidator()

validator.connect()
validator.validate()
validator.close()

print("Validation completed successfully.")
