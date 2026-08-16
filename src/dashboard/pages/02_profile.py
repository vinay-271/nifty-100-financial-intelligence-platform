import pandas as pd
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_valuation,
    get_sectors,
)


st.title("Company Profile")

companies = get_companies()
sectors = get_sectors()

if companies.empty:
    st.warning("No company data available.")
    st.stop()


# -------------------------------------------------------------------
# Company search / selector
# -------------------------------------------------------------------

search = st.text_input(
    "Search Company",
    placeholder="Type company name or ticker...",
)

if search:
    search_text = search.strip().lower()

    filtered_companies = companies[
        companies["id"].str.lower().str.contains(search_text, na=False)
        | companies["company_name"].str.lower().str.contains(
            search_text,
            na=False,
        )
    ]
else:
    filtered_companies = companies

if filtered_companies.empty:
    st.warning("Ticker not found — please try another.")
    st.stop()

ticker = st.selectbox(
    "Select Company",
    filtered_companies["id"].tolist(),
)

company = companies[
    companies["id"] == ticker
].iloc[0]

sector_row = sectors[
    sectors["company_id"] == ticker
]

ratios = get_ratios(ticker)

if ratios.empty:
    st.warning("No financial ratio data available.")
    st.stop()

annual_ratios = ratios[
    ratios["year"].astype(str).str.match(
        r"^[A-Za-z]{3}\s\d{4}$"
    )
].copy()

if annual_ratios.empty:
    latest = ratios.iloc[0]
