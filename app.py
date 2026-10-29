import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Sold Stocks Tracker", layout="wide")
st.title("📊 Sold Stocks Tracker & Notional P&L (INR)")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

uploaded_file = st.file_uploader("Upload your sold_stocks_lots_final.xlsx", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    results = []
    
    # 1. Fetch live USD to INR exchange rate
    try:
        usd_inr = yf.Ticker("INR=X", session=session).history(period="1d")['Close'].iloc[-1]
    except:
        usd_inr = 83.50 # Fallback rate if API fails
        st.warning(f"Could not fetch live USD/INR. Using fallback rate: ₹{usd_inr}")
    
    progress_text = "Fetching live market data and converting currencies..."
    my_bar = st.progress(0, text=progress_text)
    
    for index, row in df.iterrows():
        ticker = row['Ticker']
        stock = yf.Ticker(ticker, session=session) 
        
        try:
            live_price = stock.history(period="1d")['Close'].iloc[-1]
            sell_price = row['Sell_Price']
            threshold = row['Threshold_Price']
            
            # 2. Currency Conversion Logic
            # If the ticker does NOT end in .NS (meaning it's a US stock), convert to INR
            if not str(ticker).endswith('.NS'):
                live_price_inr = live_price * usd_inr
                sell_price_inr = sell_price * usd_inr
                threshold_inr = threshold * usd_inr
                currency_label = "USD (Converted to INR)"
            else:
                live_price_inr = live_price
                sell_price_inr = sell_price
                threshold_inr = threshold
                currency_label = "INR"
            
            # Calculate P&L strictly in INR
            pnl_inr = (live_price_inr - sell_price_inr) * row['Quantity']
            status = "🚨 TRIGGERED" if live_price_inr <= threshold_inr else "Watching"
            
            results.append({
                "Ticker": ticker,
                "Trade Date": row['Trade_Date'],
                "Current Price (INR)": round(live_price_inr, 2),
                "Sell Price (INR)": round(sell_price_inr, 2),
                "Threshold (INR)": round(threshold_inr, 2),
                "Notional P&L (INR)": round(pnl_inr, 2),
                "Status": status
            })
        except:
            st.error(f"Failed to fetch data for {ticker}. Check the symbol.")
            
        my_bar.progress((index + 1) / len(df), text=progress_text)
        
    my_bar.empty()
    
    results_df = pd.DataFrame(results)
    
    def highlight_alerts(val):
        color = '#ff4b4b' if val == '🚨 TRIGGERED' else ''
        return f'background-color: {color}'
        
    if not results_df.empty:
        st.dataframe(results_df.style.map(highlight_alerts, subset=['Status']), use_container_width=True)
        
        total_pnl = results_df['Notional P&L (INR)'].sum()
        st.metric(label="Total Notional P&L (Missed Gains / Saved Losses)", value=f"₹{total_pnl:,.2f}")
    else:
        st.warning("No valid data could be fetched. Check your tickers.")
