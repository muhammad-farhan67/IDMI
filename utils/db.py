import json
import streamlit as st
import pandas as pd
from supabase import create_client


@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


@st.cache_data(ttl=600)
def load_data():
    """Load and clean the full market_intel table. Cached 10 minutes."""
    supabase = init_connection()
    try:
        response = supabase.table("market_intel").select("*").execute()
        if not response.data:
            return pd.DataFrame()
        df = pd.DataFrame(response.data)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()


def get_latest(df):
    """Return the most recent row as a dict."""
    if df.empty:
        return {}
    return df.iloc[-1].to_dict()


def parse_json_col(row, col):
    """Safely parse a JSON string column into a Python list/dict."""
    val = row.get(col, "[]")
    try:
        return json.loads(val) if isinstance(val, str) else []
    except Exception:
        return []


def delta_str(df, col):
    """
    Compute the change between the last two rows of `col`.
    Returns a string like '+2.30' or '-1.10', or None if not enough data.
    """
    if col not in df.columns or len(df) < 2:
        return None
    try:
        prev = float(df.iloc[-2][col])
        curr = float(df.iloc[-1][col])
        diff = round(curr - prev, 2)
        return f"{diff:+.2f}"
    except Exception:
        return None
