import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="F&O Simulator", layout="wide")

# -----------------------
# Dummy Data Preparation
# -----------------------
stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
hours_data = 178  # number of hours to simulate

def generate_dummy_data():
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_data)
    date_range = pd.date_range(start=start_time, end=end_time, freq='H')
    all_data = {}
    for stock in stocks:
        price = 100 + np.cumsum(np.random.randn(len(date_range)))
        df = pd.DataFrame({'Datetime': date_range, 'Price': price})
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        all_data[stock] = df
    return all_data

all_data = generate_dummy_data()

# -----------------------
# Sidebar - Portfolio & Trading
# -----------------------
st.sidebar.header("Dummy Account")
if 'balance' not in st.session_state:
    st.session_state.balance = 1_00_00_000  # 1 crore
if 'portfolio' not in st.session_state:
    # portfolio structure: {stock: {'FUT':0, 'CALL':0, 'PUT':0}}
    st.session_state.portfolio = {stock: {'FUT':0, 'CALL':0, 'PUT':0} for stock in stocks}

st.sidebar.write(f"**Balance:** ₹{st.session_state.balance:,.0f}")
st.sidebar.write("### Portfolio")
st.sidebar.write(st.session_state.portfolio)

st.sidebar.header("Select Stocks to Trade")
selected_stocks = [stock for stock in stocks if st.sidebar.checkbox(stock, value=True)]

# -----------------------
# Trading Buttons
# -----------------------
for stock in selected_stocks:
    st.sidebar.write(f"**{stock}**")
    option = st.sidebar.radio(f"{stock} Instrument", ['FUT', 'CALL', 'PUT'], index=0)
    col1, col2 = st.sidebar.columns(2)
    current_price = all_data[stock]['Price'].iloc[-1]
    
    if col1.button(f"Buy {option} {stock}"):
        if st.session_state.balance >= current_price:
            st.session_state.portfolio[stock][option] += 1
            st.session_state.balance -= current_price
    if col2.button(f"Sell {option} {stock}"):
        if st.session_state.portfolio[stock][option] > 0:
            st.session_state.portfolio[stock][option] -= 1
            st.session_state.balance += current_price

# -----------------------
# Real-time Simulation
# -----------------------
st.title("F&O Simulator - Real-time Data & P&L")
chart_placeholder = st.empty()

if 'tick' not in st.session_state:
    st.session_state.tick = 0

while True:
    tick = st.session_state.tick
    combined_df = pd.DataFrame()

    for stock in selected_stocks:
        df = all_data[stock]
        rotated_df = df.iloc[tick:tick+168]  # 7 days data
        rotated_df = rotated_df.copy()
        rotated_df['Stock'] = stock
        combined_df = pd.concat([combined_df, rotated_df])

    fig = px.line(combined_df, x='Datetime', y='Price', color='Stock',
                  title='Simulated F&O Prices', markers=False)
    fig.update_xaxes(rangeslider_visible=True)
    chart_placeholder.plotly_chart(fig, use_container_width=True)

    # -----------------------
    # Real-time P&L
    # -----------------------
    total_value = st.session_state.balance
    pnl_details = {}
    for stock in selected_stocks:
        current_price = combined_df[combined_df['Stock']==stock]['Price'].iloc[-1]
        for inst in ['FUT','CALL','PUT']:
            qty = st.session_state.portfolio[stock][inst]
            value = qty * current_price
            pnl_details[f"{stock}-{inst}"] = value
            total_value += value
    st.sidebar.write("### P&L Details")
    st.sidebar.write(pnl_details)
    st.sidebar.write(f"**Total Account Value:** ₹{total_value:,.0f}")

    st.session_state.tick += 1
    if st.session_state.tick + 168 > hours_data:
        st.session_state.tick = 0

    time.sleep(1)
