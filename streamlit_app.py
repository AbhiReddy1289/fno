import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Optional: only import yfinance if installed
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

st.title("Stock & F&O Simulator")

# Example selected stocks
selected_stocks = st.multiselect(
    "Select Stocks", ["AAPL", "MSFT", "GOOG", "TSLA"], default=["AAPL", "MSFT"]
)

# Function to load stock data
def load_data(ticker):
    if YFINANCE_AVAILABLE:
        df = yf.download(ticker, period="7d", interval="1h")
        if df.empty:
            st.warning(f"No data from yfinance for {ticker}, using dummy data.")
        else:
            df = df.reset_index()
            df.rename(columns={"Date": "Datetime"}, inplace=True)
            df["Datetime"] = pd.to_datetime(df["Datetime"])
            return df[["Datetime", "Open", "High", "Low", "Close"]]
    
    # Dummy 7-day 1-hour data
    df = pd.DataFrame({
        "Datetime": pd.date_range(end=pd.Timestamp.now(), periods=7*24, freq="h"),
        "Open": np.random.uniform(100, 200, 7*24),
        "High": np.random.uniform(200, 250, 7*24),
        "Low": np.random.uniform(50, 100, 7*24),
        "Close": np.random.uniform(100, 200, 7*24),
    })
    return df

# Load data for all selected stocks
data_dict = {stock: load_data(stock) for stock in selected_stocks}

# Combine and rotate data for plotting
combined_df = pd.DataFrame()
for stock, df in data_dict.items():
    rotated_df = df.copy()
    rotated_df["Stock"] = stock
    # Use Close price for plotting
    rotated_df["Price"] = rotated_df["Close"]
    combined_df = pd.concat([combined_df, rotated_df], ignore_index=True)

# Plotly chart
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
    st.warning("No data available to plot.")
