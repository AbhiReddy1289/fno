import streamlit as st  
import pandas as pd  
import numpy as np  
import plotly.express as px  

# -----------------------------  
# Initialize session state safely  
# -----------------------------  
if 'balance' not in st.session_state:  
    st.session_state.balance = 1_00_000_000  # 1 Crore (numeric)  

if 'portfolio' not in st.session_state:  
    st.session_state.portfolio = pd.DataFrame(  
        columns=['Company', 'Type', 'Invested Amount', 'Units', 'Current Value']  
    )  

if 'prices' not in st.session_state:  
    st.session_state.prices = {}  # {company: price}  

if 'price_history' not in st.session_state:  
    st.session_state.price_history = {}  # {company: [prices]}  

# -----------------------------  
# Company list  
# -----------------------------  
companies = ["TCS", "INFY", "RELIANCE", "HDFC", "ICICI", "SBIN", "LT", "WIPRO"]  

# Page setup  
st.set_page_config(page_title="F&O Simulator", layout="wide")  
st.title("F&O Simulator")  

# -----------------------------  
# Company Selection (checkbox-style checklist)  
# -----------------------------  
st.subheader("Select Companies to Trade")  
selected_companies = st.multiselect(  
    "Choose one or more companies",  
    options=companies,  
    default=[]  
)  

# -----------------------------  
# Buy Section  
# -----------------------------  
st.subheader("Buy F&O")  

# Buy form should appear only after at least one company is selected  
if selected_companies:  
    with st.form("buy_form"):  
        buy_company = st.selectbox("Select Company", options=selected_companies)  

        fo_type = st.selectbox("Select F&O Type", ["Futures", "Options"])  

        price = st.number_input(  
            "Enter Price per Unit",  
            min_value=0.01,  
            value=0.01,  
            format="%.2f",  
            step=0.01  
        )  

        current_balance = float(st.session_state.balance)  
        amount = st.number_input(  
            "Enter Investment Amount",  
            min_value=0.01,  
            max_value=current_balance,  
            value=0.01,  
            format="%.2f",  
            step=0.01  
        )  

        submitted = st.form_submit_button("Buy")  

        if submitted:  
            # Validation  
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
                    st.session_state.price_history[buy_company] = [price]  
                else:  
                    # Append current price to history  
                    st.session_state.price_history[buy_company].append(price)  

                # Add to portfolio  
                new_row = {  
                    'Company': buy_company,  
                    'Type': fo_type,  
                    'Invested Amount': amount,  
                    'Units': units,  
                    'Current Value': amount  
                }  
                st.session_state.portfolio = pd.concat([  
                    st.session_state.portfolio,  
                    pd.DataFrame([new_row])  
                ], ignore_index=True)  

                st.success(f"Bought {units:.4f} units of {buy_company} ({fo_type}) for ₹{amount:,.2f}")  
else:  
    st.info("Select one or more companies to enable the Buy form.")  

# -----------------------------  
# Display Balance  
# -----------------------------  
st.sidebar.subheader("Account Summary")  
st.sidebar.write(f"Balance: ₹{float(st.session_state.balance):,.2f}")  

# -----------------------------  
# Price Update & Visualization  
# -----------------------------  
st.subheader("Prices & Portfolio")  

# Update Prices button (simulate random walk)  
update_clicked = st.button("Update Prices")  

# Initialize prices for all
