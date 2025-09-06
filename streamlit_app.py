import yfinance as yf
import streamlit as st

st.title("📈 F&O Stock Data Viewer")

# 🔹 Common NSE F&O tickers (Nifty50)
nifty50_tickers = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "SBIN.NS", "LT.NS", "HINDUNILVR.NS",
    "ITC.NS", "BAJFINANCE.NS", "ADANIENT.NS", "ADANIPORTS.NS", "BHARTIARTL.NS",
    "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "ULTRACEMCO.NS", "ASIANPAINT.NS"
]

# 🔹 Checklist for user
selected_tickers = st.multiselect(
    "Select one or more stocks:",
    options=nifty50_tickers,
    default=["RELIANCE.NS"]
)

# 🔹 Download and show data
if selected_tickers:
    for ticker in selected_tickers:
        st.subheader(f"📊 {ticker}")
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if data.empty:
            st.error(f"No data found for {ticker}.")
        else:
            st.write(data.tail())  # last 5 rows
            st.line_chart(data["Close"])
