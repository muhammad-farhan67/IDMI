"""
pages/Market_Intelligence.py — Skills demand, job trends, and platform analytics.
Enhanced with: emerging skills tracking, platform comparison, salary benchmarks.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.db import load_data, get_latest, parse_json_col
from utils.theme import inject_css

st.set_page_config(page_title="Market Intel | IDMI", page_icon="🧠", layout="wide")
inject_css()

st.title("Market Intelligence")
st.caption("Skills demand, job trends, platform analytics, and salary benchmarks — refreshed every pipeline run.")

df      = load_data()
if df.empty:
    st.warning("No data yet. Run the harvester pipeline first.")
    st.stop()

latest  = get_latest(df)
skills  = parse_json_col(latest, "top_skills")

# Live rate for salary conversions
USD_PKR = float(latest.get("usd_pkr_rate") or 280.0)

tab_skills, tab_jobs, tab_platforms, tab_salaries = st.tabs([
    "🔧 Skills Demand",
    "📈 Job Market",
    "⚖️ Platform Comparison",
    "💵 Salary Benchmarks",
])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 — SKILLS DEMAND
# ─────────────────────────────────────────────────────────────────────────
with tab_skills:

    # Current snapshot
    st.subheader("Top In-Demand Skills — Latest Snapshot")
    if skills:
        col_bar, col_radar = st.columns([3, 2], gap="large")
        with col_bar:
            skills_df = pd.DataFrame(skills).sort_values("count", ascending=True)
            fig = px.bar(
                skills_df, x="count", y="skill", orientation="h",
                color="count",
                color_continuous_scale=[[0,"#e8f5ee"],[1,"#01411C"]],
                labels={"count":"Job listings","skill":""},
                text="count",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0,r=0,t=10,b=0),
                coloraxis_showscale=False,
                xaxis=dict(title="Job listings mentioning skill",gridcolor="#f0f0f0"),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_radar:
            top5 = skills_df.tail(5)
            fig_r = go.Figure(go.Scatterpolar(
                r=top5["count"].tolist() + [top5["count"].iloc[0]],
                theta=top5["skill"].tolist() + [top5["skill"].iloc[0]],
                fill="toself", fillcolor="rgba(1,65,28,0.15)",
                line=dict(color="#01411C", width=2),
                name="Demand",
            ))
            fig_r.update_layout(
                polar=dict(
                    radialaxis=dict(showticklabels=False, gridcolor="#e2e8e4"),
                    angularaxis=dict(gridcolor="#e2e8e4"),
                ),
                paper_bgcolor="white",
                margin=dict(l=20,r=20,t=30,b=20),
                showlegend=False,
                height=300,
            )
            st.markdown("**Top 5 — Radar View**")
            st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info("Skills data not available yet. Run the harvester pipeline to populate.")

    st.divider()

    # Skills trend over time
    st.subheader("Skills Trend Over Time")
    st.caption("How demand has changed across pipeline snapshots.")

    if "top_skills" in df.columns:
        records = []
        for _, row in df.iterrows():
            try:
                skill_list = json.loads(row["top_skills"]) if isinstance(row["top_skills"],str) else []
                for s in skill_list:
                    records.append({
                        "timestamp": row["timestamp"],
                        "skill":     s.get("skill",""),
                        "count":     s.get("count",0),
                    })
            except Exception:
                pass

        if records:
            skills_ts  = pd.DataFrame(records)
            all_skills = sorted(skills_ts["skill"].unique())
            default_picks = all_skills[:6] if len(all_skills) >= 6 else all_skills
            picked = st.multiselect("Skills to compare", all_skills, default=default_picks)

            if picked:
                fts = skills_ts[skills_ts["skill"].isin(picked)]
                fig_ts = px.line(
                    fts, x="timestamp", y="count", color="skill",
                    markers=True, line_shape="spline",
                    color_discrete_sequence=px.colors.qualitative.Dark24,
                    labels={"count":"Job listings","timestamp":""},
                )
                fig_ts.update_layout(
                    paper_bgcolor="white", plot_bgcolor="white",
                    margin=dict(l=0,r=0,t=10,b=0),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="#f0f0f0"),
                    legend=dict(orientation="h",yanchor="bottom",y=1.02),
                )
                st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.info("Not enough snapshots yet. More pipeline runs will build the trend data.")
    else:
        st.info("Run the updated harvester to start collecting skills data.")

    st.divider()

    # Static skills heat map — categories vs demand tier
    st.subheader("Skills Landscape for Pakistani Freelancers")
    st.caption("Demand tier and earning potential by skill category (based on global market data).")

    skill_landscape = [
        {"Skill":"Python",          "Category":"Backend",   "Demand":"🔥 Very High","Avg USD/hr":"$35–65", "Learning Curve":"Medium"},
        {"Skill":"React / Next.js",  "Category":"Frontend",  "Demand":"🔥 Very High","Avg USD/hr":"$30–60", "Learning Curve":"Medium"},
        {"Skill":"Node.js",          "Category":"Backend",   "Demand":"🔥 Very High","Avg USD/hr":"$30–55", "Learning Curve":"Medium"},
        {"Skill":"WordPress",        "Category":"CMS",       "Demand":"🔥 Very High","Avg USD/hr":"$15–35", "Learning Curve":"Low"},
        {"Skill":"Shopify",          "Category":"E-Commerce","Demand":"🔥 Very High","Avg USD/hr":"$20–45", "Learning Curve":"Low"},
        {"Skill":"Flutter / Dart",   "Category":"Mobile",    "Demand":"🟠 High",     "Avg USD/hr":"$25–50", "Learning Curve":"Medium"},
        {"Skill":"DevOps / Docker",  "Category":"Infra",     "Demand":"🟠 High",     "Avg USD/hr":"$40–80", "Learning Curve":"High"},
        {"Skill":"AI / ML / LLMs",   "Category":"AI",        "Demand":"🟠 High",     "Avg USD/hr":"$45–90", "Learning Curve":"High"},
        {"Skill":"UI/UX + Figma",    "Category":"Design",    "Demand":"🟡 Medium",   "Avg USD/hr":"$20–45", "Learning Curve":"Medium"},
        {"Skill":"Laravel / PHP",    "Category":"Backend",   "Demand":"🟡 Medium",   "Avg USD/hr":"$15–35", "Learning Curve":"Medium"},
        {"Skill":"Data Analysis",    "Category":"Data",      "Demand":"🟡 Medium",   "Avg USD/hr":"$30–55", "Learning Curve":"Medium"},
        {"Skill":"SEO / Content",    "Category":"Marketing", "Demand":"🟡 Medium",   "Avg USD/hr":"$15–30", "Learning Curve":"Low"},
        {"Skill":"Cybersecurity",    "Category":"Security",  "Demand":"🟡 Medium",   "Avg USD/hr":"$45–85", "Learning Curve":"High"},
        {"Skill":"Graphic Design",   "Category":"Design",    "Demand":"🟡 Medium",   "Avg USD/hr":"$12–28", "Learning Curve":"Low"},
        {"Skill":"Copywriting",      "Category":"Marketing", "Demand":"🟢 Growing",  "Avg USD/hr":"$15–40", "Learning Curve":"Low"},
        {"Skill":"Blockchain/Web3",  "Category":"Emerging",  "Demand":"🟢 Growing",  "Avg USD/hr":"$50–100","Learning Curve":"High"},
    ]
    st.dataframe(
        pd.DataFrame(skill_landscape),
        use_container_width=True, hide_index=True,
    )


# ─────────────────────────────────────────────────────────────────────────
# TAB 2 — JOB MARKET
# ─────────────────────────────────────────────────────────────────────────
with tab_jobs:
    st.subheader("Remote Job Volume Trend")
    col_j1, col_j2 = st.columns([2,1])

    with col_j1:
        if "job_volume" in df.columns:
            fig_jv = px.area(
                df, x="timestamp", y="job_volume",
                color_discrete_sequence=["#1a7a3c"],
                labels={"job_volume":"Live listings","timestamp":""},
            )
            fig_jv.update_traces(fill="tozeroy", fillcolor="rgba(26,122,60,0.10)")
            fig_jv.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#f0f0f0"),
                hovermode="x unified",
            )
            st.plotly_chart(fig_jv, use_container_width=True)

    with col_j2:
        st.markdown("**What this tracks**")
        st.write(
            "Job volume is pulled live from RemoteOK's public API on every "
            "pipeline run — reflecting global remote tech listings. "
            "Higher volume = more competition but also more opportunity."
        )
        if "job_volume" in df.columns and len(df) >= 2:
            curr = int(df.iloc[-1]["job_volume"])
            prev = int(df.iloc[-2]["job_volume"])
            d    = curr - prev
            st.metric("Current listings", f"{curr:,}", f"{d:+,}")
            trend = "market heating up 📈" if d > 0 else "market cooling slightly 📉" if d < 0 else "stable 📊"
            st.caption(f"Trend: {trend}")

    st.divider()

    # Multi-currency rate trend
    st.subheader("Currency Rate Comparison — All Tracked Pairs")
    rate_cols = [c for c in ["usd_pkr_rate","eur_pkr_rate","gbp_pkr_rate",
                              "usdt_pkr_rate","sar_pkr_rate","aed_pkr_rate"]
                 if c in df.columns and df[c].notna().any()]

    if rate_cols:
        label_map = {
            "usd_pkr_rate":"USD/PKR","eur_pkr_rate":"EUR/PKR",
            "gbp_pkr_rate":"GBP/PKR","usdt_pkr_rate":"USDT/PKR",
            "sar_pkr_rate":"SAR/PKR","aed_pkr_rate":"AED/PKR",
        }
        df_m = df[["timestamp"]+rate_cols].melt(
            id_vars="timestamp", var_name="Pair", value_name="PKR Rate"
        )
        df_m["Pair"] = df_m["Pair"].map(label_map)

        selected_pairs = st.multiselect(
            "Currency pairs to display",
            list(df_m["Pair"].unique()),
            default=list(df_m["Pair"].unique()),
        )
        if selected_pairs:
            fig_mc = px.line(
                df_m[df_m["Pair"].isin(selected_pairs)],
                x="timestamp", y="PKR Rate", color="Pair",
                line_shape="spline",
                color_discrete_sequence=["#1a7a3c","#C9A84C","#2563eb",
                                          "#0891b2","#dc2626","#7c3aed"],
                labels={"PKR Rate":"PKR","timestamp":""},
            )
            fig_mc.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#f0f0f0"),
                legend=dict(orientation="h",yanchor="bottom",y=1.02),
                hovermode="x unified",
            )
            st.plotly_chart(fig_mc, use_container_width=True)

    st.divider()
    st.subheader("STRATOS — Latest Briefing")
    st.info(f"🧠 {latest.get('ai_sentiment','No insight yet — run the pipeline.')}")


# ─────────────────────────────────────────────────────────────────────────
# TAB 3 — PLATFORM COMPARISON
# ─────────────────────────────────────────────────────────────────────────
with tab_platforms:
    st.subheader("Freelance Platform Comparison")
    st.caption("Which platform is best for your skill set and earnings level?")

    platforms_data = [
        {
            "Platform":   "Upwork",
            "Fee":        "5–20% (tiered)",
            "Best for":   "Long-term contracts, agencies, enterprise clients",
            "Min viable rate": "$20/hr",
            "Payment":    "Wire, PayPal, Payoneer, Direct Debit",
            "PK Friendly":"✅ Yes — Payoneer widely used",
            "Competition":"Very High",
            "Avg contract":"$500–$5,000",
        },
        {
            "Platform":   "Fiverr",
            "Fee":        "20% flat",
            "Best for":   "Packaged gigs, quick deliveries, creative work",
            "Min viable rate": "$15/gig",
            "Payment":    "PayPal, Payoneer, bank transfer",
            "PK Friendly":"✅ Yes — Payoneer common",
            "Competition":"Very High",
            "Avg contract":"$50–$500",
        },
        {
            "Platform":   "Toptal",
            "Fee":        "0% to freelancer",
            "Best for":   "Senior devs, designers, finance experts",
            "Min viable rate": "$60/hr",
            "Payment":    "Wire transfer",
            "PK Friendly":"⚠️ Limited — wire preferred",
            "Competition":"Low (invite only)",
            "Avg contract":"$5,000+",
        },
        {
            "Platform":   "Contra",
            "Fee":        "0% commission",
            "Best for":   "Designers, writers, modern tech stack devs",
            "Min viable rate": "$25/hr",
            "Payment":    "Stripe, bank transfer",
            "PK Friendly":"⚠️ Stripe limited in PK",
            "Competition":"Medium",
            "Avg contract":"$500–$3,000",
        },
        {
            "Platform":   "Freelancer.com",
            "Fee":        "10% or $5 min",
            "Best for":   "Low-cost markets, entry-level, bulk projects",
            "Min viable rate": "$5/hr",
            "Payment":    "PayPal, Skrill, wire",
            "PK Friendly":"✅ Yes",
            "Competition":"Extreme",
            "Avg contract":"$50–$300",
        },
        {
            "Platform":   "PeoplePerHour",
            "Fee":        "20% then 7.5%",
            "Best for":   "UK/EU clients, writing, design",
            "Min viable rate": "$15/hr",
            "Payment":    "PayPal, Payoneer",
            "PK Friendly":"✅ Yes",
            "Competition":"High",
            "Avg contract":"$200–$1,500",
        },
        {
            "Platform":   "LinkedIn ProFinder",
            "Fee":        "0%",
            "Best for":   "Consulting, senior professionals",
            "Min viable rate": "$50/hr",
            "Payment":    "Direct with client",
            "PK Friendly":"⚠️ Network-dependent",
            "Competition":"Medium",
            "Avg contract":"$1,000+",
        },
        {
            "Platform":   "Guru",
            "Fee":        "5–9% (tiered)",
            "Best for":   "Tech, writing, admin",
            "Min viable rate": "$10/hr",
            "Payment":    "PayPal, wire, e-check",
            "PK Friendly":"✅ Yes",
            "Competition":"High",
            "Avg contract":"$200–$1,000",
        },
    ]

    st.dataframe(
        pd.DataFrame(platforms_data),
        use_container_width=True, hide_index=True,
    )

    st.divider()

    # Fee comparison chart
    st.subheader("Platform Fee Comparison — on $1,000 earned")
    fee_data = [
        ("Upwork",       upwork_calc := (100 + 950*0.10 + 0*0.05), upwork_calc),
        ("Fiverr",       200.0, 200.0),
        ("Freelancer",   100.0, 100.0),
        ("PeoplePerHour",200.0, 200.0),
        ("Contra",       0.0,   0.0),
        ("Toptal",       0.0,   0.0),
        ("Guru",         90.0,  90.0),
    ]
    # fix upwork: on $1000 → first 500 @ 20% = 100, next 500 @ 10% = 50 → 150
    fee_data[0] = ("Upwork", 150.0, 150.0)

    fee_df = pd.DataFrame([{"Platform":n,"Fee $":f,"Net $":1000-f} for n,f,_ in fee_data])
    fig_fee = px.bar(
        fee_df.sort_values("Fee $",ascending=False),
        x="Platform", y=["Fee $","Net $"],
        barmode="stack",
        color_discrete_map={"Fee $":"#ef4444","Net $":"#1a7a3c"},
        labels={"value":"USD","variable":""},
    )
    fig_fee.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0,r=0,t=10,b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#f0f0f0"),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_fee, use_container_width=True)

    def upwork_calc(x): return x  # placeholder fix
    st.caption(
        "Upwork fee on $1,000: first $500 @ 20% ($100) + next $500 @ 10% ($50) = $150 total. "
        "Fee drops to 5% after $10,000 lifetime with a client."
    )


# ─────────────────────────────────────────────────────────────────────────
# TAB 4 — SALARY BENCHMARKS
# ─────────────────────────────────────────────────────────────────────────
with tab_salaries:
    st.subheader("Freelance Rate Benchmarks")
    st.caption(
        f"Hourly rates in USD and equivalent monthly PKR at live rate ₨ {USD_PKR:,.1f}/USD. "
        "Assumes 160 billable hours/month."
    )

    HOURS = 160

    salary_data = [
        # Role, USD low, USD high, experience
        ("Frontend Dev (React)",      15, 65, "1–7 yrs"),
        ("Backend Dev (Python/Node)", 20, 80, "1–8 yrs"),
        ("Full Stack Dev",            25, 90, "2–8 yrs"),
        ("Mobile Dev (Flutter)",      20, 70, "1–6 yrs"),
        ("WordPress Dev",             10, 40, "1–5 yrs"),
        ("Shopify Dev",               15, 55, "1–5 yrs"),
        ("DevOps / Cloud Eng",        35, 100,"2–8 yrs"),
        ("ML / AI Engineer",          40, 120,"2–8 yrs"),
        ("UI/UX Designer",            15, 55, "1–7 yrs"),
        ("Graphic Designer",          10, 35, "1–6 yrs"),
        ("Data Analyst",              20, 60, "1–6 yrs"),
        ("Cybersecurity",             35, 90, "2–7 yrs"),
        ("SEO Specialist",            12, 40, "1–5 yrs"),
        ("Content Writer",            10, 35, "1–5 yrs"),
        ("Video Editor",              12, 45, "1–5 yrs"),
        ("Smart Contract Dev",        50, 120,"2–6 yrs"),
        ("Technical Writer",          20, 55, "1–5 yrs"),
        ("QA Engineer",               15, 50, "1–5 yrs"),
    ]

    rows = []
    for role, lo, hi, exp in salary_data:
        mid = (lo + hi) / 2
        rows.append({
            "Role":               role,
            "Experience":         exp,
            "USD/hr (range)":     f"${lo}–${hi}",
            "Monthly USD (mid)":  f"${mid*HOURS:,.0f}",
            "Monthly PKR (low)":  f"₨ {lo*HOURS*USD_PKR:,.0f}",
            "Monthly PKR (mid)":  f"₨ {mid*HOURS*USD_PKR:,.0f}",
            "Monthly PKR (high)": f"₨ {hi*HOURS*USD_PKR:,.0f}",
            "_mid": mid*HOURS,
        })

    sal_df = pd.DataFrame(rows)
    st.dataframe(
        sal_df.drop(columns=["_mid"]),
        use_container_width=True, hide_index=True,
    )

    st.divider()

    # Visual — mid monthly PKR per role
    fig_sal = px.bar(
        sal_df.sort_values("_mid"),
        x="_mid", y="Role", orientation="h",
        color="_mid",
        color_continuous_scale=[[0,"#e8f5ee"],[1,"#01411C"]],
        labels={"_mid":"Monthly USD (mid-rate)","Role":""},
        text=sal_df.sort_values("_mid")["Monthly PKR (mid)"],
    )
    fig_sal.update_traces(textposition="outside")
    fig_sal.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0,r=0,t=10,b=40),
        coloraxis_showscale=False,
        xaxis=dict(title="Monthly USD (mid-range rate)",gridcolor="#f0f0f0"),
        yaxis=dict(showgrid=False),
        height=540,
    )
    st.plotly_chart(fig_sal, use_container_width=True)

    st.caption(
        "Rates are global market ranges for remote freelancers, sourced from "
        "Upwork, Glassdoor Remote, and RemoteOK job data. Actual rates depend "
        "on experience, portfolio, and client location. "
        f"PKR values use live rate ₨ {USD_PKR:,.1f}/USD from IDMI pipeline."
    )
