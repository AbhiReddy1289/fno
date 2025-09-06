import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import time
import plotly.graph_objs as go

st.set_page_config(layout="wide")
st.title("F&O Simulator (Paper Trading)")

# -------------------------------
# User Config
# -------------------------------
STOCKS = ["TCS.NS", "INFY.NS", "RELIANCE.NS"]  # Add more
TIME_RANGES = {
    "1 Minute": 1,
    "5 Minutes": 5,
    "15 Minutes": 15,
    "1 Hour": 60,
    "6 Hours": 360,
    "1 Day": 1440,
}

# -------------------------------
# Sidebar Options
# -------------------------------
st.sidebar.header("Select Stocks")
selected_stocks = st.sidebar.multiselect("Stocks to Track", STOCKS, default=STOCKS[:1])

st.sidebar.header("Time Range")
selected_range_label = st.sidebar.selectbox("Zoom Level", list(TIME_RANGES.keys()))
selected_range = TIME_RANGES[selected_range_label]

# Paper trading state
if "balance" not in st.session_state:
    st.session_state.balance = 100000  # Dummy money
if "positions" not in st.session_state:
    st.session_state.positions = {stock: 0 for stock in STOCKS}

st.sidebar.write(f"💰 Balance: ₹{st.session_state.balance:.2f}")

# -------------------------------
# Load / Cache Historical Data
# -------------------------------
@st.cache_data
def load_data(ticker):
    # Last 7 days of 1-hour data
    df = yf.download(ticker, period="7d", interval="1h")
    df = df.reset_index()
    return df[["Datetime", "Open", "High", "Low", "Close"]]

data_dict = {stock: load_data(stock) for stock in selected_stocks}

# -------------------------------
# Paper Trading Buttons
# -------------------------------
st.sidebar.header("Trade")
for stock in selected_stocks:
    col1, col2 = st.sidebar.columns(2)
    if col1.button(f"Buy {stock}"):
        current_price = data_dict[stock]["Close"].iloc[-1]
        st.session_state.balance -= current_price
        st.session_state.positions[stock] += 1
    if col2.button(f"Sell {stock}"):
        if st.session_state.positions[stock] > 0:
            current_price = data_dict[stock]["Close"].iloc[-1]
            st.session_state.balance += current_price
            st.session_state.positions[stock] -= 1

st.sidebar.write("Positions:")
for stock in selected_stocks:
    st.sidebar.write(f"{stock}: {st.session_state.positions[stock]} shares")

# -------------------------------
# Simulate Live Data
# -------------------------------
st.header("Live Stock Charts")
charts = {stock: st.empty() for stock in selected_stocks}

# Rotate data every second
rot_index = 0
while True:
    for stock in selected_stocks:
        df = data_dict[stock]
        # Circular rotation
        df_live = pd.concat([df.iloc[rot_index:], df.iloc[:rot_index]])
        df_display = df_live.tail(selected_range)  # Zoom
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_display["Datetime"],
            open=df_display["Open"],
            high=df_display["High"],
            low=df_display["Low"],
            close=df_display["Close"]
        ))
        fig.update_layout(height=400, xaxis_rangeslider_visible=False)
        charts[stock].plotly_chart(fig, use_container_width=True)
    
    rot_index = (rot_index + 1) % len(df)
    time.sleep(1)
