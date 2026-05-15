"""
pages/5_ℹ️_About.py — Project overview and pipeline status.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.db import load_data
from utils.theme import inject_css

st.set_page_config(page_title="About | IDMI", page_icon="ℹ️", layout="wide")
inject_css()

st.title("About IDMI")

col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("""
## What is IDMI?

**Indus Digital Market Intelligence** is a real-time intelligence platform
built for Pakistan's digital economy. It tracks exchange rates, remote job
market trends, and skill demand — synthesising everything into actionable
briefings powered by AI.

## Who is it for?

**Freelancers** on Upwork, Fiverr, and Toptal who need to know the best time
to convert earnings to PKR. **Remote workers** wanting to track which skills
are most in demand globally. **Digital entrepreneurs** monitoring Pakistan's
tech economy. **Students** entering the freelance market who want data to
guide their learning path.

## How it works

A data pipeline runs automatically every 12 hours, pulling live exchange
rates, job market data, and news headlines from multiple sources. The data
is stored in a cloud database and the Streamlit app reads from it in
near-real-time, with a 10-minute cache.

An AI engine called **STRATOS** analyses the freshest snapshot and produces
a concise 3-sentence briefing tailored to Pakistani freelancers — covering
currency outlook, job market trends, and one actionable recommendation.

# STRATOS Chat – Features

- **Session Memory:** Stores full chat history so STRATOS remembers the conversation. Clear Chat resets it.

- **Voice Input:** Uses the browser’s Web Speech API (free, no extra packages). Mic button converts speech to text. Best supported on Chrome & Edge.

- **File Upload:** Supports `.txt`, `.py`, `.md`, `.csv`, `.json`, and `.pdf`. File content is added as context before sending messages.

- **Image Upload:** Supports `.png`, `.jpg`, `.jpeg`, `.webp`. Images are sent to `llama-3.2-11b-vision-preview` for analysis, OCR, chart reading, and review.

- **Market Context:** Injects live Supabase data into prompts for real-time responses.

## Tech Stack

- **Pipeline**: Python, running on GitHub Actions (every 12 hours)
- **Database**: Supabase (PostgreSQL)
- **Frontend**: Streamlit multi-page app
- **Charts**: Plotly Express
- **AI Briefings**: Groq (Llama 3.3 70B)

## Disclaimer

IDMI is for informational purposes only. Nothing on this platform constitutes
financial advice. Exchange rates and market data are provided as-is and may
be delayed. Always verify rates before making financial decisions.
    """)

with col2:
    st.subheader("Pipeline Status")

    df = load_data()
    if not df.empty:
        latest_ts = df.iloc[-1]["timestamp"]
        row_count  = len(df)
        oldest_ts  = df.iloc[0]["timestamp"]

        st.metric("Total snapshots", f"{row_count:,}")
        st.metric("Latest snapshot", str(latest_ts)[:16])
        st.metric("Tracking since",  str(oldest_ts)[:10])

        try:
            now = pd.Timestamp.now(tz="UTC")
            # Ensure latest_ts is timezone-aware before subtraction
            ts = pd.Timestamp(latest_ts)
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
        except Exception as e:
            st.info(f"Latest snapshot: {str(latest_ts)[:16]} UTC")

        st.divider()

        # Sparkline of recent USD/PKR
        if "usd_pkr_rate" in df.columns:
            import plotly.express as px
            spark_df = df.tail(20).dropna(subset=["usd_pkr_rate"])
            if not spark_df.empty:
                fig = px.line(
                    spark_df, x="timestamp", y="usd_pkr_rate",
                    line_shape="spline",
                    color_discrete_sequence=["#1a7a3c"],
                    labels={"usd_pkr_rate": "USD/PKR", "timestamp": ""},
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(gridcolor="rgba(128,128,128,0.15)", tickfont=dict(size=10)),
                    height=150,
                )
                st.caption("USD/PKR — last 20 snapshots")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data in database yet.")
        st.info("Trigger the GitHub Action manually to seed your first snapshot.")
