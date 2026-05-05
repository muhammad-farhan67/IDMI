"""
pages/3_🧠_Market_Intelligence.py — Skills demand radar + job market trends.
Parses the top_skills JSON stored by harvester v2.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from collections import defaultdict
from utils.db import load_data, get_latest, parse_json_col
from utils.theme import inject_css

st.set_page_config(page_title="Market Intel | IDMI", page_icon="🧠", layout="wide")
inject_css()

st.title("Market Intelligence")
st.caption("Skills demand, job trends, and platform insights — updated every pipeline run.")

df = load_data()
if df.empty:
    st.warning("No data yet.")
    st.stop()

latest  = get_latest(df)
skills  = parse_json_col(latest, "top_skills")

# ── Skills demand — latest snapshot ───────────────────────────────────────
st.subheader("Top In-Demand Skills — Latest Snapshot")

if skills:
    col_bar, col_radar = st.columns([3, 2], gap="large")

    with col_bar:
        skills_df = pd.DataFrame(skills).sort_values("count", ascending=True)
        fig = px.bar(
            skills_df, x="count", y="skill", orientation="h",
            color="count",
            color_continuous_scale=[[0, "#e8f5ee"], [1, "#01411C"]],
            labels={"count": "Job listings", "skill": ""},
        )
        fig.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False,
            xaxis=dict(title="Job listings mentioning skill", gridcolor="#f0f0f0"),
            yaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_radar:
        top5 = skills_df.tail(5)
        fig_r = go.Figure(go.Scatterpolar(
            r=top5["count"].tolist() + [top5["count"].iloc[0]],
            theta=top5["skill"].tolist() + [top5["skill"].iloc[0]],
            fill="toself",
            fillcolor="rgba(1,65,28,0.15)",
            line=dict(color="#01411C", width=2),
        ))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(showticklabels=False, gridcolor="#e2e8e4"),
                       angularaxis=dict(gridcolor="#e2e8e4")),
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
        )
        st.markdown("**Top 5 — Radar View**")
        st.plotly_chart(fig_r, use_container_width=True)
else:
    st.info("Skills data not available yet. Run the harvester pipeline to populate this section.")

st.divider()

# ── Skills trend over time ─────────────────────────────────────────────────
st.subheader("Skills Trend Over Time")
st.caption("How skill demand has changed across pipeline snapshots.")

# Build a skills-over-time dataframe from the JSON column
if "top_skills" in df.columns:
    records = []
    for _, row in df.iterrows():
        try:
            skill_list = json.loads(row["top_skills"]) if isinstance(row["top_skills"], str) else []
            for s in skill_list:
                records.append({
                    "timestamp": row["timestamp"],
                    "skill": s.get("skill", ""),
                    "count": s.get("count", 0),
                })
        except Exception:
            pass

    if records:
        skills_ts = pd.DataFrame(records)

        # Let user pick skills to compare
        all_skills = sorted(skills_ts["skill"].unique())
        default_picks = all_skills[:5] if len(all_skills) >= 5 else all_skills
        picked = st.multiselect("Skills to compare", all_skills, default=default_picks)

        if picked:
            filtered_ts = skills_ts[skills_ts["skill"].isin(picked)]
            fig_ts = px.line(
                filtered_ts, x="timestamp", y="count", color="skill",
                markers=True, line_shape="spline",
                color_discrete_sequence=px.colors.qualitative.Dark24,
                labels={"count": "Job listings", "timestamp": ""},
            )
            fig_ts.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#f0f0f0"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("Not enough snapshots yet to draw a trend. Check back after more pipeline runs.")
else:
    st.info("Run the updated harvester to start collecting skills data.")

st.divider()

# ── Job volume trend ───────────────────────────────────────────────────────
st.subheader("Remote Job Volume Trend")
col_j1, col_j2 = st.columns([2, 1])

with col_j1:
    if "job_volume" in df.columns:
        fig_jv = px.area(
            df, x="timestamp", y="job_volume",
            color_discrete_sequence=["#1a7a3c"],
            labels={"job_volume": "Live listings", "timestamp": ""},
        )
        fig_jv.update_traces(fill="tozeroy", fillcolor="rgba(26,122,60,0.1)")
        fig_jv.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#f0f0f0"),
        )
        st.plotly_chart(fig_jv, use_container_width=True)

with col_j2:
    st.markdown("**What this measures**")
    st.write(
        "Live job count is pulled from RemoteOK's free public API every "
        "pipeline run. It reflects the total number of active remote tech "
        "listings globally — a proxy for how hot the market is for Pakistani "
        "remote workers at any given moment."
    )
    if "job_volume" in df.columns and len(df) >= 2:
        current  = int(df.iloc[-1]["job_volume"])
        previous = int(df.iloc[-2]["job_volume"])
        delta    = current - previous
        trend    = "▲ up" if delta > 0 else "▼ down" if delta < 0 else "→ flat"
        st.metric("Current listings", f"{current:,}", f"{delta:+,} vs last snapshot")
        st.caption(f"Market is {trend} from last check.")

st.divider()

# ── Insight callout ────────────────────────────────────────────────────────
st.subheader("STRATOS — Skills Briefing")
st.info(f"🧠  {latest.get('ai_sentiment', 'No insight available. Run the pipeline.')}")
