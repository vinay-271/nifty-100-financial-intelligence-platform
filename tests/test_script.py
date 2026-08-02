import pandas as pd

df = pd.read_csv("data/output/validation_failures.csv")

print(df.groupby(["severity"]).size())
