import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import plotly.express as px
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

# ── Header — live dot below title so it is clearly visible ────────────────
st.title("Indus Digital Market Intelligence")
st.caption(
    "A real-time intelligence engine for Pakistan's digital economy — "
    "exchange rates, freelance job markets, and AI-powered briefings."
)
st.markdown(
    '<p style="margin-top:-4px;margin-bottom:4px;font-size:13px;">'
    '<span class="live-dot"></span>'
    '<span style="color:#22c55e;font-weight:700;letter-spacing:.5px;">LIVE</span>'
    '&nbsp;·&nbsp;pipeline runs every 12 h&nbsp;·&nbsp;UI cache 10 min</p>',
    unsafe_allow_html=True,
)
st.divider()

df = load_data()

if df.empty:
    st.warning(
        "Database is empty. Go to GitHub → Actions → IDMI Data Harvester → "
        "Run workflow to seed your first snapshot."
    )
    st.stop()

latest = get_latest(df)

# ── Row 1 — five primary metrics ──────────────────────────────────────────
st.subheader("Live Economic Pulse")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("USD / PKR",  f"₨ {latest.get('usd_pkr_rate','—')}",  delta_str(df,"usd_pkr_rate"))
c2.metric("EUR / PKR",  f"₨ {latest.get('eur_pkr_rate','—')}",  delta_str(df,"eur_pkr_rate"))
c3.metric("GBP / PKR",  f"₨ {latest.get('gbp_pkr_rate','—')}",  delta_str(df,"gbp_pkr_rate"))
c4.metric("USDT / PKR", f"₨ {latest.get('usdt_pkr_rate','—')}", delta_str(df,"usdt_pkr_rate"))
c5.metric(
    "Remote Jobs",
    f"{int(latest.get('job_volume',0)):,}" if latest.get("job_volume") else "—",
    delta_str(df,"job_volume"),
)

# ── Row 2 — secondary metrics ─────────────────────────────────────────────
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
r1, r2, r3, r4 = st.columns(4)
r1.metric("SAR / PKR", f"₨ {latest.get('sar_pkr_rate','—')}", delta_str(df,"sar_pkr_rate"))
r2.metric("AED / PKR", f"₨ {latest.get('aed_pkr_rate','—')}", delta_str(df,"aed_pkr_rate"))
r3.metric(
    "BTC / USD",
    f"${int(latest.get('btc_usd_rate',0)):,}" if latest.get("btc_usd_rate") else "—",
    delta_str(df,"btc_usd_rate"),
)
r4.metric("Purchasing Power Index", latest.get("purchasing_power_index","—"),
          delta_str(df,"purchasing_power_index"))

st.divider()

# ── STRATOS briefing ─────────────────────────────────────────────────
st.subheader("🧠 STRATOS — Latest Market Briefing")
    raw_briefing = latest.get("ai_sentiment", "")
    if raw_briefing:
        # Try to render the structured format with coloured labels
        for line in raw_briefing.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("Currency Outlook:"):
                st.markdown(
                    f"<div style='background:#f0fdf4;border-left:4px solid #16a34a;"
                    f"padding:10px 14px;border-radius:6px;margin-bottom:8px;'>"
                    f"<strong style='color:#15803d;'>💱 Currency Outlook</strong><br>"
                    f"<span style='color:#1c1c1c'>{line.replace('Currency Outlook:','').strip()}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            elif line.startswith("Job Market:"):
                st.markdown(
                    f"<div style='background:#fffbeb;border-left:4px solid #d97706;"
                    f"padding:10px 14px;border-radius:6px;margin-bottom:8px;'>"
                    f"<strong style='color:#b45309;'>📋 Job Market</strong><br>"
                    f"<span style='color:#1c1c1c'>{line.replace('Job Market:','').strip()}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            elif line.startswith("Action Item:"):
                st.markdown(
                    f"<div style='background:#eff6ff;border-left:4px solid #2563eb;"
                    f"padding:10px 14px;border-radius:6px;margin-bottom:8px;'>"
                    f"<strong style='color:#1d4ed8;'>⚡ Action Item</strong><br>"
                    f"<span style='color:#1c1c1c'>{line.replace('Action Item:','').strip()}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.info(line)
    else:
        st.info("🧠 No briefing yet — run the pipeline to populate.")

# ── Two charts ────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2, gap="large")

with col_l:
    st.subheader("USD / PKR — Trend")
    fig = px.line(
        df.tail(30), x="timestamp", y="usd_pkr_rate",
        markers=True, line_shape="spline",
        color_discrete_sequence=["#1a7a3c"],
        labels={"usd_pkr_rate":"PKR per USD","timestamp":""},
    )
    fig.update_layout(
        margin=dict(l=0,r=0,t=10,b=0),
        paper_bgcolor="white", plot_bgcolor="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#f0f0f0"),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.subheader("Remote Job Volume")
    if "job_volume" in df.columns:
        fig2 = px.area(
            df.tail(30), x="timestamp", y="job_volume",
            color_discrete_sequence=["#C9A84C"],
            labels={"job_volume":"Listings","timestamp":""},
        )
        fig2.update_traces(fill="tozeroy", fillcolor="rgba(201,168,76,0.12)")
        fig2.update_layout(
            margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor="white", plot_bgcolor="white",
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#f0f0f0"),
            hovermode="x unified",
        )
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Quick navigation cards ─────────────────────────────────────────────────
st.subheader("Explore IDMI")
cols = st.columns(5)
nav = [
    ("📊","Dashboard",         "Full historical charts for all tracked indicators"),
    ("💰","Freelancer Tools",  "Multi-currency income calculator with FBR tax"),
    ("🧠","Market Intel",      "Skills radar, demand trends & job analytics"),
    ("💻","Tech Prices",       "Software subscriptions & hardware prices in PKR"),
    ("🤖","STRATOS Chat",      "AI assistant — voice, file & image analysis"),
]
for col,(icon,name,desc) in zip(cols,nav):
    with col:
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #e2e8e4;border-radius:10px;
                    padding:14px 12px;text-align:center;min-height:108px;">
          <div style="font-size:24px;margin-bottom:4px">{icon}</div>
          <div style="font-weight:700;font-size:13px;color:#0d1f15;margin-bottom:4px">{name}</div>
          <div style="font-size:11px;color:#5a7263;line-height:1.4">{desc}</div>
        </div>""", unsafe_allow_html=True)

st.caption(
    f"Last snapshot: {str(latest.get('timestamp',''))[:16]} UTC  ·  "
    "Ingested via GitHub Actions  ·  Stored in Supabase  ·  "
)
