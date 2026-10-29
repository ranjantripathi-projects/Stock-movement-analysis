import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title="Sold Stocks Tracker", layout="wide")
st.title("📊 Sold Stocks Tracker & Notional P&L")

# File Uploader
uploaded_file = st.file_uploader("Upload your sold_stocks.xlsx", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    results = []
    
    # Progress bar for fetching data
    progress_text = "Fetching live market data..."
    my_bar = st.progress(0, text=progress_text)
    
    for index, row in df.iterrows():
        ticker = row['Ticker']
        stock = yf.Ticker(ticker)
        
        try:
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            pnl = (current_price - row['Sell_Price']) * row['Quantity']
            status = "🚨 TRIGGERED" if current_price <= row['Threshold_Price'] else "Watching"
            
            results.append({
                "Ticker": ticker,
                "Trade Date": row['Trade_Date'],
                "Current Price": round(current_price, 2),
                "Sell Price": row['Sell_Price'],
                "Threshold": row['Threshold_Price'],
                "Notional P&L": round(pnl, 2),
                "Status": status
            })
        except:
            st.error(f"Failed to fetch data for {ticker}. Check the symbol.")
            
        my_bar.progress((index + 1) / len(df), text=progress_text)
        
    my_bar.empty()
    
    # Display as a clean, interactive dashboard table
    results_df = pd.DataFrame(results)
    
    # Highlight triggered rows
    def highlight_alerts(val):
        color = '#ff4b4b' if val == '🚨 TRIGGERED' else ''
        return f'background-color: {color}'
        
    st.dataframe(results_df.style.applymap(highlight_alerts, subset=['Status']), use_container_width=True)
    
    # Summary Metrics
    total_pnl = results_df['Notional P&L'].sum()
    st.metric(label="Total Notional P&L (Missed Gains / Saved Losses)", value=f"₹{total_pnl:,.2f}")
