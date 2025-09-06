import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# --------- Download Real Hourly Data with error handling ---------
@st.cache_data(ttl=3600)
def get_reliance_data():
    try:
        data = yf.download("RELIANCE.NS", period="7d", interval="60m", progress=False)
        if data.empty:
            return None, "Downloaded data is empty. Check ticker or network."
        if 'Close' not in data.columns:
            return None, "'Close' column missing in data. Check symbol or data source."
        return data, None
    except Exception as e:
        return None, f"Error downloading data: {e}"

data, error_msg = get_reliance_data()

if error_msg is not None:
    st.error(error_msg)
    st.stop()

hourly_prices = data['Close'].dropna().tolist()

# Initialize session state after data validation
if "hourly_prices" not in st.session_state:
    st.session_state.hourly_prices = hourly_prices
if "price_index" not in st.session_state:
    st.session_state.price_index = 0
if "trades" not in st.session_state:
    st.session_state.trades = []

companies = [
    {"name": "Reliance Industries", "symbol": "RELIANCE.NS"},
]

company_names = [f"{c['name']} ({c['symbol']})" for c in companies]
company_dict = {name: c for name, c in zip(company_names, companies)}

st.title("Robust Real Data F&O Trading Simulator - Reliance Industries")

selected_company_name = st.selectbox("Choose Company", company_names)
selected_company = company_dict[selected_company_name]

start_time = data.index[0]
current_time = start_time + timedelta(hours=st.session_state.price_index)
current_price = st.session_state.hourly_prices[st.session_state.price_index]

st.markdown(f"### Simulated Date & Time: {current_time.strftime('%Y-%m-%d %H:%M')}")
st.markdown(f"### Simulated Market Price: ₹{current_price:.2f}")

with st.form("trade_form", clear_on_submit=True):
    t_type = st.selectbox("F&O Product", ["Future", "Call Option", "Put Option"])
    buy_sell = st.selectbox("Side", ["Buy", "Sell"])
    qty = st.number_input("Quantity", 1, 1000, 100)
    strike = st.number_input("Strike Price (for options)", 100, 3000, int(current_price))
    premium = st.number_input("Premium (0 for Future)", 0, 10000, 100)
    expiry = st.date_input("Expiry Date", value=datetime.today() + timedelta(days=30))
    submitted = st.form_submit_button("Add Trade")

if submitted:
    new_trade = {
        "Company": selected_company['name'],
        "Symbol": selected_company['symbol'],
        "Type": t_type,
        "Side": buy_sell,
        "Qty": qty,
        "Strike": strike,
        "Premium": premium if t_type != "Future" else 0,
        "EntryPrice": current_price,
        "Expiry": expiry,
        "Open": True,
        "Timestamp": datetime.now()
    }
    st.session_state.trades.append(new_trade)
    st.success(f"Added {buy_sell} {t_type} with qty {qty} @ strike {strike}")

if st.button("Square Off All Trades"):
    for trade in st.session_state.trades:
        trade["Open"] = False
    st.success("All trades closed.")

def calc_pnl(trade, spot):
    if trade["Type"] == "Future":
        multiplier = 1 if trade["Side"] == "Buy" else -1
        return (spot - trade["EntryPrice"]) * trade["Qty"] * multiplier
    else:
        is_call = (trade["Type"] == "Call Option")
        side = 1 if trade["Side"] == "Buy" else -1
        intrinsic = max(spot - trade["Strike"], 0) if is_call else max(trade["Strike"] - spot, 0)
        return (intrinsic - trade["Premium"]) * side * trade["Qty"]

trade_df = pd.DataFrame(st.session_state.trades)
if not trade_df.empty:
    trade_df["MTM_PnL"] = trade_df.apply(lambda t: calc_pnl(t, current_price) if t.get("Open", True) else 0, axis=1)
    st.markdown("### Active Trades and Their Mark-to-Market P&L")
    st.dataframe(trade_df[["Company","Type","Side","Qty","Strike","Premium","Expiry","Open","MTM_PnL","Timestamp"]])

window_size = 24
start_idx = max(0, st.session_state.price_index - window_size + 1)
window_prices = st.session_state.hourly_prices[start_idx:st.session_state.price_index+1]
window_times = data.index[start_idx:st.session_state.price_index+1]

def pnl_series_only(prices):
    return [
        sum(calc_pnl(t, price) for t in st.session_state.trades if t.get("Open", True))
        for price in prices
    ]

pnl_values = pnl_series_only(window_prices)

fig = go.Figure()
fig.add_trace(go.Scatter(x=window_times, y=pnl_values, mode="lines+markers", name="MTM P&L"))
fig.update_layout(
    title=f"MTM P&L Sliding Window (Last {window_size} Hours)",
    xaxis_title="Time",
    yaxis_title="Profit / Loss (INR)"
)
st.plotly_chart(fig, use_container_width=True)

running_pnl = sum(calc_pnl(t, current_price) for t in st.session_state.trades if t.get("Open", True))
st.metric("Running Mark-to-Market P&L at Current Price", f"₹ {running_pnl:,.2f}")

st_autorefresh(interval=1000, key="autoreload")
st.session_state.price_index = (st.session_state.price_index + 1) % len(st.session_state.hourly_prices)
