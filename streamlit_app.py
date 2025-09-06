import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Dynamic F&O Simulator", layout="wide")

# ----------------------
# Initialize Session State
# ----------------------
if 'balance' not in st.session_state:
    st.session_state.balance = 1_00_00_000  # 1 crore
if 'portfolio' not in st.session_state:
    # Structure: {stock: [{'instrument':'FUT/CALL/PUT', 'qty':x, 'price':y}]}
    st.session_state.portfolio = {}
if 'tick' not in st.session_state:
    st.session_state.tick = 0

# ----------------------
# Generate Dummy Stock Data
# ----------------------
stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
hours_data = 178

def generate_data():
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_data)
    date_range = pd.date_range(start=start_time, end=end_time, freq='H')
    data = {}
    for stock in stocks:
        price = 100 + np.cumsum(np.random.randn(len(date_range)))
        df = pd.DataFrame({'Datetime': date_range, 'Price': price})
        data[stock] = df
    return data

all_data = generate_data()

# ----------------------
# Sidebar - Portfolio & Balance
# ----------------------
st.sidebar.header("Account Info")
st.sidebar.write(f"**Balance:** ₹{st.session_state.balance:,.0f}")
st.sidebar.header("Portfolio")
if st.session_state.portfolio:
    for s, holdings in st.session_state.portfolio.items():
        for h in holdings:
            st.sidebar.write(f"{s} | {h['instrument']} | Qty: {h['qty']} | Invested: ₹{h['price']*h['qty']:.0f}")

# ----------------------
# Stock Selection
# ----------------------
st.sidebar.header("Select Stocks to Trade")
selected_stocks = st.sidebar.multiselect("Choose Stocks", stocks)

# ----------------------
# Trading Inputs
# ----------------------
for stock in selected_stocks:
    st.sidebar.write(f"**{stock}**")
    instrument = st.sidebar.radio(f"Instrument for {stock}", ['FUT', 'CALL', 'PUT'], key=f"{stock}_inst")
    qty = st.sidebar.number_input(f"Qty for {stock}-{instrument}", min_value=1, value=1, key=f"{stock}_qty")
    price = st.sidebar.number_input(f"Price per unit for {stock}-{instrument}", min_value=1.0, value=float(all_data[stock]['Price'].iloc[-1]), key=f"{stock}_price")
    
    if st.sidebar.button(f"Buy {stock}-{instrument}"):
        total_cost = price * qty
        if st.session_state.balance >= total_cost:
            st.session_state.balance -= total_cost
            st.session_state.portfolio.setdefault(stock, []).append({
                'instrument': instrument,
                'qty': qty,
                'price': price
            })
        else:
            st.sidebar.warning("Insufficient balance!")

# ----------------------
# Real-time Simulation
# ----------------------
st.title("Dynamic F&O Simulator")
chart_placeholder = st.empty()

while True:
    tick = st.session_state.tick
    combined_df = pd.DataFrame()
    
    for stock in selected_stocks:
        df = all_data[stock]
        rotated_df = df.iloc[tick:tick+168].copy()  # Simulate 7 days
        rotated_df['Stock'] = stock
        combined_df = pd.concat([combined_df, rotated_df])

    fig = px.line(combined_df, x='Datetime', y='Price', color='Stock',
                  title='Simulated Stock & F&O Prices')
    fig.update_xaxes(rangeslider_visible=True)
    chart_placeholder.plotly_chart(fig, use_container_width=True)

    # Update Portfolio Value & P&L
    total_value = st.session_state.balance
    pnl_details = {}
    for stock, holdings in st.session_state.portfolio.items():
        current_price = combined_df[combined_df['Stock']==stock]['Price'].iloc[-1]
        for h in holdings:
            value = h['qty'] * current_price
            pnl_details[f"{stock}-{h['instrument']}"] = value
            total_value += value

    st.sidebar.write("### P&L Details")
    st.sidebar.write(pnl_details)
    st.sidebar.write(f"**Total Account Value:** ₹{total_value:,.0f}")

    st.session_state.tick += 1
    if st.session_state.tick + 168 > hours_data:
        st.session_state.tick = 0

    time.sleep(1)
