"""
pages/1_📊_Dashboard.py — Full historical dashboard with multi-currency charts.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.db import load_data, get_latest, delta_str
from utils.theme import inject_css

st.set_page_config(page_title="Dashboard | IDMI", page_icon="📊", layout="wide")
inject_css()

st.title("Market Dashboard")
st.caption("Full historical view of all tracked economic indicators.")

df = load_data()
if df.empty:
    st.warning("No data yet. Run the harvester pipeline first.")
    st.stop()

latest = get_latest(df)

# ── Date range filter ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    days = st.selectbox("History window", [7, 14, 30, 90, 999], index=2,
                        format_func=lambda x: "All time" if x == 999 else f"Last {x} days")

df_filtered = df.tail(days) if days < 999 else df

# ── Currency metrics row ──────────────────────────────────────────────────
st.subheader("Currency Rates")
cols = st.columns(6)
pairs = [
    ("USD/PKR", "usd_pkr_rate"),
    ("EUR/PKR", "eur_pkr_rate"),
    ("GBP/PKR", "gbp_pkr_rate"),
    ("SAR/PKR", "sar_pkr_rate"),
    ("AED/PKR", "aed_pkr_rate"),
    ("USDT/PKR","usdt_pkr_rate"),
]
for col, (label, key) in zip(cols, pairs):
    val = latest.get(key)
    col.metric(label, f"₨ {val}" if val else "—", delta_str(df, key))

st.divider()

# ── Multi-currency line chart ─────────────────────────────────────────────
st.subheader("Currency Trends")

currency_cols = [k for _, k in pairs if k in df_filtered.columns]
if currency_cols:
    df_melt = df_filtered[["timestamp"] + currency_cols].melt(
        id_vars="timestamp", var_name="Pair", value_name="PKR Rate"
    )
    label_map = {k: label for label, k in pairs}
    df_melt["Pair"] = df_melt["Pair"].map(label_map)

    fig = px.line(
        df_melt, x="timestamp", y="PKR Rate", color="Pair",
        line_shape="spline", markers=False,
        color_discrete_sequence=["#1a7a3c","#C9A84C","#2563eb","#dc2626","#7c3aed","#0891b2"],
    )
    fig.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(title="", showgrid=False),
        yaxis=dict(title="PKR", gridcolor="#f0f0f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Two-column section: Job volume + Purchasing Power ─────────────────────
st.subheader("Job Market & Purchasing Power")
col_a, col_b = st.columns(2)

with col_a:
    if "job_volume" in df_filtered.columns:
        fig2 = px.bar(
            df_filtered, x="timestamp", y="job_volume",
            color_discrete_sequence=["#1a7a3c"],
            labels={"job_volume": "Live Job Listings", "timestamp": ""},
        )
        fig2.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#f0f0f0"),
        )
        st.markdown("**Remote Job Volume**")
        st.plotly_chart(fig2, use_container_width=True)

with col_b:
    if "purchasing_power_index" in df_filtered.columns:
        fig3 = px.area(
            df_filtered, x="timestamp", y="purchasing_power_index",
            color_discrete_sequence=["#C9A84C"],
            labels={"purchasing_power_index": "Index", "timestamp": ""},
        )
        fig3.update_traces(fill="tozeroy", fillcolor="rgba(201,168,76,0.12)")
        fig3.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#f0f0f0"),
        )
        st.markdown("**Freelancer Purchasing Power Index**")
        st.caption("PKR equivalent of earning USD 100,000 — higher = stronger rupee")
        st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Raw data table ────────────────────────────────────────────────────────
with st.expander("Raw data table"):
    display_cols = ["timestamp", "usd_pkr_rate", "eur_pkr_rate", "gbp_pkr_rate",
                    "usdt_pkr_rate", "job_volume", "purchasing_power_index"]
    available = [c for c in display_cols if c in df_filtered.columns]
    st.dataframe(df_filtered[available].sort_values("timestamp", ascending=False),
                 use_container_width=True, hide_index=True)
    st.download_button(
        "Download CSV",
        df_filtered[available].to_csv(index=False),
        "idmi_data.csv", "text/csv",
    )
