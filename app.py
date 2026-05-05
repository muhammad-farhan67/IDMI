import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from utils.db import load_data, get_latest, delta_str
from utils.theme import inject_css

st.set_page_config(
    page_title="IDMI | Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Header ────────────────────────────────────────────────────────────────
st.markdown(
    '<span class="live-dot"></span> **Live** — data refreshed every 10 minutes',
    unsafe_allow_html=True,
)
st.title("Indus Digital Market Intelligence")
st.caption("A real-time intelligence engine for Pakistan's digital economy — "
           "exchange rates, freelance job markets, and AI-powered briefings.")
st.divider()

df = load_data()

if df.empty:
    st.warning("Database is empty. The harvester pipeline hasn't run yet. "
               "Trigger your GitHub Action manually to seed data.")
    st.stop()

latest = get_latest(df)

# ── 5 top metrics ─────────────────────────────────────────────────────────
st.subheader("Live Economic Pulse")
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "USD / PKR",
    f"₨ {latest.get('usd_pkr_rate', '—')}",
    delta_str(df, "usd_pkr_rate"),
)
c2.metric(
    "EUR / PKR",
    f"₨ {latest.get('eur_pkr_rate', '—')}",
    delta_str(df, "eur_pkr_rate"),
)
c3.metric(
    "GBP / PKR",
    f"₨ {latest.get('gbp_pkr_rate', '—')}",
    delta_str(df, "gbp_pkr_rate"),
)
c4.metric(
    "USDT / PKR",
    f"₨ {latest.get('usdt_pkr_rate', '—')}",
    delta_str(df, "usdt_pkr_rate"),
)
c5.metric(
    "Remote Jobs Live",
    f"{latest.get('job_volume', '—'):,}" if latest.get("job_volume") else "—",
    delta_str(df, "job_volume"),
)

st.divider()

# ── STRATOS briefing ──────────────────────────────────────────────────────
st.subheader("STRATOS — AI Market Briefing")
st.info(f"🧠  {latest.get('ai_sentiment', 'Generating…')}")

st.divider()

# ── USD/PKR sparkline ─────────────────────────────────────────────────────
st.subheader("USD / PKR — Recent Trend")

import plotly.express as px
fig = px.line(
    df.tail(30),
    x="timestamp",
    y="usd_pkr_rate",
    markers=True,
    line_shape="spline",
    color_discrete_sequence=["#1a7a3c"],
)
fig.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis=dict(title="", showgrid=False),
    yaxis=dict(title="PKR per USD", gridcolor="#f0f0f0"),
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

st.caption(
    f"Last snapshot: {latest.get('timestamp', '')} UTC  ·  "
    "Ingested via GitHub Actions  ·  Stored in Supabase  ·  "
    "Use the sidebar to explore Freelancer Tools, Market Intelligence, and News."
)
