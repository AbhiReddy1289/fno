import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# Simulate 178 hourly prices starting from 1000
def simulate_hourly_prices(start_price=1000, hours=178):
    prices = [start_price]
    for _ in range(hours - 1):
        change = np.random.normal(0, 5)
        prices.append(max(prices[-1] + change, 100))
    return prices

if "hourly_prices" not in st.session_state:
    st.session_state.hourly_prices = simulate_hourly_prices()
if "price_index" not in st.session_state:
    st.session_state.price_index = 0
if "trades" not in st.session_state:
    st.session_state.trades = []

companies = [
    {"name": "Alpha Corp", "symbol": "ALPH"},
    {"name": "Beta Ltd", "symbol": "BETA"},
    {"name": "Gamma Inc", "symbol": "GAMM"},
]
company_names = [f"{c['name']} ({c['symbol']})" for c in companies]
company_dict = {name: c for name, c in zip(company_names, companies)}

st.title("Live F&O Trading Simulator with 1-Second Auto-Refresh")

selected_company_name = st.selectbox("Choose Company", company_names)
selected_company = company_dict[selected_company_name]

start_time = datetime.now()
current_time = start_time + timedelta(hours=st.session_state.price_index)
current_price = st.session_state.hourly_prices[st.session_state.price_index]

st.markdown(f"### Simulated Date & Time: {current_time.strftime('%Y-%m-%d %H:%M')}")
st.markdown(f"### Simulated Market Price: ₹{current_price:.2f}")

with st.form("add_trade", clear_on_submit=True):
    t_type = st.selectbox("F&O Product", ["Future", "Call Option", "Put Option"])
    buy_sell = st.selectbox("Side", ["Buy", "Sell"])
    qty = st.number_input("Quantity", min_value=1, max_value=1000, value=100)
    strike = st.number_input("Strike Price (for options)", min_value=100, max_value=3000, value=int(current_price))
    premium = st.number_input("Premium (0 for Future)", min_value=0, max_value=10000, value=100)
    expiry = st.date_input("Expiry Date", value=datetime.today() + timedelta(days=30))
    submitted = st.form_submit_button("Add Trade")

if submitted:
    trade = {
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
    st.session_state.trades.append(trade)
    st.success("Trade added.")

if st.button("Square Off All Trades"):
    for t in st.session_state.trades:
        t["Open"] = False
    st.success("All trades closed.")

def calc_pnl(trade, spot):
    if trade["Type"] == "Future":
        multiplier = 1 if trade["Side"] == "Buy" else -1
        return (spot - trade["EntryPrice"]) * trade["Qty"] * multiplier
    else:
        is_call = trade["Type"] == "Call Option"
        side = 1 if trade["Side"] == "Buy" else -1
        intrinsic = max(spot - trade["Strike"], 0) if is_call else max(trade["Strike"] - spot, 0)
        return (intrinsic - trade["Premium"]) * side * trade["Qty"]

trade_df = pd.DataFrame(st.session_state.trades)
if not trade_df.empty:
    trade_df["MTM_PnL"] = trade_df.apply(lambda x: calc_pnl(x, current_price) if x.get("Open", True) else 0, axis=1)
    st.markdown("### Current Trades and Mark-to-Market P&L")
    st.dataframe(trade_df[["Company", "Type", "Side", "Qty", "Strike", "Premium", "Expiry", "Open", "MTM_PnL", "Timestamp"]])

def draw_pnl_graph(index):
    pnl_time_series = [
        sum(calc_pnl(t, price) for t in st.session_state.trades if t.get("Open", True))
        for price in st.session_state.hourly_prices
    ]
    times = [start_time + timedelta(hours=i) for i in range(len(st.session_state.hourly_prices))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=pnl_time_series, mode="lines", name="MTM P&L"))
    fig.add_trace(go.Scatter(
        x=[times[index]],
        y=[pnl_time_series[index]],
        mode="markers+text",
        marker=dict(color="red", size=12),
        text=["Current"],
        textposition="top center",
        name="Current P&L"
    ))
    fig.update_layout(title="Live Mark-to-Market P&L Over Time",
                      xaxis_title="DateTime",
                      yaxis_title="Profit / Loss (INR)")
    st.plotly_chart(fig, use_container_width=True)

draw_pnl_graph(st.session_state.price_index)

running_pnl = sum(calc_pnl(trade, current_price) for trade in st.session_state.trades if trade.get("Open", True))
st.metric("Running MTM P&L at Current Price", f"₹ {running_pnl:,.2f}")

# Auto refresh every 1 second with streamlit-autorefresh
count = st_autorefresh(interval=1000, key="fno_autorefresh")

# Update price index to loop over prices
st.session_state.price_index = (st.session_state.price_index + 1) % len(st.session_state.hourly_prices)
