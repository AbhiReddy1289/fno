import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import time

# --- Initialize session state ---
if "balance" not in st.session_state:
    st.session_state.balance = 1_00_00_000  # 1 Cr
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=["Stock", "Type", "Qty", "Price", "Total"])
if "price_data" not in st.session_state:
    st.session_state.price_data = {}

# --- Companies & F&O types ---
companies = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
types_dict = {
    "RELIANCE": ["Option", "Future"],
    "TCS": ["Option", "Future"],
    "INFY": ["Option", "Future"],
    "HDFCBANK": ["Option", "Future"]
}

# --- Select Companies ---
selected_stocks = st.multiselect("Select Companies", companies)

# --- Initialize price data for selected stocks ---
for stock in selected_stocks:
    if stock not in st.session_state.price_data:
        # generate 7 days of hourly dummy prices
        hours = 7 * 24
        base_price = np.random.randint(1000, 5000)
        times = [datetime.now() - timedelta(hours=i) for i in reversed(range(hours))]
        prices = base_price + np.cumsum(np.random.randn(hours)*5)
        st.session_state.price_data[stock] = pd.DataFrame({"Datetime": times, "Price": prices})

# --- Buy section ---
st.sidebar.subheader("Buy Stocks / F&O")
buy_stock = st.sidebar.selectbox("Select Stock", selected_stocks)
if buy_stock:
    buy_type = st.sidebar.selectbox("Select Type", types_dict[buy_stock])
    buy_qty = st.sidebar.number_input("Quantity", min_value=1, value=1)
    buy_price = st.sidebar.number_input("Price per unit", min_value=1, value=int(st.session_state.price_data[buy_stock]["Price"].iloc[-1]))

    if st.sidebar.button("Buy"):
        total_cost = buy_qty * buy_price
        if total_cost > st.session_state.balance:
            st.sidebar.error("Insufficient balance!")
        else:
            st.session_state.balance -= total_cost
            new_entry = pd.DataFrame({
                "Stock": [buy_stock],
                "Type": [buy_type],
                "Qty": [buy_qty],
                "Price": [buy_price],
                "Total": [total_cost]
            })
            st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_entry], ignore_index=True)
            st.sidebar.success(f"Bought {buy_qty} {buy_stock} ({buy_type})")

# --- Portfolio display ---
st.subheader("Portfolio")
st.write(f"Balance: ₹{st.session_state.balance:,.0f}")
st.dataframe(st.session_state.portfolio)

# --- Function to simulate live price movement ---
def simulate_live_prices():
    for stock in selected_stocks:
        if stock in st.session_state.price_data:
            last_price = st.session_state.price_data[stock]['Price'].iloc[-1]
            new_price = last_price + np.random.randn()*5
            new_time = datetime.now()
            st.session_state.price_data[stock] = pd.concat([
                st.session_state.price_data[stock],
                pd.DataFrame({"Datetime": [new_time], "Price": [new_price]})
            ], ignore_index=True)
            # keep only last 7 days of hourly data (~168 points)
            if len(st.session_state.price_data[stock]) > 168:
                st.session_state.price_data[stock] = st.session_state.price_data[stock].iloc[1:]

# --- Live Chart ---
chart_placeholder = st.empty()

while True:
    simulate_live_prices()
    
    combined_df = pd.DataFrame()
    for stock, df in st.session_state.price_data.items():
        temp_df = df.copy()
        temp_df["Stock"] = stock
        combined_df = pd.concat([combined_df, temp_df], ignore_index=True)
    
    fig = px.line(
        combined_df,
        x="Datetime",
        y="Price",
        color="Stock",
        title="Simulated Stock & F&O Prices"
    )
    fig.update_xaxes(rangeslider_visible=True)
    chart_placeholder.plotly_chart(fig, use_container_width=True)
    
    time.sleep(1)
