import streamlit as st
import pandas as pd
from supabase import create_client
import os
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="IDMI | Market Intelligence", layout="wide")
st.title("📊 Indus Digital Market Intelligence (IDMI)")
st.markdown("A High-Velocity Predictive Analytics Engine for Pakistan's Digital Economy.")

# --- DATABASE CONNECTION ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- DATA FETCHING ---
@st.cache_data(ttl=600) # Cache data for 10 minutes to save database hits
def load_data():
    try:
        response = supabase.table("market_intel").select("*").execute()
        
        # 1. Check if we actually got data
        if not response.data:
            return pd.DataFrame()
            
        # 2. Convert to DataFrame
        df = pd.DataFrame(response.data)
        
        # 3. Clean up the timestamp
        # Using errors='coerce' prevents the app from crashing if a row is messy
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # 4. Final sorting
        df = df.sort_values('timestamp')
        return df
    except Exception as e:
        # This will show you the ACTUAL error on the Streamlit screen
        st.error(f"Error fetching from Supabase: {e}")
        return pd.DataFrame()

df = load_data()

# --- DASHBOARD UI ---
if df.empty:
    st.warning("Database is currently empty. Waiting for the Harvester pipeline to run...")
else:
    # Get the latest row of data
    latest = df.iloc[-1]
    
    # 1. Key Metrics Row
    st.header("⚡ Live Economic Pulse")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current USD/PKR Rate", f"Rs. {latest['usd_pkr_rate']}")
    col2.metric("Freelance Purchasing Power Index", latest['purchasing_power_index'])
    col3.metric("Global Tech Job Volume", latest['job_volume'])

    st.divider()

    # 2. AI Sentiment Section
    st.header("🧠 STRATOS: AI Market Sentiment")
    st.info(latest['ai_sentiment'])

    st.divider()

    # 3. Big Data Visualization
    st.header("📈 Historical Trend Analysis")
    fig = px.line(df, x='timestamp', y='usd_pkr_rate', 
                  title="USD to PKR Volatility Over Time",
                  markers=True, line_shape="spline")
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("Data is ingested automatically via serverless GitHub Action pipelines.")