else:
    annual_ratios["fiscal_year"] = (
        annual_ratios["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .astype(int)
    )

    latest = annual_ratios.loc[
        annual_ratios["fiscal_year"].idxmax()
    ]

if sector_row.empty:
    sector_name = "N/A"
    industry_name = "N/A"
else:
    sector_name = sector_row.iloc[0]["sector"]
    industry_name = sector_row.iloc[0]["industry"]

# -------------------------------------------------------------------
# Company header
# -------------------------------------------------------------------

st.subheader(company["company_name"])

st.caption(
    f"Sector: {sector_name}  •  Industry: {industry_name}  •  "
    f"NSE Ticker: {ticker}"
)

if pd.notna(company.get("about_company")):
    st.write(company["about_company"])


# -------------------------------------------------------------------
# Company KPIs
# -------------------------------------------------------------------

st.divider()
st.subheader("Key Financial Metrics")

cols = st.columns(6)

kpis = [
    ("ROE", "return_on_equity_pct", "%"),
    ("ROCE", "return_on_capital_employed_pct", "%"),
    ("Net Profit Margin", "net_profit_margin_pct", "%"),
    ("Debt / Equity", "debt_to_equity", ""),
    ("Revenue CAGR 5yr", "revenue_cagr_5yr", "%"),
    ("FCF", "free_cash_flow_cr", " Cr"),
]

for col, (label, column, suffix) in zip(cols, kpis):
    value = latest.get(column)

    if pd.isna(value):
        display = "N/A"
    elif column == "free_cash_flow_cr":
        display = f"₹{float(value):,.0f} Cr"
    elif suffix == "%":
        display = f"{float(value):.2f}%"
    else:
        display = f"{float(value):.2f}{suffix}"

    with col:
        st.metric(label, display)


# -------------------------------------------------------------------
# Financial ratios
# -------------------------------------------------------------------

st.divider()
st.subheader("Financial Ratios")

ratios = get_ratios(ticker)

if ratios.empty:
    st.info("No financial ratio data available.")
else:
    # Use the latest annual financial-ratio record.
    # TTM currently does not contain ROE, ROCE, or D/E values.
    annual_ratios = ratios[
        ratios["year"].astype(str).str.match(r"^[A-Za-z]{3}\s\d{4}$")
    ].copy()

    if annual_ratios.empty:
        latest = ratios.iloc[-1]
    else:
        annual_ratios["fiscal_year"] = (
            annual_ratios["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .astype(int)
        )

        latest = annual_ratios.loc[
            annual_ratios["fiscal_year"].idxmax()
        ]

    ratio_columns = [
        (
            "Net Profit Margin",
            "net_profit_margin_pct",
            "%",
        ),
        (
            "Operating Profit Margin",
            "operating_profit_margin_pct",
            "%",
        ),
        (
            "ROE",
            "return_on_equity_pct",
            "%",
        ),
        (
            "ROCE",
            "return_on_capital_employed_pct",
            "%",
        ),
        (
            "Debt / Equity",
            "debt_to_equity",
            "",
        ),
        (
            "Interest Coverage",
            "interest_coverage",
            "x",
        ),
    ]

    cols = st.columns(3)

    for i, (label, column, suffix) in enumerate(
        ratio_columns
    ):
        value = latest.get(column)

        if value is None:
            display = "N/A"
        else:
            try:
                display = f"{float(value):.2f}{suffix}"
            except (TypeError, ValueError):
                display = "N/A"

        with cols[i % 3]:
            st.metric(label, display)


# -------------------------------------------------------------------
# Profit & Loss
# -------------------------------------------------------------------

st.divider()
st.subheader("Profit & Loss")

pl = get_pl(ticker)

if pl.empty:
    st.info("No profit & loss data available.")
else:
    display_columns = [
        column
        for column in [
            "year",
            "sales",
            "operating_profit",
            "net_profit",
            "eps",
            "dividend_payout",
        ]
        if column in pl.columns
    ]

    st.dataframe(
        pl[display_columns],
        use_container_width=True,
        hide_index=True,
    )

# -------------------------------------------------------------------
# Revenue & Net Profit Trend
# -------------------------------------------------------------------

st.divider()
st.subheader("Revenue & Net Profit Trend")

if pl.empty:
    st.info("No profit & loss data available.")
else:
    chart_data = pl[
        ["year", "sales", "net_profit"]
    ].copy()

    chart_data = chart_data.dropna(
        subset=["sales", "net_profit"]
    )

    chart_data = chart_data.rename(
        columns={
            "sales": "Revenue",
            "net_profit": "Net Profit",
        }
    )

    chart_data = chart_data.set_index("year")

    st.line_chart(
        chart_data,
        use_container_width=True,
    )

# -------------------------------------------------------------------
# Balance Sheet
# -------------------------------------------------------------------

st.divider()
st.subheader("Balance Sheet")

bs = get_bs(ticker)

if bs.empty:
    st.info("No balance sheet data available.")
else:
    display_columns = [
        column
        for column in [
            "year",
            "equity_capital",
            "reserves",
            "borrowings",
            "total_liabilities",
            "fixed_assets",
            "investments",
            "total_assets",
        ]
        if column in bs.columns
    ]

    st.dataframe(
        bs[display_columns],
        use_container_width=True,
        hide_index=True,
    )

# -------------------------------------------------------------------
# Balance Sheet Trend
# -------------------------------------------------------------------

st.divider()
st.subheader("Balance Sheet Trend")

if bs.empty:
    st.info("No balance sheet data available.")
else:
    balance_data = bs[
        ["year", "reserves", "borrowings", "total_assets"]
    ].copy()

    balance_data = balance_data.dropna(
        subset=["reserves", "borrowings", "total_assets"]
    )

    balance_data = balance_data.rename(
        columns={
            "reserves": "Reserves",
            "borrowings": "Borrowings",
            "total_assets": "Total Assets",
        }
    )

    balance_data = balance_data.set_index("year")

    st.line_chart(
        balance_data,
        use_container_width=True,
    )

# -------------------------------------------------------------------
# Cash Flow
# -------------------------------------------------------------------

st.divider()
st.subheader("Cash Flow")

cf = get_cf(ticker)

if cf.empty:
    st.info("No cash flow data available.")
else:
    display_columns = [
        column
        for column in [
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ]
        if column in cf.columns
    ]

    st.dataframe(
        cf[display_columns],
        use_container_width=True,
        hide_index=True,
    )

# -------------------------------------------------------------------
# Cash Flow Trend
# -------------------------------------------------------------------

st.divider()
st.subheader("Cash Flow Trend")

if cf.empty:
    st.info("No cash flow data available.")
else:
    cash_flow_data = cf[
        [
            "year",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ]
    ].copy()

    cash_flow_data = cash_flow_data.dropna(
        subset=[
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ]
    )

    cash_flow_data = cash_flow_data.rename(
        columns={
            "operating_activity": "Operating Cash Flow",
            "investing_activity": "Investing Cash Flow",
            "financing_activity": "Financing Cash Flow",
            "net_cash_flow": "Net Cash Flow",
        }
    )

    cash_flow_data = cash_flow_data.set_index("year")

    st.line_chart(
        cash_flow_data,
        use_container_width=True,
    )

# -------------------------------------------------------------------
# Valuation
# -------------------------------------------------------------------

st.divider()
st.subheader("Valuation")

valuation = get_valuation(ticker)

if valuation.empty:
    st.info("No valuation data available.")
else:
    display_columns = [
        column
        for column in [
            "year",
            "market_cap_cr",
            "enterprise_value_cr",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ]
        if column in valuation.columns
    ]

    st.dataframe(
        valuation[display_columns],
        use_container_width=True,
        hide_index=True,
    )

# -------------------------------------------------------------------
# Valuation Trend
# -------------------------------------------------------------------

st.divider()
st.subheader("Valuation Trend")

if valuation.empty:
    st.info("No valuation data available.")
else:
    valuation_data = valuation[
        [
            "year",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ]
    ].copy()

    valuation_data = valuation_data.dropna(
        subset=[
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ],
        how="all",
    )

    valuation_data = valuation_data.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
            "dividend_yield_pct": "Dividend Yield %",
        }
    )

    valuation_data = valuation_data.set_index("year")

    st.line_chart(
        valuation_data,
        use_container_width=True,
    )

