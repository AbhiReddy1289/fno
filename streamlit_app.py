import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Company universe (customize as needed)
companies = [
    {"name": "Alpha Corp", "symbol": "ALPH"},
    {"name": "Beta Ltd", "symbol": "BETA"},
    {"name": "Gamma Inc", "symbol": "GAMM"},
]

# Initialize session state for balance and trades
if "balance" not in st.session_state:
    st.session_state.balance = 1_00_00_000
if "trades" not in st.session_state:
    st.session_state.trades = []

# Patch older trades with missing fields if needed
for trade in st.session_state.trades:
    if "Open" not in trade:
        trade["Open"] = True

st.title("F&O Trading Simulation Playground")

# Select company
company_names = [f"{c['name']} ({c['symbol']})" for c in companies]
company_dict = {f"{c['name']} ({c['symbol']})": c for c in companies}
selected_company_name = st.selectbox("Choose Company", company_names)
selected_company = company_dict[selected_company_name]

st.markdown("---")

# Simulated Market Price Slider (real or replay)
market_price = st.slider(
    "Simulated Spot Price (moves live P&L)", 500, 2000, 1000, step=1
)

st.markdown(f"**Current Simulated Market Price: ₹{market_price}**")

# F&O Trade Entry
with st.form(key="trade_entry_form"):
    t_type = st.selectbox("F&O Product", ["Future", "Call Option", "Put Option"])
    buy_sell = st.selectbox("Buy or Sell", ["Buy", "Sell"])
    qty = st.number_input("Quantity", 1, 1000, 100)
    strike = st.number_input("Strike Price (for option)", 500, 2000, market_price, step=1)
    premium = st.number_input("Option Premium (0 for Future)", 0, 10000, 100)
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
            "EntryPrice": market_price,
            "Expiry": expiry,
            "Open": True,
            "Timestamp": datetime.now()
        }
        st.session_state.trades.append(trade)
        st.success(f"Trade added: {selected_company['name']} {t_type} {buy_sell}, Strike {strike}")

# Button to square off all open trades
if st.button("Square Off All Trades"):
    for t in st.session_state.trades:
        t["Open"] = False
    st.success("All trades closed.")

# Mark-to-Market P&L calculation
def calc_pnl(trade, spot):
    if trade["Type"] == "Future":
        multiplier = 1 if trade["Side"] == "Buy" else -1
        return (spot - trade["EntryPrice"]) * trade["Qty"] * multiplier
    else:
        is_call = trade["Type"] == "Call Option"
        side = 1 if trade["Side"] == "Buy" else -1
        # Option payoff calculation:
        intrinsic = max(spot - trade["Strike"], 0) if is_call else max(trade["Strike"] - spot, 0)
        payoff = (intrinsic - trade["Premium"]) * side * trade["Qty"]
        return payoff

# Display trades and live MTM P&L
trade_df = pd.DataFrame(st.session_state.trades)
if not trade_df.empty:
    trade_df["MTM_PnL"] = trade_df.apply(lambda x: calc_pnl(x, market_price) if x.get("Open", True) else 0, axis=1)
    st.markdown("### Current Trades and Mark-to-Market P&L")
    st.dataframe(trade_df[["Company", "Type", "Side", "Qty", "Strike", "Premium", "Expiry", "Open", "MTM_PnL", "Timestamp"]])

# Live, moving P&L graph as spot changes
st.markdown('### Live P&L Graph: Moves with Price')
pnl_hist = []
spot_range = np.linspace(market_price - 200, market_price + 200, 100)
for spot in spot_range:
    total_pnl = sum(
        calc_pnl(trade, spot) for trade in st.session_state.trades if trade.get("Open", True)
    )
    pnl_hist.append({'Spot': spot, 'P&L': total_pnl})

pnl_df = pd.DataFrame(pnl_hist)

fig = go.Figure()
fig.add_trace(go.Scatter(x=pnl_df["Spot"], y=pnl_df["P&L"], mode="lines+markers", name="P&L"))
fig.add_trace(go.Scatter(x=[market_price], y=[pnl_df.loc[np.abs(pnl_df['Spot'] - market_price).idxmin(), 'P&L']],
                         mode="markers+text", text=["Current"], textposition="top center",
                         marker=dict(size=12, color='red'), name="Current Price"))
fig.update_layout(title="Potential Profit/Loss vs Spot Price", xaxis_title="Spot Price", yaxis_title="P&L")

st.plotly_chart(fig, use_container_width=True)

st.metric(
    "Total Running P&L at Current Price",
    int(pnl_df.loc[np.abs(pnl_df['Spot'] - market_price).idxmin(), 'P&L'])
)

st.info(
    "Try any company and F&O product, buy/sell, adjust spot, play with strikes, expiry and premium. "
    "The table and graph update instantly to show how your P&L would move with the market—just like real F&O trading."
)

