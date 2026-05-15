"""
pages/Market_Intelligence.py — Skills demand, job trends, platform analytics.
v3.0: Tab 2 now shows live job listings with search + Apply links.
       STRATOS briefing shown in structured format everywhere.
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
st.caption("Skills demand, live job listings, platform analytics, and salary benchmarks — refreshed every pipeline run.")

df     = load_data()
if df.empty:
    st.warning("No data yet. Run the harvester pipeline first.")
    st.stop()

latest = get_latest(df)
skills = parse_json_col(latest, "top_skills")

# Live rate for salary conversions
USD_PKR = float(latest.get("usd_pkr_rate") or 280.0)

tab_skills, tab_jobs, tab_platforms, tab_salaries = st.tabs([
    "🔧 Skills Demand",
    "📋 Live Job Listings",
    "⚖️ Platform Comparison",
    "💵 Salary Benchmarks",
])


# ─────────────────────────────────────────────────────────────────────────
# TAB 1 — SKILLS DEMAND
# ─────────────────────────────────────────────────────────────────────────
with tab_skills:

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

    st.divider()

    # Static skills landscape
    st.subheader("Skills Landscape for Pakistani Freelancers")
    st.caption("Demand tier and earning potential by skill category (based on global market data).")

    skill_landscape = [
        {"Skill":"Python",          "Category":"Backend",   "Demand":"🔥 Very High","Avg USD/hr":"$35–65", "Learning Curve":"Medium"},
        {"Skill":"React / Next.js", "Category":"Frontend",  "Demand":"🔥 Very High","Avg USD/hr":"$30–60", "Learning Curve":"Medium"},
        {"Skill":"Node.js",         "Category":"Backend",   "Demand":"🔥 Very High","Avg USD/hr":"$30–55", "Learning Curve":"Medium"},
        {"Skill":"WordPress",       "Category":"CMS",       "Demand":"🔥 Very High","Avg USD/hr":"$15–35", "Learning Curve":"Low"},
        {"Skill":"Shopify",         "Category":"E-Commerce","Demand":"🔥 Very High","Avg USD/hr":"$20–45", "Learning Curve":"Low"},
        {"Skill":"Flutter / Dart",  "Category":"Mobile",    "Demand":"🟠 High",     "Avg USD/hr":"$25–50", "Learning Curve":"Medium"},
        {"Skill":"DevOps / Docker", "Category":"Infra",     "Demand":"🟠 High",     "Avg USD/hr":"$40–80", "Learning Curve":"High"},
        {"Skill":"AI / ML / LLMs",  "Category":"AI",        "Demand":"🟠 High",     "Avg USD/hr":"$45–90", "Learning Curve":"High"},
        {"Skill":"UI/UX + Figma",   "Category":"Design",    "Demand":"🟡 Medium",   "Avg USD/hr":"$20–45", "Learning Curve":"Medium"},
        {"Skill":"Laravel / PHP",   "Category":"Backend",   "Demand":"🟡 Medium",   "Avg USD/hr":"$15–35", "Learning Curve":"Medium"},
        {"Skill":"Data Analysis",   "Category":"Data",      "Demand":"🟡 Medium",   "Avg USD/hr":"$30–55", "Learning Curve":"Medium"},
        {"Skill":"SEO / Content",   "Category":"Marketing", "Demand":"🟡 Medium",   "Avg USD/hr":"$15–30", "Learning Curve":"Low"},
        {"Skill":"Cybersecurity",   "Category":"Security",  "Demand":"🟡 Medium",   "Avg USD/hr":"$45–85", "Learning Curve":"High"},
        {"Skill":"Graphic Design",  "Category":"Design",    "Demand":"🟡 Medium",   "Avg USD/hr":"$12–28", "Learning Curve":"Low"},
        {"Skill":"Copywriting",     "Category":"Marketing", "Demand":"🟢 Growing",  "Avg USD/hr":"$15–40", "Learning Curve":"Low"},
        {"Skill":"Blockchain/Web3", "Category":"Emerging",  "Demand":"🟢 Growing",  "Avg USD/hr":"$50–100","Learning Curve":"High"},
    ]
    st.dataframe(
        pd.DataFrame(skill_landscape),
        use_container_width=True, hide_index=True,
    )


# ─────────────────────────────────────────────────────────────────────────
# TAB 2 — LIVE JOB LISTINGS
# ─────────────────────────────────────────────────────────────────────────
with tab_jobs:

    

    # ── Live job listings with search ────────────────────────────────────
    st.subheader("🔍 Search Live Remote Jobs")
    st.caption("Jobs pulled from RemoteOK. Click **Apply Now** to open the job on RemoteOK.")

    raw_jobs = parse_json_col(latest, "jobs_data")

    if not raw_jobs:
        st.info(
            "Job listings data not available yet — run the updated v3.0 harvester "
            "pipeline to start collecting detailed job records."
        )
    else:
        # ── Search & filter controls ──────────────────────────────────────
        fj1, fj2, fj3 = st.columns([3, 2, 1])
        with fj1:
            job_search = st.text_input(
                "Search jobs",
                placeholder="e.g. Python, React, Flutter, DevOps…",
                label_visibility="collapsed",
            )
        with fj2:
            all_job_tags = sorted({
                tag
                for j in raw_jobs
                for tag in j.get("tags", [])
            })
            tag_filter = st.multiselect("Filter by skill tag", all_job_tags, default=[], key="job_tag_filter")
        with fj3:
            salary_only = st.toggle("Salary listed", value=False)

        # ── Filter jobs ───────────────────────────────────────────────────
        filtered_jobs = []
        search_lower  = job_search.lower().strip()
        for j in raw_jobs:
            title   = j.get("title", "").lower()
            company = j.get("company", "").lower()
            tags    = [t.lower() for t in j.get("tags", [])]

            if search_lower and search_lower not in title and search_lower not in company \
                    and not any(search_lower in t for t in tags):
                continue
            if tag_filter and not any(t in tags for t in [x.lower() for x in tag_filter]):
                continue
            if salary_only and not j.get("salary"):
                continue
            filtered_jobs.append(j)

        st.caption(
            f"Showing **{len(filtered_jobs)}** of **{len(raw_jobs)}** live listings "
            f"· Last snapshot: {str(latest.get('timestamp',''))[:16]} UTC"
        )

        # ── Render jobs as cards ─────────────────────────────────────────
        if not filtered_jobs:
            st.info("No jobs match your filters. Try a different keyword or clear the filters.")
        else:
            # Paginate: show 15 at a time
            PAGE_SIZE = 15
            if "job_page" not in st.session_state:
                st.session_state.job_page = 0

            # Reset page on new search
            total_pages = max(1, (len(filtered_jobs) + PAGE_SIZE - 1) // PAGE_SIZE)
            page = st.session_state.job_page
            if page >= total_pages:
                page = 0
                st.session_state.job_page = 0

            page_jobs = filtered_jobs[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

            for j in page_jobs:
                salary_badge = (
                    f'<span style="background:#d1fae5;color:#065f46;padding:2px 8px;'
                    f'border-radius:12px;font-size:11px;font-weight:600;">'
                    f'💰 {j["salary"]}</span>'
                ) if j.get("salary") else ""

                tags_html = " ".join([
                    f'<span style="background:#f0f4f8;color:#374151;padding:2px 7px;'
                    f'border-radius:10px;font-size:11px;">{t}</span>'
                    for t in j.get("tags", [])[:6]
                ])

                st.markdown(
                    f"""
                    <div style="border:1px solid #e2e8e4;border-radius:10px;padding:14px 18px;
                                margin-bottom:8px;background:#fff;">
                      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px;">
                        <div>
                          <div style="font-weight:700;font-size:15px;color:#0d1f15;">{j.get('title','')}</div>
                          <div style="font-size:13px;color:#5a7263;margin-top:2px;">
                            🏢 {j.get('company','')}
                            &nbsp;·&nbsp; 🌍 {j.get('location','Worldwide')}
                            {'&nbsp;·&nbsp; 📅 ' + j['date'] if j.get('date') else ''}
                          </div>
                        </div>
                        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                          {salary_badge}
                        </div>
                      </div>
                      <div style="margin-top:8px;">{tags_html}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Apply button
                apply_url = j.get("url", "https://remoteok.com/remote-jobs")
                st.markdown(
                    f'<a href="{apply_url}" target="_blank" style="'
                    f'display:inline-block;margin-top:-4px;margin-bottom:4px;'
                    f'padding:4px 14px;background:#01411C;color:#fff;border-radius:8px;'
                    f'font-size:12px;font-weight:600;text-decoration:none;">'
                    f'Apply on RemoteOK ↗</a>',
                    unsafe_allow_html=True,
                )

            # Pagination controls
            if total_pages > 1:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                p1, p2, p3 = st.columns([1, 2, 1])
                with p1:
                    if st.button("← Prev", disabled=(page == 0), key="job_prev"):
                        st.session_state.job_page = max(0, page - 1)
                        st.rerun()
                with p2:
                    st.caption(f"Page {page + 1} of {total_pages}")
                with p3:
                    if st.button("Next →", disabled=(page >= total_pages - 1), key="job_next"):
                        st.session_state.job_page = min(total_pages - 1, page + 1)
                        st.rerun()

    st.divider()

   


