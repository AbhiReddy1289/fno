import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh  # pip install streamlit-autorefresh

st.set_page_config(page_title="F&O Simulator", layout="wide")

# --- Autorefresh every 1 second ---
st_autorefresh(interval=1000, key="datarefresh")

# --- Initialize session state ---
if "balance" not in st.session_state:
    st.session_state.balance = 100_000_000  # 1 Cr default
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}  # {"Stock": [{"type":"option/future","strike":..,"qty":..,"price":..}]}
if "price_data" not in st.session_state:
    st.session_state.price_data = {}  # {"Stock": DataFrame}

# --- Define available companies ---
companies = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

# --- Company selection ---
selected_stocks = st.multiselect("Select companies to simulate", companies)

# --- Initialize price data ---
for stock in selected_stocks:
    if stock not in st.session_state.price_data:
        base_time = datetime.now() - timedelta(hours=168)
        times = [base_time + timedelta(hours=i) for i in range(168)]
        prices = np.random.rand(168) * 1000 + 1000
        st.session_state.price_data[stock] = pd.DataFrame({
            "Datetime": times,
            "Price": prices
        })

# --- Simulate live prices ---
for stock in selected_stocks:
    df = st.session_state.price_data[stock]
    last_price = df["Price"].iloc[-1]
    new_price = last_price + np.random.randn()*5
    new_time = datetime.now()
    st.session_state.price_data[stock] = pd.concat([
        df,
        pd.DataFrame({"Datetime": [new_time], "Price": [new_price]})
    ], ignore_index=True)
    if len(st.session_state.price_data[stock]) > 168:
        st.session_state.price_data[stock] = st.session_state.price_data[stock].iloc[1:]

# --- Display live graph ---
combined_df = pd.DataFrame()
for stock, df in st.session_state.price_data.items():
    if not df.empty:
        temp_df = df.copy()
        temp_df["Stock"] = stock
        combined_df = pd.concat([combined_df, temp_df], ignore_index=True)

if not combined_df.empty:
    fig = px.line(
        combined_df,
        x="Datetime",
        y="Price",
        color="Stock",
        title="Simulated Stock & F&O Prices"
    )
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Select at least one company to see the live graph.")

# --- Portfolio management ---
st.subheader(f"Balance: ₹{st.session_state.balance:,.2f}")

for stock in selected_stocks:
    st.markdown(f"### {stock}")
    option_type = st.selectbox(f"Choose Type for {stock}", ["Stock", "Option", "Future"], key=f"type_{stock}")

    buy_qty = st.number_input(f"Buy quantity for {stock}", min_value=0, step=1, key=f"qty_{stock}")
    buy_price = st.number_input(f"Enter price per unit for {stock}", min_value=0.0, step=0.01, key=f"price_{stock}")

    if st.button(f"Buy {stock}", key=f"buy_{stock}"):
        cost = buy_qty * buy_price
        if cost > st.session_state.balance:
            st.warning("Not enough balance!")
        elif buy_qty > 0:
            st.session_state.balance -= cost
            if stock not in st.session_state.portfolio:
                st.session_state.portfolio[stock] = []
            st.session_state.portfolio[stock].append({
                "type": option_type,
                "qty": buy_qty,
                "price": buy_price,
                "time": datetime.now()
            })
            st.success(f"Bought {buy_qty} of {stock} at ₹{buy_price} each.")

# --- Show Portfolio with Sell Option ---
st.subheader("Portfolio")
if st.session_state.portfolio:
    for stock, entries in st.session_state.portfolio.items():
        st.markdown(f"**{stock}**")
        to_remove = []
        for idx, entry in enumerate(entries):
            current_price = st.session_state.price_data[stock]["Price"].iloc[-1] if stock in st.session_state.price_data else entry["price"]
            pnl = (current_price - entry["price"]) * entry["qty"]
            st.write(f"{idx+1}. {entry['type']} | Qty: {entry['qty']} | Bought at: ₹{entry['price']} | Current P&L: ₹{pnl:,.2f}")
            
            if st.button(f"Sell {stock} position {idx+1}", key=f"sell_{stock}_{idx}"):
                # Sell stock
                st.session_state.balance += current_price * entry["qty"]
                to_remove.append(idx)
                st.success(f"Sold {entry['qty']} of {stock} at ₹{current_price:.2f} each, P&L: ₹{pnl:,.2f}")
        # Remove sold entries
        for idx in sorted(to_remove, reverse=True):
            entries.pop(idx)
else:
    st.info("No stocks bought yet.")
