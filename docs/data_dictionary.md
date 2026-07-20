| Dataset | Primary Key | Foreign Key | Description |
|----------|-------------|-------------|-------------|
| companies | id | - | Company master information |
| profitandloss | id | company_id | Annual profit & loss statements |
| balancesheet | id | company_id | Annual balance sheet |
| cashflow | id | company_id | Annual cash flow |
| analysis | id | company_id | Financial analysis metrics |
| documents | id | company_id | Annual reports and company documents |
| prosandcons | id | company_id | Company strengths and weaknesses |
| financial_ratios | id | company_id | Financial ratio history |
| market_cap | id | company_id | Market capitalization history |
| peer_groups | id | company_id | Peer company mapping |
| sectors | id | - | Sector master data |
| stock_prices | id | company_id | Historical stock prices |
