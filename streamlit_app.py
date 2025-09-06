import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="F&O Simulator", layout="wide")

# --- Initialize session state ---
if "balance" not in st.session_state:
    st.session_state.balance = 1_00_00_000  # 1 crore default
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=[
        "Stock", "Type", "Price", "Quantity", "Invested", "Current Value", "PnL"
    ])
if "price_data" not in st.session_state:
    st.session_state.price_data = {}  # will store simulated price data

# --- Company list ---
COMPANIES = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

# --- Dummy price generator ---
def generate_dummy_data(stock):
    now = datetime.now()
    times = [now - timedelta(hours=i) for i in range(168)][::-1]  # last 7 days, 1-hour interval
    base_price = np.random.randint(1000, 5000)
    prices = base_price + np.cumsum(np.random.randn(168)*5)  # small random walk
    df = pd.DataFrame({"Datetime": times, "Price": prices})
    return df

# Initialize price data for selected stocks
selected_stocks = st.sidebar.multiselect("Select Companies", COMPANIES)
for stock in selected_stocks:
    if stock not in st.session_state.price_data:
        st.session_state.price_data[stock] = generate_dummy_data(stock)

# --- Buy section ---
st.subheader("Buy Stocks / F&O")
if selected_stocks:
    buy_stock = st.selectbox("Select Stock", selected_stocks)
    buy_type = st.selectbox("Select Type", ["Stock", "Option", "Future"])
    
    option_type = None
    if buy_type == "Option":
        option_type = st.selectbox("Option Type", ["Call", "Put"])
    
    price = st.number_input("Enter Price", min_value=0.0, step=0.1)
    quantity = st.number_input("Enter Quantity", min_value=1, step=1)
    
    if st.button("Buy"):
        invested_amount = price * quantity
        if invested_amount > st.session_state.balance:
            st.error("Insufficient balance!")
        else:
            st.session_state.balance -= invested_amount
            st.session_state.portfolio.loc[len(st.session_state.portfolio)] = [
                buy_stock,
                f"{buy_type}{' '+option_type if option_type else ''}",
                price,
                quantity,
                invested_amount,
                invested_amount,  # initially current value same as invested
                0  # initial PnL
            ]
            st.success(f"Bought {quantity} of {buy_stock} {buy_type} for {invested_amount}")

# --- Update portfolio current value ---
for idx, row in st.session_state.portfolio.iterrows():
    if row["Stock"] in st.session_state.price_data:
        latest_price = st.session_state.price_data[row["Stock"]]["Price"].iloc[-1]
        st.session_state.portfolio.at[idx, "Current Value"] = latest_price * row["Quantity"]
        st.session_state.portfolio.at[idx, "PnL"] = (latest_price - row["Price"]) * row["Quantity"]

# --- Show balance and portfolio ---
st.sidebar.subheader("Balance")
st.sidebar.write(f"₹ {st.session_state.balance:,.2f}")

st.subheader("Portfolio")
st.dataframe(st.session_state.portfolio)

# --- Plot graph ---
st.subheader("Real-Time Stock & F&O Prices")
chart_placeholder = st.empty()

def update_chart():
    combined_df = pd.DataFrame()
    for stock, df in st.session_state.price_data.items():
        if df.empty or 'Datetime' not in df.columns or 'Price' not in df.columns:
            continue
        temp_df = df.copy()
        temp_df['Stock'] = stock
        combined_df = pd.concat([combined_df, temp_df], ignore_index=True)
    
    if combined_df.empty:
        st.warning("No data to plot yet. Please select stocks.")
        return
    
    fig = px.line(
        combined_df,
        x='Datetime',
        y='Price',
        color='Stock',
        title="Simulated Stock & F&O Prices"
    )
    fig.update_xaxes(rangeslider_visible=True)
    chart_placeholder.plotly_chart(fig, use_container_width=True)

update_chart()
