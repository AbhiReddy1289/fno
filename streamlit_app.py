import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import time
from datetime import datetime, timedelta

# ----- Setup: Simulate 178 hourly prices -----
def simulate_hourly_prices(start_price=1000, hours=178):
    prices = [start_price]
    for _ in range(hours - 1):
        change = np.random.normal(loc=0, scale=5)  # Gaussian noise simulating volatility
        new_price = prices[-1] + change
        if new_price < 100:
            new_price = 100
        prices.append(new_price)
    return prices

if "hourly_prices" not in st.session_state:
    st.session_state.hourly_prices = simulate_hourly_prices()

if "price_index" not in st.session_state:
    st.session_state.price_index = 0

# Company data
companies = [
    {"name": "Alpha Corp", "symbol": "ALPH"},
    {"name": "Beta Ltd", "symbol": "BETA"},
    {"name": "Gamma Inc", "symbol": "GAMM"},
]
company_names = [f"{c['name']} ({c['symbol']})" for c in companies]
company_dict = {name: c for name, c in zip(company_names, companies)}

# Initialize balance and trades
if "balance" not in st.session_state:
    st.session_state.balance = 1_00_00_000
if "trades" not in st.session_state:
    st.session_state.trades = []

for trade in st.session_state.trades:
    if "Open" not in trade:
        trade["Open"] = True

st.title("Live F&O Trading Simulator with Real-Time Moving P&L Graph")

# Company Selection
selected_company_name = st.selectbox("Choose Company", company_names)
selected_company = company_dict[selected_company_name]

# Show simulated current time and price
start_time = datetime.now()
current_time = start_time + timedelta(hours=st.session_state.price_index)
current_price = st.session_state.hourly_prices[st.session_state.price_index]
st.markdown(f"### Simulated Date & Time: {current_time.strftime('%Y-%m-%d %H:%M')}")
st.markdown(f"### Simulated Market Price: ₹{current_price:.2f}")

# Trade Entry Form
with st.form("trade_entry_form", clear_on_submit=True):
    t_type = st.selectbox("F&O Product", ["Future", "Call Option", "Put Option"])
    buy_sell = st.selectbox("Buy or Sell", ["Buy", "Sell"])
    qty = st.number_input("Quantity", min_value=1, max_value=1000, value=100)
    strike = st.number_input("Strike Price (for options)", min_value=100, max_value=3000, value=int(current_price), step=1)
    premium = st.number_input("Option Premium (0 for Future)", min_value=0, max_value=10000, value=100, step=1)
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
    st.success(f"Trade added: {selected_company['name']} {t_type} {buy_sell} Qty: {qty}")

# Square off trades button
if st.button("Square Off All Trades"):
    for t in st.session_state.trades:
        t["Open"] = False
    st.success("All trades closed.")

# P&L calculation
def calc_pnl(trade, spot):
    if trade["Type"] == "Future":
        multiplier = 1 if trade["Side"] == "Buy" else -1
        return (spot - trade["EntryPrice"]) * trade["Qty"] * multiplier
    else:
        is_call = trade["Type"] == "Call Option"
        side = 1 if trade["Side"] == "Buy" else -1
        intrinsic = max(spot - trade["Strike"], 0) if is_call else max(trade["Strike"] - spot, 0)
        return (intrinsic - trade["Premium"]) * side * trade["Qty"]

# Display trades and MTM at current price
trade_df = pd.DataFrame(st.session_state.trades)
if not trade_df.empty:
    trade_df["MTM_PnL"] = trade_df.apply(lambda x: calc_pnl(x, current_price) if x.get("Open", True) else 0, axis=1)
    st.markdown("### Current Trades and Mark-to-Market Profit/Loss")
    st.dataframe(trade_df[["Company", "Type", "Side", "Qty", "Strike", "Premium", "Expiry", "Open", "MTM_PnL", "Timestamp"]])

# Live moving P&L graph container
graph_placeholder = st.empty()

# Auto-play checkbox
auto_play = st.checkbox("Auto-play simulation (updates every second)", value=True)

# Function to draw P&L graph at given index
def draw_pnl_graph(index):
    spot_price = st.session_state.hourly_prices[index]
    pnl_time_series = [
        sum(calc_pnl(trade, price) for trade in st.session_state.trades if trade.get("Open", True))
        for price in st.session_state.hourly_prices
    ]
    times = [start_time + timedelta(hours=i) for i in range(len(pnl_time_series))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=pnl_time_series, mode="lines", name="MTM P&L"))
    # Mark current price point
    fig.add_trace(go.Scatter(
        x=[times[index]],
        y=[pnl_time_series[index]],
        mode="markers+text",
        marker=dict(color="red", size=12),
        text=["Current"],
        textposition="top center",
        name="Current P&L"
    ))
    fig.update_layout(
        title="Live Mark-to-Market P&L Over Simulated Time (Updates Every Second)",
        xaxis_title="DateTime",
        yaxis_title="Profit / Loss (INR)"
    )
    graph_placeholder.plotly_chart(fig, use_container_width=True)

# Manual time slider to jump around
time_index = st.slider(
    "Simulated Time Index (hours)",
    0, len(st.session_state.hourly_prices) - 1,
    st.session_state.price_index,
    step=1
)

# Update session state time index if changed by user slider
if time_index != st.session_state.price_index:
    st.session_state.price_index = time_index
    # Update current price view immediately
    current_price = st.session_state.hourly_prices[st.session_state.price_index]
    st.experimental_rerun()

# Draw the graph at the current index
draw_pnl_graph(st.session_state.price_index)

# Display running P&L metric
running_pnl = sum(
    calc_pnl(trade, st.session_state.hourly_prices[st.session_state.price_index])
    for trade in st.session_state.trades if trade.get("Open", True)
)
st.metric("Running Mark-to-Market P&L at Current Price", f"₹ {running_pnl:,.2f}")

# Auto-play logic: iteratively increase price_index and rerun app every second
if auto_play:
    if st.session_state.price_index < len(st.session_state.hourly_prices) - 1:
        st.session_state.price_index += 1
        time.sleep(1)
        st.experimental_rerun()
