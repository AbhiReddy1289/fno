import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

# --- INITIAL SETUP ---
st.set_page_config(page_title="F&O Trading Simulator", layout="wide")
st.title("F&O Trading Simulator")

# Initialize session state
if "balance" not in st.session_state:
    st.session_state.balance = 1_00_00_000  # 1 crore
if "holdings" not in st.session_state:
    st.session_state.holdings = pd.DataFrame(columns=["Stock", "Type", "OptionType", "Price", "Quantity", "CurrentValue"])
if "price_data" not in st.session_state:
    st.session_state.price_data = {}

# --- STOCK SELECTION ---
stocks_available = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "ICICIBANK"]
selected_stocks = st.multiselect("Select Stocks", options=stocks_available)

# --- SIMULATED PRICE DATA ---
def generate_dummy_data(stock):
    # Simulate 7 days of 1-hour interval data
    hours = 7*24
    times = pd.date_range(end=pd.Timestamp.now(), periods=hours, freq="H")
    base_price = np.random.randint(1000, 3000)
    prices = base_price + np.cumsum(np.random.randn(hours)*10)
    return pd.DataFrame({"Datetime": times, "Price": prices})

for stock in selected_stocks:
    if stock not in st.session_state.price_data:
        st.session_state.price_data[stock] = generate_dummy_data(stock)

# --- BUY / SELL INTERFACE ---
st.sidebar.subheader("Buy Stock / F&O")
stock_to_buy = st.sidebar.selectbox("Select Stock", options=selected_stocks if selected_stocks else [])
if stock_to_buy:
    trade_type = st.sidebar.radio("Trade Type", ["Stock", "Futures", "Options"])
    option_type = None
    if trade_type == "Options":
        option_type = st.sidebar.radio("Option Type", ["Call", "Put"])
    
    buy_price = st.sidebar.number_input("Price per unit", min_value=1.0, step=1.0)
    quantity = st.sidebar.number_input("Quantity", min_value=1, step=1)
    
    if st.sidebar.button("Buy"):
        total_cost = buy_price * quantity
        if total_cost > st.session_state.balance:
            st.sidebar.error("Insufficient balance!")
        else:
            st.session_state.balance -= total_cost
            st.session_state.holdings = pd.concat([
                st.session_state.holdings,
                pd.DataFrame([{
                    "Stock": stock_to_buy,
                    "Type": trade_type,
                    "OptionType": option_type if option_type else "",
                    "Price": buy_price,
                    "Quantity": quantity,
                    "CurrentValue": total_cost
                }])
            ], ignore_index=True)
            st.sidebar.success(f"Bought {quantity} units of {stock_to_buy} at ₹{buy_price} each.")

# --- HOLDINGS & BALANCE DISPLAY ---
st.subheader("Portfolio")
holdings_df = st.session_state.holdings.copy()

# Update current value based on latest price
for idx, row in holdings_df.iterrows():
    latest_price = st.session_state.price_data[row.Stock]["Price"].iloc[-1]
    holdings_df.at[idx, "CurrentValue"] = latest_price * row.Quantity

st.dataframe(holdings_df)
st.subheader(f"Available Balance: ₹{st.session_state.balance:,.2f}")

# --- PLOT REAL-TIME GRAPH ---
st.subheader("Live Stock & F&O Prices")
chart_placeholder = st.empty()

def update_chart():
    combined_df = pd.DataFrame()
    for stock, df in st.session_state.price_data.items():
        temp_df = df.copy()
        temp_df['Stock'] = stock
        combined_df = pd.concat([combined_df, temp_df], ignore_index=True)
    fig = px.line(combined_df, x='Datetime', y='Price', color='Stock', title="Simulated Stock & F&O Prices")
    fig.update_xaxes(rangeslider_visible=True)
    chart_placeholder.plotly_chart(fig, use_container_width=True)

# Auto-refresh every second
while True:
    # Append new price points to simulate live market
    for stock in selected_stocks:
        last_price = st.session_state.price_data[stock]["Price"].iloc[-1]
        new_price = last_price + np.random.randn()*5
        new_row = pd.DataFrame({"Datetime": [pd.Timestamp.now()], "Price": [new_price]})
        st.session_state.price_data[stock] = pd.concat([st.session_state.price_data[stock], new_row], ignore_index=True)
    update_chart()
    time.sleep(1)