# ─────────────────────────────────────────────────────────────────────────
# TAB 3 — PLATFORM COMPARISON
# ─────────────────────────────────────────────────────────────────────────
with tab_platforms:
    st.subheader("Freelance Platform Comparison")
    st.caption("Which platform is best for your skill set and earnings level?")

    platforms_data = [
        {"Platform":"Upwork","Fee":"5–20% (tiered)","Best for":"Long-term contracts, agencies, enterprise clients","Min viable rate":"$20/hr","Payment":"Wire, PayPal, Payoneer","PK Friendly":"✅ Yes — Payoneer widely used","Competition":"Very High","Avg contract":"$500–$5,000","Link":"https://www.upwork.com"},
        {"Platform":"Fiverr","Fee":"20% flat","Best for":"Packaged gigs, quick deliveries, creative work","Min viable rate":"$15/gig","Payment":"PayPal, Payoneer, bank transfer","PK Friendly":"✅ Yes — Payoneer common","Competition":"Very High","Avg contract":"$50–$500","Link":"https://www.fiverr.com"},
        {"Platform":"Toptal","Fee":"0% to freelancer","Best for":"Senior devs, designers, finance experts","Min viable rate":"$60/hr","Payment":"Wire transfer","PK Friendly":"⚠️ Limited — wire preferred","Competition":"Low (invite only)","Avg contract":"$5,000+","Link":"https://www.toptal.com"},
        {"Platform":"Contra","Fee":"0% commission","Best for":"Designers, writers, modern tech stack devs","Min viable rate":"$25/hr","Payment":"Stripe, bank transfer","PK Friendly":"⚠️ Stripe limited in PK","Competition":"Medium","Avg contract":"$500–$3,000","Link":"https://contra.com"},
        {"Platform":"Freelancer.com","Fee":"10% or $5 min","Best for":"Low-cost markets, entry-level, bulk projects","Min viable rate":"$5/hr","Payment":"PayPal, Skrill, wire","PK Friendly":"✅ Yes","Competition":"Extreme","Avg contract":"$50–$300","Link":"https://www.freelancer.com"},
        {"Platform":"PeoplePerHour","Fee":"20% then 7.5%","Best for":"UK/EU clients, writing, design","Min viable rate":"$15/hr","Payment":"PayPal, Payoneer","PK Friendly":"✅ Yes","Competition":"High","Avg contract":"$200–$1,500","Link":"https://www.peopleperhour.com"},
        {"Platform":"Guru","Fee":"5–9% (tiered)","Best for":"Tech, writing, admin","Min viable rate":"$10/hr","Payment":"PayPal, wire, e-check","PK Friendly":"✅ Yes","Competition":"High","Avg contract":"$200–$1,000","Link":"https://www.guru.com"},
    ]

    plat_df = pd.DataFrame(platforms_data)

    # Render with Visit links
    for _, row in plat_df.iterrows():
        pc1, pc2 = st.columns([5, 1])
        with pc1:
            st.markdown(
                f"**{row['Platform']}** — {row['Fee']} fee · {row['PK Friendly']} · Avg {row['Avg contract']}"
            )
            st.caption(f"Best for: {row['Best for']} | Min rate: {row['Min viable rate']} | Payment: {row['Payment']}")
        with pc2:
            st.link_button("Visit ↗", row["Link"], use_container_width=True)
        st.markdown("<hr style='margin:4px 0;border-color:#f0f0f0'>", unsafe_allow_html=True)

    st.divider()

    # Fee comparison chart
    st.subheader("Platform Fee Comparison — on $1,000 earned")
    fee_data = [
        ("Upwork",        150.0),
        ("Fiverr",        200.0),
        ("Freelancer",    100.0),
        ("PeoplePerHour", 200.0),
        ("Contra",          0.0),
        ("Toptal",          0.0),
        ("Guru",           90.0),
    ]
    fee_df = pd.DataFrame([{"Platform":n,"Fee $":f,"Net $":1000-f} for n,f in fee_data])
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
        "Rates are global market ranges for remote freelancers. "
        f"PKR values use live rate ₨ {USD_PKR:,.1f}/USD from IDMI pipeline."
    )
