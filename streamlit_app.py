import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import time

# ----------------------
# Page Config
# ----------------------
st.set_page_config(page_title="F&O Live Simulator", layout="wide")

# ----------------------
# Auto-refresh every 2 seconds
# ----------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > 2:
    st.session_state.last_refresh = time.time()
    st.experimental_rerun()

# ----------------------
# Sidebar Settings
# ----------------------
st.sidebar.header("Simulator Settings")
symbol = st.sidebar.text_input("Stock Symbol", value="TCS.NS")
days = st.sidebar.slider("Number of Days to Simulate", min_value=5, max_value=30, value=10)
volatility_futures = st.sidebar.slider("Futures Volatility (%)", min_value=0.1, max_value=5.0, value=1.0)
volatility_options = st.sidebar.slider("Options Volatility (%)", min_value=0.1, max_value=10.0, value=2.0)

# ----------------------
# Fetch Historical Data
# ----------------------
@st.cache_data
def get_stock_data(symbol, days):
    end = datetime.today()
    start = end - timedelta(days=days*3)  # buffer for weekends
    data = yf.download(symbol, start=start, end=end, progress=False)
    if data.empty:
        return pd.DataFrame()
    data = data.reset_index()[["Date", "Close"]].tail(days)
    data.rename(columns={"Close": "Stock Price"}, inplace=True)
    return data

stock_df = get_stock_data(symbol, days)

# ----------------------
# Simulate F&O Prices
# ----------------------
def simulate_fo(stock_df, vol_f, vol_o):
    fo_df = stock_df.copy()
    np.random.seed(int(time.time()))
    fo_df["Futures"] = fo_df["Stock Price"] * (1 + np.random.normal(0, vol_f/100, len(fo_df)))
    fo_df["Options"] = fo_df["Stock Price"] * (1 + np.random.normal(0, vol_o/100, len(fo_df)))
    return fo_df

fo_df = simulate_fo(stock_df, volatility_futures, volatility_options)

# ----------------------
# Plot Chart
# ----------------------
if not fo_df.empty:
    fig = px.line(
        fo_df,
        x="Date",
        y=["Stock Price", "Futures", "Options"],
        title=f"{symbol} - Live F&O Simulation",
        labels={"value": "Price", "variable": "Type"},
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data found for this symbol or time range.")

# ----------------------
# Footer
# ----------------------
st.caption("Live F&O Prices are simulated for demonstration. Not financial advice.")
