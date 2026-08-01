import pandas as pd

print(pd.read_csv("data/cleaned/peer_groups.csv").columns.tolist())
print(pd.read_csv("data/cleaned/sectors.csv").columns.tolist())
