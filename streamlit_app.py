import streamlit as st
import yfinance as yf

st.set_page_config(page_title="F&O Practice Dashboard", layout="wide")
st.title("📊 F&O Practice Dashboard")

ticker = st.text_input("Enter Stock Ticker (NSE)", "RELIANCE.NS")

if st.button("Fetch Data"):
    data = yf.download(ticker, period="6mo", interval="1d", progress=False)
    st.line_chart(data["Close"])
    st.dataframe(data.tail())

