"""
pages/About.py — Project overview, STRATOS engine details, pipeline status.
v3.0: Updated with full platform description, STRATOS engine briefing explanation,
      detailed tech stack, and pipeline health monitor.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.db import load_data, get_latest, parse_json_col
from utils.theme import inject_css

st.set_page_config(page_title="About | IDMI", page_icon="ℹ️", layout="wide")
inject_css()

st.title("About IDMI")
st.caption("Indus Digital Market Intelligence — Pakistan's freelancer intelligence platform")

col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("""
## What is IDMI?

**Indus Digital Market Intelligence (IDMI)** is a real-time intelligence platform built for Pakistan's digital economy. It tracks exchange rates, live remote job listings, software prices in PKR, and AI-powered market briefings — all on 100% free-tier infrastructure.

## Who is it for?

- **Freelancers** on Upwork, Fiverr, and Toptal who need to know the best time to convert USD earnings to PKR
- **Remote workers** tracking which tech skills are most in demand globally right now
- **Digital entrepreneurs** monitoring Pakistan's tech economy and software costs in PKR
- **Students** entering the freelance market who want real data to guide their skill choices

## How the Data Pipeline Works

A Python pipeline runs automatically via **GitHub Actions every 12 hours**, pulling:

- **Exchange rates** — USD, EUR, GBP, SAR, AED, USDT, BTC vs PKR from open APIs
- **Live remote jobs** — Full job listings from RemoteOK (title, company, salary, skills, apply link) with skill demand analytics
- **Tech prices** — Curated software subscriptions and hardware prices, auto-converted to PKR at the live exchange rate
- **News headlines** — RSS feeds from ProPakistani, Profit Pakistan, Hacker News, TechCrunch, The Verge, and Ars Technica

All data is stored in **Supabase (PostgreSQL)** and the Streamlit app reads from it with a 10-minute cache.
""")

    st.divider()

    st.markdown("""
## 🧠 The STRATOS Engine

**STRATOS** (Strategic Tracking and Reporting AI for Opportunistic Signals) is the AI engine powering IDMI's intelligence layer. It appears in three places:

### 1. Automated Market Briefing
After every pipeline run, STRATOS analyses the freshest snapshot — exchange rates, live job titles, top skill demand, and news headlines — and generates a structured 3-part briefing:

> **Currency Outlook** — Is now a good time to invoice in USD, hold dollars, or convert?
>
> **Job Market** — Which specific skills and roles are seeing live demand right now?
>
> **Action Item** — One concrete, data-backed recommendation for this week.

The briefing is stored in Supabase and displayed on the Home page, Market Intelligence page, and the STRATOS Chat sidebar.

### 2. STRATOS Chat
The interactive chat assistant on the STRATOS Chat page has access to all live IDMI data — exchange rates, actual job listings and titles, top skill demand, news headlines, and tech prices in PKR — injected into every response. Ask it anything about Pakistan's digital economy.

### 3. Tech Price AI Search
The AI Price Search tab on the Tech Prices page lets you ask STRATOS about any software or hardware price, including Pakistani availability, import advice, and alternatives — using the live USD/PKR rate.

## Features

- **Live Job Listings** — Search and filter 60+ live remote jobs from RemoteOK with salary info and direct Apply links
- **Software Prices in PKR** — 50+ tools with live PKR conversion and direct "Visit Site" links
- **Hardware Prices** — Popular devices with PKR conversion and Amazon search links
- **Skills Radar** — Top 10 in-demand skills with historical trend charts
- **Platform Comparison** — Upwork vs Fiverr vs Toptal vs Contra with fee analysis
- **Salary Benchmarks** — 18 roles with USD/hr ranges and live PKR monthly equivalents
- **Income Calculator** — Multi-currency income with FBR tax brackets (Freelancer Tools page)
- **Voice Input** — Browser-native speech-to-text in STRATOS Chat (Chrome/Edge)
- **File & Image Analysis** — Upload PDFs, code files, CSV, or images for STRATOS to analyse

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Pipeline** | Python 3.11, GitHub Actions (every 12h) |
| **Database** | Supabase (PostgreSQL, free tier) |
| **Frontend** | Streamlit multi-page app |
| **Charts** | Plotly Express |
| **AI Engine** | Groq API — Llama 3.3 70B (text), Llama 3.2 11B Vision (images) |
| **Exchange Rates** | open.er-api.com (free tier) |
| **Crypto Prices** | CoinGecko API (free tier) |
| **Job Data** | RemoteOK public API |
| **News** | RSS feeds via feedparser |
| **Hosting** | Streamlit Community Cloud (free) |

## Disclaimer

