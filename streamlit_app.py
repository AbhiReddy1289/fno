import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Demo Data for Companies and Trade Details
COMPANIES = [
    {"name": "Alpha Corp", "symbol": "ALPH"},
    {"name": "Beta Ltd", "symbol": "BETA"},
    {"name": "Gamma Inc", "symbol": "GAMM"},
]

TRADING_TYPES = ["Option", "Future"]

# Example trade details per type
TRADE_DETAILS = {
    "Option": ["Call Option", "Put Option"],
    "Future": ["Quarterly Future", "Monthly Future"]
}

# Session state setup (persistence across Streamlit runs)
if "balance" not in st.session_state:
    st.session_state.balance = 1_00_00_000  # 1 crore in INR (1,00,00,000)
if "trades" not in st.session_state:
    st.session_state.trades = []

st.title("Trading Simulation Interface")

# 1. Company Selection (Checklist-style Dropdown)
company_options = [f"{c['name']} ({c['symbol']})" for c in COMPANIES]
company_choice = st.selectbox("Select a Company", ["-- Select Company --"] + company_options)
selected_company = None
if company_choice != "-- Select Company --":
    selected_company = next(c for c in COMPANIES if company_choice.startswith(c["name"]))

# 2. Trading Type (shown after company selection)
selected_type = None
if selected_company:
    selected_type = st.selectbox("Select Trading Type", TRADING_TYPES)

# 3. Trading Detail (shown after trading type selection)
selected_detail = None
if selected_type:
    trade_detail_options = TRADE_DETAILS[selected_type]
    selected_detail = st.selectbox("Select Trade Detail", trade_detail_options)

# 4. Price Input & Buy Action (shown after trade detail selection)
execute_trade = False
price = None
if selected_detail:
    st.write(f"Current Balance: ₹ {st.session_state.balance:,.2f}")
    price = st.number_input("Enter Trade Price (INR)", min_value=1, step=1, value=10000)
    if st.button("Buy"):
        # Validation: Sufficient Funds
        if price > st.session_state.balance:
            st.error("Insufficient funds.")
        else:
            trade_record = {
                "Company": selected_company['name'],
                "Symbol": selected_company['symbol'],
                "Type": selected_type,
                "Detail": selected_detail,
                "Price": price,
                "Timestamp": datetime.now()
            }
            st.session_state.balance -= price
            st.session_state.trades.append(trade_record)
            st.success(f"Trade executed for {selected_company['name']} ({selected_type} - {selected_detail}) at ₹ {price:,.2f}.")

# 5. Trade Log Table
trades_df = pd.DataFrame(st.session_state.trades)
if not trades_df.empty:
    st.markdown("#### Trade Log")
    show_df = trades_df.copy()
    show_df["Timestamp"] = show_df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(show_df)

# 6. Dynamic Balance/Trade Graph (only after first trade)
if not trades_df.empty:
    # Plotting: Balance after each trade
    balances = [1_00_00_000]
    for price in trades_df["Price"]:
        balances.append(balances[-1] - price)
    balances = balances[1:]  # Exclude initial

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trades_df["Timestamp"], 
        y=balances, 
        mode="lines+markers", 
        name="Balance"
    ))
    fig.update_layout(
        title="Account Balance Over Trades",
        xaxis_title="Trade Timestamp",
        yaxis_title="Balance (INR)",
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)
