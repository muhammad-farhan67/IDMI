"""
pages/5_ℹ️_About.py — Project overview and data source transparency.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from utils.db import load_data
from utils.theme import inject_css

st.set_page_config(page_title="About | IDMI", page_icon="ℹ️", layout="wide")
inject_css()

st.title("About IDMI")

col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("""
## What is IDMI?

**Indus Digital Market Intelligence** is a free, open-source market intelligence 
platform built for Pakistan's growing digital economy. It tracks real-time 
exchange rates, remote job market trends, and skill demand — and synthesises 
everything into actionable briefings using AI.

It is built and maintained entirely on free-tier services.

## Who is it for?

- **Freelancers** on Upwork, Fiverr, and Toptal who need to know the best time 
  to convert USD to PKR.
- **Remote workers** wanting to track which skills are most in demand globally.
- **Digital entrepreneurs** monitoring Pakistan's tech economy.
- **Students** entering the freelance market who want data to guide their learning.

## Data Sources

All data is collected automatically every hour via a GitHub Actions pipeline.

| Source | What it provides | Cost |
|---|---|---|
| open.er-api.com | USD, EUR, GBP, SAR, AED rates | Free, no API key |
| CoinGecko API | USDT and BTC prices | Free, no API key |
| RemoteOK API | Live remote job listings + skill tags | Free, no API key |
| Dawn.com RSS | Pakistan tech news | Free, public RSS |
| The News RSS | Pakistan business news | Free, public RSS |
| ProPakistani RSS | Pakistan tech news | Free, public RSS |
| Groq API (Llama 3.3) | AI market briefings | Free tier |
| Supabase | Database storage | Free tier (500MB) |
| GitHub Actions | Hourly data pipeline | Free tier (2000 min/mo) |
| Streamlit Community Cloud | App hosting | Free |

**Total monthly cost: ₨ 0**

## Tech Stack

- **Backend pipeline**: Python · `requests` · `feedparser` · `groq`
- **Database**: Supabase (PostgreSQL)
- **Frontend**: Streamlit multi-page app
- **Charts**: Plotly Express
- **CI/CD**: GitHub Actions (hourly cron)

## Open Source

The full source code is available on GitHub. Contributions welcome.
    """)

with col2:
    st.subheader("Pipeline Status")

    df = load_data()
    if not df.empty:
        latest_ts = df.iloc[-1]["timestamp"]
        row_count = len(df)
        oldest_ts = df.iloc[0]["timestamp"]

        st.metric("Total snapshots", f"{row_count:,}")
        st.metric("Latest snapshot", str(latest_ts)[:16])
        st.metric("Tracking since", str(oldest_ts)[:10])

        import pandas as pd
        from datetime import datetime, timezone
        now = pd.Timestamp.now(tz="UTC")
        age = now - pd.Timestamp(latest_ts, tz="UTC")
        minutes_old = int(age.total_seconds() / 60)

        if minutes_old < 75:
            st.success(f"✓ Pipeline healthy — last run {minutes_old}m ago")
        elif minutes_old < 180:
            st.warning(f"⚠ Last run was {minutes_old}m ago — pipeline may be delayed")
        else:
            st.error(f"✗ Last run was {minutes_old}m ago — check GitHub Actions")
    else:
        st.warning("No data in database yet.")

    st.divider()
    st.subheader("Disclaimer")
    st.caption(
        "IDMI is for informational purposes only. Nothing on this platform "
        "constitutes financial advice. Exchange rates and market data are "
        "provided as-is and may be delayed. Always verify rates before making "
        "financial decisions."
    )
