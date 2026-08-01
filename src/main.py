from etl.database_loader import DatabaseLoader

# profit_loss = pd.read_csv(self.cleaned_data_path / "profitandloss.csv")
# print(profit_loss["year"].unique())

loader = DatabaseLoader()

loader.connect()
loader.create_tables()
loader.clear_tables()

loader.load_companies()
loader.load_profitandloss()
loader.load_balancesheet()
loader.load_cashflow()
loader.load_analysis()
loader.load_documents()
loader.load_prosandcons()
loader.load_stock_prices()
loader.load_financial_ratios()
loader.load_market_cap()
loader.load_market_cap()
loader.load_peer_groups()
loader.load_sectors()

loader.export_load_audit()

loader.close()
