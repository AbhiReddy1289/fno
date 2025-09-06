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
# Let's assume 5 stocks for simulation
stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
hours_data = 178  # number of hours to simulate

# Generate dummy historical data
def generate_dummy_data():
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours_data)
    date_range = pd.date_range(start=start_time, end=end_time, freq='H')
    
    all_data = {}
    for stock in stocks:
        # random walk for price simulation
        price = 100 + np.cumsum(np.random.randn(len(date_range)))  
        df = pd.DataFrame({'Datetime': date_range, 'Price': price})
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        all_data[stock] = df
    return all_data

all_data = generate_dummy_data()

# -----------------------
# Sidebar - Stock Selection
# -----------------------
st.sidebar.header("Select Stocks to Monitor")
selected_stocks = [stock for stock in stocks if st.sidebar.checkbox(stock, value=True)]

# -----------------------
# Trading Simulator Variables
# -----------------------
# Dummy portfolio to track trades
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {stock: 0 for stock in stocks}

# -----------------------
# Real-time simulation
# -----------------------
st.title("F&O Simulator - Real-time Data")
chart_placeholder = st.empty()
portfolio_placeholder = st.sidebar.empty()

# Rotating index for real-time simulation
if 'tick' not in st.session_state:
    st.session_state.tick = 0

while True:
    tick = st.session_state.tick
    combined_df = pd.DataFrame()

    for stock in selected_stocks:
        df = all_data[stock]
        # Rotate data to simulate 7-day window
        rotated_df = df.iloc[tick:tick+168]  # 168 hours ~ 7 days
        rotated_df = rotated_df.copy()
        rotated_df['Stock'] = stock
        combined_df = pd.concat([combined_df, rotated_df])
    
    # Plot using Plotly
    fig = px.line(combined_df, x='Datetime', y='Price', color='Stock',
                  title='Simulated F&O Prices', markers=False)
    fig.update_xaxes(rangeslider_visible=True)
    chart_placeholder.plotly_chart(fig, use_container_width=True)
    
    # Update portfolio display
    portfolio_placeholder.write("### Dummy Portfolio")
    portfolio_placeholder.write(st.session_state.portfolio)

    # Increment tick to rotate data
    st.session_state.tick += 1
    if st.session_state.tick + 168 > hours_data:
        st.session_state.tick = 0

    time.sleep(1)  # 1-second refresh
