import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import time
from datetime import datetime, timedelta

# Session State Setup
if "balance" not in st.session_state:
    st.session_state.balance = 1_00_00_000
if "trades" not in st.session_state:
    st.session_state.trades = []
if "market_price" not in st.session_state:
    st.session_state.market_price = 1000  # Example starting price

st.title("F&O Trading Simulator – Real-Time P&L Playground")

# 1. Simulated Market Price Slider (real-time or replay)
market_price = st.slider("Simulated Spot Price", 500, 2000, int(st.session_state.market_price), step=1)
st.session_state.market_price = market_price

# 2. F&O Trade Entry
with st.form("trade_entry"):
    t_type = st.selectbox("Product", ["Future", "Call Option", "Put Option"])
    buy_sell = st.selectbox("Side", ["Buy", "Sell"])
    qty = st.number_input("Quantity", 1, 1000, 1)
    strike = st.number_input("Strike Price", 500, 2000, market_price, step=1)
    premium = st.number_input("Option Premium (0 for Future)", 0, 10000, 100)
    expiry = st.date_input("Expiry Date", value=datetime.today() + timedelta(days=30))
    submit = st.form_submit_button("Add Trade")
    
    if submit:
        trade = {
            "Type": t_type, "Side": buy_sell, "Qty": qty, "Strike": strike,
            "Premium": premium if t_type != "Future" else 0,
            "EntryPrice": st.session_state.market_price,
            "Expiry": expiry,
            "Open": True,
            "Timestamp": datetime.now()
        }
        st.session_state.trades.append(trade)
        st.success("Trade added.")

# Close (exit/unwind) trades button
if st.button("Square Off All"):
    for t in st.session_state.trades:
        t["Open"] = False

# 3. Live Trade Table & P&L
def calc_pnl(trade, spot):
    if trade["Type"] == "Future":
        multiplier = 1 if trade["Side"] == "Buy" else -1
        return (spot - trade["EntryPrice"]) * trade["Qty"] * multiplier
    else:
        # Option
        is_call = trade["Type"] == "Call Option"
        side = 1 if trade["Side"] == "Buy" else -1
        # Payoff for call: max(spot-strike, 0) - premium  (long), or -payoff (short)
        intrinsic = max(spot - trade["Strike"], 0) if is_call else max(trade["Strike"] - spot, 0)
        payoff = (intrinsic - trade["Premium"]) * side * trade["Qty"]
        return payoff

# MTM P&L Table
trade_df = pd.DataFrame(st.session_state.trades)
if not trade_df.empty:
    trade_df["MTM_PnL"] = trade_df.apply(lambda x: calc_pnl(x, st.session_state.market_price), axis=1)
    st.markdown("### Current Trades and MTM Profit/Loss")
    st.dataframe(trade_df)

# 4. Real-Time Moving Graph (simulate passage of time or price)
st.markdown('### Live P&L Graph (Moves with Price or Time)')
placeholder = st.empty()
pnl_history = []

# Simulate a "live" moving graph over spot price range
spot_prices = np.linspace(st.session_state.market_price - 100, st.session_state.market_price + 100, 100)
for spot in spot_prices:
    pnl = sum([calc_pnl(trade, spot) for trade in st.session_state.trades if trade["Open"]])
    pnl_history.append({'Spot': spot, 'PnL': pnl})

_pnl_df = pd.DataFrame(pnl_history)
with placeholder.container():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=_pnl_df["Spot"], y=_pnl_df["PnL"], mode="lines+markers", name="Running P&L"))
    fig.update_layout(title="Potential P&L vs Spot Price (Dynamic Live View)", xaxis_title="Spot Price", yaxis_title="P&L")
    st.plotly_chart(fig, use_container_width=True)

# 5. Real-Time Progress: Show recent P&L change with price updates
if not trade_df.empty:
    st.metric("Running P&L at Current Price", int(_pnl_df[_pnl_df["Spot"] == st.session_state.market_price]["PnL"].values))

st.info("Try any combination: buy/sell, different strikes, expiries, and see real-time change in loss/gain as market price moves. Use slider to simulate the market, or add/close trades to observe instantaneous MTM movement, like real F&O trading.")


