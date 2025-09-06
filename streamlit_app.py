import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# -----------------------------
# Initialize session state
# -----------------------------
if 'balance' not in st.session_state:
    st.session_state.balance = 100_00_000  # 1 Cr

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=['Company', 'Type', 'Invested Amount', 'Units', 'Current Value'])

if 'prices' not in st.session_state:
    st.session_state.prices = {}

# -----------------------------
# Company list
# -----------------------------
companies = ["TCS", "INFY", "RELIANCE", "HDFC", "ICICI", "SBIN", "LT", "WIPRO"]

st.set_page_config(page_title="F&O Simulator", layout="wide")
st.title("F&O Simulator")

# -----------------------------
# Company Selection
# -----------------------------
selected_companies = st.multiselect("Select Companies to Trade", options=companies)

# -----------------------------
# Buy Section
# -----------------------------
st.subheader("Buy F&O")

with st.form("buy_form"):
    if selected_companies:
        buy_company = st.selectbox("Select Company", selected_companies)
        fo_type = st.selectbox("Select F&O Type", ["Futures", "Options"])
        price = st.number_input("Enter Price per Unit", min_value=0.01, format="%.2f")
        amount = st.number_input("Enter Investment Amount", min_value=0.01, max_value=st.session_state.balance, format="%.2f")
        submitted = st.form_submit_button("Buy")
        
        if submitted:
            if amount > st.session_state.balance:
                st.error("Insufficient balance!")
            elif price <= 0 or amount <= 0:
                st.error("Price and amount must be greater than 0")
            else:
                units = amount / price
                # Deduct from balance
                st.session_state.balance -= amount
                # Initialize price simulation for this company if not already
                if buy_company not in st.session_state.prices:
                    st.session_state.prices[buy_company] = price
                # Add to portfolio
                st.session_state.portfolio = pd.concat([
                    st.session_state.portfolio,
                    pd.DataFrame([{
                        'Company': buy_company,
                        'Type': fo_type,
                        'Invested Amount': amount,
                        'Units': units,
                        'Current Value': amount
                    }])
                ], ignore_index=True)
                st.success(f"Bought {units:.2f} units of {buy_company} {fo_type} for ₹{amount:,.2f}")

# -----------------------------
# Show Balance
# -----------------------------
st.subheader("Available Balance")
st.write(f"₹{st.session_state.balance:,.2f}")

# -----------------------------
# Price Simulation
# -----------------------------
def simulate_prices():
    new_prices = {}
    for company, current_price in st.session_state.prices.items():
        # Simulate price movement: random walk
        change_percent = np.random.normal(0, 0.5)  # +/-0.5% per update
        new_price = current_price * (1 + change_percent / 100)
        new_prices[company] = max(new_price, 0.01)
    return new_prices

# -----------------------------
# Update portfolio values
# -----------------------------
def update_portfolio(prices):
    df = st.session_state.portfolio.copy()
    for idx, row in df.iterrows():
        company = row['Company']
        df.at[idx, 'Current Value'] = row['Units'] * prices.get(company, row['Units'])
    return df

# -----------------------------
# Dynamic Graph
# -----------------------------
st.subheader("Price Chart")

if st.button("Update Prices"):
    st.session_state.prices = simulate_prices()
    
if st.session_state.prices:
    price_df = pd.DataFrame(list(st.session_state.prices.items()), columns=['Company', 'Price'])
    fig = px.bar(price_df, x='Company', y='Price', text='Price', title="Current Prices of Companies")
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Show Portfolio
# -----------------------------
st.subheader("Portfolio")
if not st.session_state.portfolio.empty:
    st.session_state.portfolio = update_portfolio(st.session_state.prices)
    st.dataframe(st.session_state.portfolio.style.format({
        'Invested Amount': "₹{:,.2f}",
        'Current Value': "₹{:,.2f}",
        'Units': "{:.2f}"
    }))
else:
    st.info("Your portfolio is empty. Buy some F&O to see it here.")