# -------------------------------------------------------------------
# Pros & Cons
# -------------------------------------------------------------------

st.divider()
st.subheader("Investment Snapshot")

pros = []
cons = []

roe = latest.get("return_on_equity_pct")
roce = latest.get("return_on_capital_employed_pct")
de = latest.get("debt_to_equity")
npm = latest.get("net_profit_margin_pct")
revenue_cagr = latest.get("revenue_cagr_5yr")
fcf = latest.get("free_cash_flow_cr")

if pd.notna(roe):
    if roe >= 15:
        pros.append(f"Strong ROE of {roe:.2f}%")
    elif roe < 10:
        cons.append(f"Low ROE of {roe:.2f}%")

if pd.notna(roce):
    if roce >= 15:
        pros.append(f"Healthy ROCE of {roce:.2f}%")
    elif roce < 10:
        cons.append(f"Low ROCE of {roce:.2f}%")

if pd.notna(de):
    if de <= 1:
        pros.append(f"Moderate leverage with D/E of {de:.2f}")
    elif de > 2:
        cons.append(f"High leverage with D/E of {de:.2f}")

if pd.notna(npm):
    if npm >= 15:
        pros.append(f"Strong net margin of {npm:.2f}%")
    elif npm < 5:
        cons.append(f"Low net margin of {npm:.2f}%")

if pd.notna(revenue_cagr):
    if revenue_cagr >= 10:
        pros.append(f"Healthy 5-year revenue CAGR of {revenue_cagr:.2f}%")
    elif revenue_cagr < 0:
        cons.append(f"Declining 5-year revenue CAGR of {revenue_cagr:.2f}%")

if pd.notna(fcf):
    if fcf > 0:
        pros.append("Positive free cash flow")
    else:
        cons.append("Negative free cash flow")


col1, col2 = st.columns(2)

with col1:
    st.markdown("### Pros")

    if pros:
        for item in pros:
            st.success(f"✓ {item}")
    else:
        st.info("No significant strengths identified.")

with col2:
    st.markdown("### Cons")

    if cons:
        for item in cons:
            st.error(f"⚠ {item}")
    else:
        st.info("No significant weaknesses identified.")