IDMI is for informational purposes only. Nothing on this platform constitutes financial advice. Exchange rates and market data are provided as-is and may be delayed. Always verify rates before making financial decisions.
""")

with col2:
    st.subheader("Pipeline Status")

    df = load_data()
    if not df.empty:
        latest    = get_latest(df)
        latest_ts = df.iloc[-1]["timestamp"]
        row_count = len(df)
        oldest_ts = df.iloc[0]["timestamp"]

        st.metric("Total snapshots",    f"{row_count:,}")
        st.metric("Latest snapshot",    str(latest_ts)[:16])
        st.metric("Tracking since",     str(oldest_ts)[:10])
        st.metric("Remote jobs tracked",
                  f"{int(latest.get('job_volume', 0)):,}" if latest.get("job_volume") else "—")

        # Jobs detail availability
        jobs_data = parse_json_col(latest, "jobs_data")
        if jobs_data:
            st.success(f"✓ {len(jobs_data)} detailed job records available")
        else:
            st.warning("⚠ Run v3.0 harvester to collect detailed job records")

        # Pipeline health
        try:
            now = pd.Timestamp.now(tz="UTC")
            ts  = pd.Timestamp(latest_ts)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            else:
                ts = ts.tz_convert("UTC")
            age         = now - ts
            minutes_old = int(age.total_seconds() / 60)

            if minutes_old < 75:
                st.success(f"✓ Pipeline healthy — last run {minutes_old}m ago")
            elif minutes_old < 180:
                st.warning(f"⚠ Last run was {minutes_old}m ago — pipeline may be delayed")
            else:
                hours_old = minutes_old // 60
                st.error(f"✗ Last run was {hours_old}h ago — check GitHub Actions logs")
        except Exception:
            st.info(f"Latest snapshot: {str(latest_ts)[:16]} UTC")

        st.divider()

        # Current rates snapshot
        st.subheader("Current Rates")
        r1, r2 = st.columns(2)
        r1.metric("USD/PKR", f"₨ {latest.get('usd_pkr_rate','—')}")
        r2.metric("EUR/PKR", f"₨ {latest.get('eur_pkr_rate','—')}")
        r3, r4 = st.columns(2)
        r3.metric("GBP/PKR", f"₨ {latest.get('gbp_pkr_rate','—')}")
        r4.metric("BTC/USD",
                  f"${int(latest.get('btc_usd_rate',0)):,}" if latest.get("btc_usd_rate") else "—")

        st.divider()

        # Top skills
        skills = parse_json_col(latest, "top_skills")
        if skills:
            st.subheader("Top In-Demand Skills")
            for s in skills[:5]:
                bar_pct = min(100, int(s["count"] / max(sk["count"] for sk in skills) * 100))
                st.markdown(
                    f'<div style="margin-bottom:4px">'
                    f'<span style="font-size:13px;font-weight:600;color:#0d1f15">{s["skill"]}</span>'
                    f'<span style="font-size:12px;color:#5a7263;float:right">{s["count"]} listings</span>'
                    f'</div>'
                    f'<div style="background:#e8f5ee;border-radius:4px;height:6px;margin-bottom:8px;">'
                    f'<div style="background:#01411C;width:{bar_pct}%;height:6px;border-radius:4px;"></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.divider()

        # USD/PKR sparkline
        if "usd_pkr_rate" in df.columns:
            import plotly.express as px
            spark_df = df.tail(20).dropna(subset=["usd_pkr_rate"])
            if not spark_df.empty:
                fig = px.line(
                    spark_df, x="timestamp", y="usd_pkr_rate",
                    line_shape="spline",
                    color_discrete_sequence=["#1a7a3c"],
                    labels={"usd_pkr_rate":"USD/PKR","timestamp":""},
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0,r=0,t=10,b=0),
                    xaxis=dict(showgrid=False,showticklabels=False),
                    yaxis=dict(gridcolor="rgba(128,128,128,0.15)",tickfont=dict(size=10)),
                    height=150,
                )
                st.caption("USD/PKR — last 20 snapshots")
                st.plotly_chart(fig, use_container_width=True)

        # Latest STRATOS briefing
        briefing = latest.get("ai_sentiment","")
        if briefing:
            st.divider()
            st.subheader("🧠 Latest STRATOS Briefing")
            for line in briefing.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith("Currency Outlook:"):
                    st.markdown(
                        f"<div style='background:#f0fdf4;border-left:3px solid #16a34a;"
                        f"padding:8px 12px;border-radius:5px;margin-bottom:6px;font-size:12px;'>"
                        f"<strong style='color:#15803d'>💱</strong> "
                        f"{line.replace('Currency Outlook:','').strip()}</div>",
                        unsafe_allow_html=True,
                    )
                elif line.startswith("Job Market:"):
                    st.markdown(
                        f"<div style='background:#fffbeb;border-left:3px solid #d97706;"
                        f"padding:8px 12px;border-radius:5px;margin-bottom:6px;font-size:12px;'>"
                        f"<strong style='color:#b45309'>📋</strong> "
                        f"{line.replace('Job Market:','').strip()}</div>",
                        unsafe_allow_html=True,
                    )
                elif line.startswith("Action Item:"):
                    st.markdown(
                        f"<div style='background:#eff6ff;border-left:3px solid #2563eb;"
                        f"padding:8px 12px;border-radius:5px;margin-bottom:6px;font-size:12px;'>"
                        f"<strong style='color:#1d4ed8'>⚡</strong> "
                        f"{line.replace('Action Item:','').strip()}</div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.warning("No data in database yet.")
        st.info("Trigger the GitHub Action manually to seed your first snapshot.")
