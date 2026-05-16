"""
pages/Market_Intelligence.py — v4.0
5-platform job aggregation: RemoteOK · Himalayas · We Work Remotely
                            · Remotive · Arbeitnow
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

# ── Source colour palette (consistent across all charts + badges) ─────────
SOURCE_META = {
    "RemoteOK":       {"color": "#e11d48", "emoji": "🔴", "home": "https://remoteok.com"},
    "Himalayas":      {"color": "#7c3aed", "emoji": "🟣", "home": "https://himalayas.app/jobs"},
    "WeWorkRemotely": {"color": "#0284c7", "emoji": "🔵", "home": "https://weworkremotely.com"},
    "Remotive":       {"color": "#16a34a", "emoji": "🟢", "home": "https://remotive.com"},
    "Arbeitnow":      {"color": "#d97706", "emoji": "🟡", "home": "https://www.arbeitnow.com"},
}
ALL_SOURCES = list(SOURCE_META.keys())

# ── Load data ─────────────────────────────────────────────────────────────
df = load_data()
if df.empty:
    st.warning("No data yet. Run the harvester pipeline first.")
    st.stop()

latest  = get_latest(df)
skills  = parse_json_col(latest, "top_skills")
USD_PKR = float(latest.get("usd_pkr_rate") or 280.0)

st.title("Market Intelligence")
st.caption(
    "Live job listings from **5 platforms** — RemoteOK · Himalayas · "
    "We Work Remotely · Remotive · Arbeitnow · Refreshed every pipeline run."
)

# ── Top-level KPI strip ───────────────────────────────────────────────────
raw_jobs     = parse_json_col(latest, "jobs_data")     or []
source_stats = parse_json_col(latest, "source_stats")  or {}
job_volume   = int(latest.get("job_volume") or 0)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total unique jobs",  f"{job_volume:,}")
k2.metric("RemoteOK",           f"{source_stats.get('RemoteOK', 0):,}")
k3.metric("Himalayas",          f"{source_stats.get('Himalayas', 0):,}")
k4.metric("We Work Remotely",   f"{source_stats.get('WeWorkRemotely', 0):,}")
k5.metric("Remotive + Arbeit.", f"{source_stats.get('Remotive',0)+source_stats.get('Arbeitnow',0):,}")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────
tab_jobs, tab_skills, tab_sources, tab_platforms, tab_salaries = st.tabs([
    "📋 Live Job Board",
    "🔧 Skills Demand",
    "📊 Source Analytics",
    "⚖️ Platform Comparison",
    "💵 Salary Benchmarks",
])


# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — LIVE JOB BOARD (5 sources)
# ══════════════════════════════════════════════════════════════════════════
with tab_jobs:

    # ── Filter bar ───────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([3, 2, 2, 1])
    with fc1:
        job_search = st.text_input(
            "Search", placeholder="🔍  role, skill, company…",
            label_visibility="collapsed", key="job_search",
        )
    with fc2:
        all_tags = sorted({
            tag
            for j in raw_jobs
            for tag in j.get("tags", [])
        })
        tag_filter = st.multiselect(
            "Skill tags", all_tags, default=[], key="job_tag_filter",
        )
    with fc3:
        source_filter = st.multiselect(
            "Sources", ALL_SOURCES,
            default=ALL_SOURCES, key="job_source_filter",
            format_func=lambda s: f"{SOURCE_META[s]['emoji']} {s}",
        )
    with fc4:
        salary_only = st.toggle("💰 Salary only", value=False)

    # ── Apply filters ─────────────────────────────────────────────────────
    q = job_search.lower().strip()
    filtered: list = []
    for j in raw_jobs:
        src   = j.get("source", "")
        title = j.get("title", "").lower()
        co    = j.get("company", "").lower()
        tags  = [t.lower() for t in j.get("tags", [])]

        if source_filter and src not in source_filter:
            continue
        if q and q not in title and q not in co and not any(q in t for t in tags):
            continue
        if tag_filter:
            sel = [x.lower() for x in tag_filter]
            if not any(t in tags for t in sel):
                continue
        if salary_only and not j.get("salary"):
            continue
        filtered.append(j)

    # Summary bar
    last_ts = str(latest.get("timestamp", ""))[:16]
    st.caption(
        f"Showing **{len(filtered):,}** of **{len(raw_jobs):,}** unique jobs · "
        f"Last pipeline run: {last_ts} UTC"
    )

    if not raw_jobs:
        st.info(
            "No job listings yet — run the v4.0 harvester pipeline. "
            "The first run will populate all 5 sources."
        )
    elif not filtered:
        st.info("No jobs match your filters. Try clearing the skill or source filters.")
    else:
        # ── Pagination ────────────────────────────────────────────────────
        PAGE_SIZE = 15
        if "job_page" not in st.session_state:
            st.session_state.job_page = 0

        total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
        page = min(st.session_state.job_page, total_pages - 1)
        if page != st.session_state.job_page:
            st.session_state.job_page = page

        page_jobs = filtered[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

        # ── Job cards ─────────────────────────────────────────────────────
        for j in page_jobs:
            src       = j.get("source", "")
            src_meta  = SOURCE_META.get(src, {"color": "#6b7280", "emoji": "⚪"})
            src_color = src_meta["color"]
            src_emoji = src_meta["emoji"]

            # Salary badge
            salary_badge = ""
            if j.get("salary"):
                salary_badge = (
                    f'<span style="background:#d1fae5;color:#065f46;'
                    f'padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;">'
                    f'💰 {j["salary"]}</span>&nbsp;'
                )

            # Source badge
            source_badge = (
                f'<span style="background:{src_color}18;color:{src_color};'
                f'border:1px solid {src_color}40;'
                f'padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;">'
                f'{src_emoji} {src}</span>'
            )

            # Skill tags
            tags_html = " ".join(
                f'<span style="background:#f0f4f8;color:#374151;'
                f'padding:2px 7px;border-radius:10px;font-size:11px;">{t}</span>'
                for t in j.get("tags", [])[:7]
            )

            date_str = f" · 📅 {j['date']}" if j.get("date") else ""

            st.markdown(
                f"""<div style="border:1px solid #e2e8e4;border-radius:10px;
                    padding:14px 18px;margin-bottom:8px;background:#fff;
                    border-left:3px solid {src_color};">
                  <div style="display:flex;justify-content:space-between;
                              align-items:flex-start;flex-wrap:wrap;gap:6px;">
                    <div>
                      <div style="font-weight:700;font-size:15px;color:#0d1f15;">
                        {j.get('title','')}
                      </div>
                      <div style="font-size:13px;color:#5a7263;margin-top:2px;">
                        🏢 {j.get('company','')} &nbsp;·&nbsp;
                        🌍 {j.get('location','Worldwide')}{date_str}
                      </div>
                    </div>
                    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">
                      {salary_badge}{source_badge}
                    </div>
                  </div>
                  <div style="margin-top:8px;">{tags_html}</div>
                </div>""",
                unsafe_allow_html=True,
            )

            apply_url = j.get("url", SOURCE_META.get(src, {}).get("home", "#"))
            st.markdown(
                f'<a href="{apply_url}" target="_blank" style="'
                f'display:inline-block;margin-top:-4px;margin-bottom:6px;'
                f'padding:4px 14px;background:{src_color};color:#fff;'
                f'border-radius:8px;font-size:12px;font-weight:600;'
                f'text-decoration:none;">Apply on {src} ↗</a>',
                unsafe_allow_html=True,
            )

        # ── Pagination controls ───────────────────────────────────────────
        if total_pages > 1:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            pp1, pp2, pp3 = st.columns([1, 2, 1])
            with pp1:
                if st.button("← Prev", disabled=(page == 0), key="jp_prev"):
                    st.session_state.job_page = page - 1
                    st.rerun()
            with pp2:
                st.caption(f"Page {page + 1} of {total_pages} · "
                           f"{len(filtered):,} matching jobs")
            with pp3:
                if st.button("Next →",
                             disabled=(page >= total_pages - 1), key="jp_next"):
                    st.session_state.job_page = page + 1
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — SKILLS DEMAND
# ══════════════════════════════════════════════════════════════════════════
with tab_skills:

    st.subheader("Top In-Demand Skills — Aggregated Across All 5 Platforms")
    st.caption(
        "Skill tags are normalised via a shared alias map so 'Node.js', 'node', "
        "and 'nodejs' all count as the same skill. Counts reflect unique job listings."
    )

    if skills:
        col_bar, col_radar = st.columns([3, 2], gap="large")
        with col_bar:
            skills_df = pd.DataFrame(skills).sort_values("count", ascending=True)
            fig_bar = px.bar(
                skills_df, x="count", y="skill", orientation="h",
                color="count",
                color_continuous_scale=[[0, "#e8f5ee"], [1, "#01411C"]],
                labels={"count": "Job listings", "skill": ""},
                text="count",
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False,
                xaxis=dict(title="Unique listings mentioning skill",
                           gridcolor="#f0f0f0"),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_radar:
            top5 = skills_df.tail(5)
            if len(top5) >= 3:
                fig_r = go.Figure(go.Scatterpolar(
                    r=top5["count"].tolist() + [top5["count"].iloc[0]],
                    theta=top5["skill"].tolist() + [top5["skill"].iloc[0]],
                    fill="toself",
                    fillcolor="rgba(1,65,28,0.12)",
                    line=dict(color="#01411C", width=2),
                ))
                fig_r.update_layout(
                    polar=dict(
                        radialaxis=dict(showticklabels=False,
                                        gridcolor="#e2e8e4"),
                        angularaxis=dict(gridcolor="#e2e8e4"),
                    ),
                    paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=30, b=20),
                    showlegend=False, height=300,
                )
                st.markdown("**Top 5 — Radar**")
                st.plotly_chart(fig_r, use_container_width=True)

    else:
        st.info("Skills data not available yet — run the v4.0 pipeline.")

    st.divider()

    # ── Per-source skill breakdown ────────────────────────────────────────
    st.subheader("Skill Demand by Source")
    st.caption("Which platform contributes the most demand for each skill?")

    if raw_jobs:
        src_skill_counter: dict = {}
        for j in raw_jobs:
            src = j.get("source", "Other")
            for skill in j.get("tags", []):
                src_skill_counter.setdefault(skill, {}).setdefault(src, 0)
                src_skill_counter[skill][src] += 1

        if skills:
            top_skill_names = [s["skill"] for s in skills[:12]]
            rows = []
            for skill in top_skill_names:
                for src in ALL_SOURCES:
                    cnt = src_skill_counter.get(skill, {}).get(src, 0)
                    rows.append({"skill": skill, "source": src, "count": cnt})

            src_skill_df = pd.DataFrame(rows)
            color_map = {s: SOURCE_META[s]["color"] for s in ALL_SOURCES}

            fig_ss = px.bar(
                src_skill_df, x="skill", y="count", color="source",
                barmode="stack",
                color_discrete_map=color_map,
                labels={"count": "Listings", "skill": "", "source": "Platform"},
            )
            fig_ss.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(showgrid=False, tickangle=-30),
                yaxis=dict(gridcolor="#f0f0f0"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_ss, use_container_width=True)

    st.divider()

    # ── Historical skill trend ────────────────────────────────────────────
    st.subheader("Skills Trend — Historical Snapshots")
    if "top_skills" in df.columns:
        hist_rows = []
        for _, row in df.iterrows():
            try:
                sl = json.loads(row["top_skills"]) \
                     if isinstance(row["top_skills"], str) else []
                for s in sl:
                    hist_rows.append({
                        "timestamp": row["timestamp"],
                        "skill":     s.get("skill", ""),
                        "count":     s.get("count", 0),
                    })
            except Exception:
                pass

        if hist_rows:
            hist_df    = pd.DataFrame(hist_rows)
            all_skills = sorted(hist_df["skill"].unique())
            default_sk = all_skills[:6] if len(all_skills) >= 6 else all_skills
            picked     = st.multiselect("Skills to compare", all_skills,
                                        default=default_sk, key="skills_trend_pick")
            if picked:
                fig_ts = px.line(
                    hist_df[hist_df["skill"].isin(picked)],
                    x="timestamp", y="count", color="skill",
                    markers=True, line_shape="spline",
                    color_discrete_sequence=px.colors.qualitative.Dark24,
                    labels={"count": "Listings", "timestamp": ""},
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
            st.info("More pipeline runs will build the trend chart.")

    st.divider()

    # ── Static skills landscape ───────────────────────────────────────────
    st.subheader("Full Skills Landscape for Pakistani Freelancers")
    landscape = [
        {"Skill": "Python",           "Category": "Backend",    "Demand": "🔥 Very High", "USD/hr": "$35–65",  "Learning Curve": "Medium"},
        {"Skill": "React / Next.js",  "Category": "Frontend",   "Demand": "🔥 Very High", "USD/hr": "$30–60",  "Learning Curve": "Medium"},
        {"Skill": "Node.js",          "Category": "Backend",    "Demand": "🔥 Very High", "USD/hr": "$30–55",  "Learning Curve": "Medium"},
        {"Skill": "TypeScript",       "Category": "Frontend",   "Demand": "🔥 Very High", "USD/hr": "$35–65",  "Learning Curve": "Medium"},
        {"Skill": "WordPress",        "Category": "CMS",        "Demand": "🔥 Very High", "USD/hr": "$15–35",  "Learning Curve": "Low"},
        {"Skill": "Shopify",          "Category": "E-Commerce", "Demand": "🔥 Very High", "USD/hr": "$20–45",  "Learning Curve": "Low"},
        {"Skill": "Flutter",          "Category": "Mobile",     "Demand": "🟠 High",      "USD/hr": "$25–50",  "Learning Curve": "Medium"},
        {"Skill": "DevOps / Docker",  "Category": "Infra",      "Demand": "🟠 High",      "USD/hr": "$40–80",  "Learning Curve": "High"},
        {"Skill": "AWS / GCP",        "Category": "Cloud",      "Demand": "🟠 High",      "USD/hr": "$40–85",  "Learning Curve": "High"},
        {"Skill": "AI / ML / LLMs",   "Category": "AI",         "Demand": "🟠 High",      "USD/hr": "$45–90",  "Learning Curve": "High"},
        {"Skill": "Kubernetes",       "Category": "Infra",      "Demand": "🟠 High",      "USD/hr": "$50–90",  "Learning Curve": "High"},
        {"Skill": "Django / FastAPI", "Category": "Backend",    "Demand": "🟠 High",      "USD/hr": "$30–60",  "Learning Curve": "Medium"},
        {"Skill": "UI/UX + Figma",    "Category": "Design",     "Demand": "🟡 Medium",    "USD/hr": "$20–45",  "Learning Curve": "Medium"},
        {"Skill": "Laravel / PHP",    "Category": "Backend",    "Demand": "🟡 Medium",    "USD/hr": "$15–35",  "Learning Curve": "Medium"},
        {"Skill": "GraphQL",          "Category": "API",        "Demand": "🟡 Medium",    "USD/hr": "$30–60",  "Learning Curve": "Medium"},
        {"Skill": "Data Analysis",    "Category": "Data",       "Demand": "🟡 Medium",    "USD/hr": "$30–55",  "Learning Curve": "Medium"},
        {"Skill": "SEO / Content",    "Category": "Marketing",  "Demand": "🟡 Medium",    "USD/hr": "$15–30",  "Learning Curve": "Low"},
        {"Skill": "Cybersecurity",    "Category": "Security",   "Demand": "🟡 Medium",    "USD/hr": "$45–85",  "Learning Curve": "High"},
        {"Skill": "Rust",             "Category": "Systems",    "Demand": "🟢 Growing",   "USD/hr": "$45–85",  "Learning Curve": "High"},
        {"Skill": "Golang",           "Category": "Backend",    "Demand": "🟢 Growing",   "USD/hr": "$40–80",  "Learning Curve": "Medium"},
        {"Skill": "Blockchain/Web3",  "Category": "Emerging",   "Demand": "🟢 Growing",   "USD/hr": "$50–100", "Learning Curve": "High"},
        {"Skill": "Copywriting",      "Category": "Marketing",  "Demand": "🟢 Growing",   "USD/hr": "$15–40",  "Learning Curve": "Low"},
    ]
    st.dataframe(pd.DataFrame(landscape), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — SOURCE ANALYTICS
# ══════════════════════════════════════════════════════════════════════════
with tab_sources:

    st.subheader("Platform Source Breakdown")
    st.caption("How many jobs each platform contributed to this snapshot.")

    if source_stats:
        src_df = pd.DataFrame([
            {
                "Platform": src,
                "Jobs":     cnt,
                "Color":    SOURCE_META.get(src, {}).get("color", "#6b7280"),
            }
            for src, cnt in source_stats.items()
        ]).sort_values("Jobs", ascending=False)

        sc1, sc2 = st.columns([2, 2], gap="large")

        with sc1:
            fig_pie = px.pie(
                src_df, names="Platform", values="Jobs",
                color="Platform",
                color_discrete_map={
                    s: SOURCE_META[s]["color"] for s in ALL_SOURCES
                    if s in src_df["Platform"].values
                },
                hole=0.4,
            )
            fig_pie.update_traces(textposition="outside", textinfo="percent+label")
            fig_pie.update_layout(
                paper_bgcolor="white",
                margin=dict(l=0, r=0, t=20, b=0),
                showlegend=False,
                height=320,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with sc2:
            fig_src_bar = px.bar(
                src_df.sort_values("Jobs"),
                x="Jobs", y="Platform", orientation="h",
                color="Platform",
                color_discrete_map={
                    s: SOURCE_META[s]["color"] for s in ALL_SOURCES
                },
                text="Jobs",
                labels={"Jobs": "Unique job listings"},
            )
            fig_src_bar.update_traces(textposition="outside")
            fig_src_bar.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(title="Unique listings", gridcolor="#f0f0f0"),
                yaxis=dict(showgrid=False),
                showlegend=False,
                height=320,
            )
            st.plotly_chart(fig_src_bar, use_container_width=True)

    st.divider()

    # ── Source cards ──────────────────────────────────────────────────────
    st.subheader("About Each Source")
    source_info = {
        "RemoteOK": {
            "desc":    "Tech-focused remote job board. Free public JSON API, updated continuously.",
            "types":   "Engineering, Design, DevOps, Data, Product",
            "salary":  "~40% of listings include salary range",
            "tags":    "Rich per-job skill tags",
            "api":     "remoteok.com/api",
        },
        "Himalayas": {
            "desc":    "Curated remote-only job board with structured salary and location data.",
            "types":   "Engineering, Design, Product, Marketing, Sales",
            "salary":  "~35% have salary_min/salary_max fields",
            "tags":    "Structured tags per listing",
            "api":     "himalayas.app/jobs/api",
        },
        "WeWorkRemotely": {
            "desc":    "One of the oldest remote job boards. 10 category RSS feeds.",
            "types":   "All categories — prog, devops, design, writing, support…",
            "salary":  "Not exposed in RSS",
            "tags":    "Category-based fallback tags",
            "api":     "weworkremotely.com RSS feeds",
        },
        "Remotive": {
            "desc":    "Global remote-first job board with category API. Free, no auth.",
            "types":   "Software Dev, DevOps, Design, Data, Product, Marketing",
            "salary":  "Free-text salary string (~25% of listings)",
            "tags":    "Per-job skill tags",
            "api":     "remotive.com/api/remote-jobs",
        },
        "Arbeitnow": {
            "desc":    "EU-based, all listings remote-friendly. Free paginated JSON API.",
            "types":   "Engineering, Finance, Marketing, Legal, HR, Sales",
            "salary":  "Not exposed in API",
            "tags":    "job_types array as skill signals",
            "api":     "arbeitnow.com/api/job-board-api",
        },
    }

    for src, info in source_info.items():
        meta  = SOURCE_META[src]
        count = source_stats.get(src, 0)
        with st.expander(
            f"{meta['emoji']} {src}  —  {count:,} jobs this snapshot",
            expanded=False,
        ):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{info['desc']}**")
                st.markdown(
                    f"- **Job types:** {info['types']}\n"
                    f"- **Salary data:** {info['salary']}\n"
                    f"- **Skill tags:** {info['tags']}\n"
                    f"- **API endpoint:** `{info['api']}`"
                )
            with c2:
                st.link_button(
                    f"Browse {src} ↗",
                    meta["home"],
                    use_container_width=True,
                )

    st.divider()

    # ── Volume trend ──────────────────────────────────────────────────────
    st.subheader("Total Job Volume — Historical Trend")
    if "job_volume" in df.columns:
        fig_vol = px.area(
            df, x="timestamp", y="job_volume",
            color_discrete_sequence=["#1a7a3c"],
            labels={"job_volume": "Unique listings", "timestamp": ""},
        )
        fig_vol.update_traces(fill="tozeroy", fillcolor="rgba(26,122,60,0.10)")
        fig_vol.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#f0f0f0"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_vol, use_container_width=True)
        if len(df) >= 2:
            curr = int(df.iloc[-1]["job_volume"])
            prev = int(df.iloc[-2]["job_volume"])
            d    = curr - prev
            col_a, col_b = st.columns([1, 3])
            col_a.metric("Latest count", f"{curr:,}", f"{d:+,}")
            col_b.info(
                "Volume reflects deduplicated unique jobs across all 5 sources. "
                "Duplicates (same title + company seen on multiple platforms) are "
                "removed via MD5 fingerprinting."
            )

    st.divider()

    # ── STRATOS briefing ──────────────────────────────────────────────────
    st.subheader("🧠 STRATOS — Latest Market Briefing")
    _render_briefing(latest.get("ai_sentiment", ""))


# ══════════════════════════════════════════════════════════════════════════
# STRATOS BRIEFING RENDERER (shared helper — defined after tabs for scope)
# ══════════════════════════════════════════════════════════════════════════
def _render_briefing(raw: str):
    if not raw:
        st.info("🧠 No briefing yet — run the pipeline.")
        return
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("Currency Outlook:"):
            st.markdown(
                f"<div style='background:#f0fdf4;border-left:4px solid #16a34a;"
                f"padding:10px 14px;border-radius:6px;margin-bottom:8px;'>"
                f"<strong style='color:#15803d;'>💱 Currency Outlook</strong><br>"
                f"<span style='color:#1c1c1c'>"
                f"{line.replace('Currency Outlook:','').strip()}</span></div>",
                unsafe_allow_html=True,
            )
        elif line.startswith("Job Market:"):
            st.markdown(
                f"<div style='background:#fffbeb;border-left:4px solid #d97706;"
                f"padding:10px 14px;border-radius:6px;margin-bottom:8px;'>"
                f"<strong style='color:#b45309;'>📋 Job Market</strong><br>"
                f"<span style='color:#1c1c1c'>"
                f"{line.replace('Job Market:','').strip()}</span></div>",
                unsafe_allow_html=True,
            )
        elif line.startswith("Action Item:"):
            st.markdown(
                f"<div style='background:#eff6ff;border-left:4px solid #2563eb;"
                f"padding:10px 14px;border-radius:6px;margin-bottom:8px;'>"
                f"<strong style='color:#1d4ed8;'>⚡ Action Item</strong><br>"
                f"<span style='color:#1c1c1c'>"
                f"{line.replace('Action Item:','').strip()}</span></div>",
                unsafe_allow_html=True,
            )
        else:
            st.info(line)


# ══════════════════════════════════════════════════════════════════════════
# TAB 4 — PLATFORM COMPARISON
# ══════════════════════════════════════════════════════════════════════════
with tab_platforms:
    st.subheader("Freelance Platform Comparison")
    st.caption("Best platform for your skill set and earnings level.")

    platforms_data = [
        {"Platform": "Upwork",          "Fee": "5–20% tiered",   "Best for": "Long-term contracts, agencies",              "Min rate": "$20/hr",  "PK Friendly": "✅ Payoneer", "Avg contract": "$500–$5k",  "Link": "https://www.upwork.com"},
        {"Platform": "Fiverr",          "Fee": "20% flat",        "Best for": "Packaged gigs, creative work",              "Min rate": "$15/gig", "PK Friendly": "✅ Payoneer", "Avg contract": "$50–$500",  "Link": "https://www.fiverr.com"},
        {"Platform": "Toptal",          "Fee": "0% to freelancer","Best for": "Senior devs, finance experts",              "Min rate": "$60/hr",  "PK Friendly": "⚠️ Wire",    "Avg contract": "$5k+",      "Link": "https://www.toptal.com"},
        {"Platform": "Contra",          "Fee": "0% commission",   "Best for": "Designers, modern tech devs",               "Min rate": "$25/hr",  "PK Friendly": "⚠️ Stripe",  "Avg contract": "$500–$3k",  "Link": "https://contra.com"},
        {"Platform": "Freelancer.com",  "Fee": "10% or $5 min",   "Best for": "Entry-level, bulk small projects",          "Min rate": "$5/hr",   "PK Friendly": "✅ PayPal",   "Avg contract": "$50–$300",  "Link": "https://www.freelancer.com"},
        {"Platform": "PeoplePerHour",   "Fee": "20% then 7.5%",   "Best for": "UK/EU clients, writing, design",            "Min rate": "$15/hr",  "PK Friendly": "✅ Payoneer", "Avg contract": "$200–$1.5k","Link": "https://www.peopleperhour.com"},
        {"Platform": "Guru",            "Fee": "5–9% tiered",     "Best for": "Tech, writing, admin",                      "Min rate": "$10/hr",  "PK Friendly": "✅ PayPal",   "Avg contract": "$200–$1k",  "Link": "https://www.guru.com"},
    ]

    for row in platforms_data:
        pc1, pc2 = st.columns([5, 1])
        with pc1:
            st.markdown(
                f"**{row['Platform']}** — {row['Fee']} fee · "
                f"{row['PK Friendly']} · Avg {row['Avg contract']}"
            )
            st.caption(
                f"Best for: {row['Best for']} | "
                f"Min rate: {row['Min rate']} | "
                f"Avg contract: {row['Avg contract']}"
            )
        with pc2:
            st.link_button("Visit ↗", row["Link"], use_container_width=True)
        st.markdown("<hr style='margin:4px 0;border-color:#f0f0f0'>",
                    unsafe_allow_html=True)

    st.divider()

    # Fee comparison chart
    st.subheader("Platform Fee — on $1,000 earned")
    fee_data = [
        ("Upwork", 150.0), ("Fiverr", 200.0), ("Freelancer", 100.0),
        ("PeoplePerHour", 200.0), ("Contra", 0.0), ("Toptal", 0.0), ("Guru", 90.0),
    ]
    fee_df = pd.DataFrame([{"Platform": n, "Fee $": f, "Net $": 1000 - f}
                            for n, f in fee_data])
    fig_fee = px.bar(
        fee_df.sort_values("Fee $", ascending=False),
        x="Platform", y=["Fee $", "Net $"],
        barmode="stack",
        color_discrete_map={"Fee $": "#ef4444", "Net $": "#1a7a3c"},
        labels={"value": "USD", "variable": ""},
    )
    fig_fee.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#f0f0f0"),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig_fee, use_container_width=True)
    st.caption(
        "Upwork: $500 @ 20% + $500 @ 10% = $150 total fee on first $1k. "
        "Drops to 5% after $10k lifetime billings with a client."
    )


# ══════════════════════════════════════════════════════════════════════════
# TAB 5 — SALARY BENCHMARKS
# ══════════════════════════════════════════════════════════════════════════
with tab_salaries:
    st.subheader("Freelance Rate Benchmarks")
    st.caption(
        f"Hourly rates in USD and equivalent monthly PKR at live rate "
        f"₨ {USD_PKR:,.1f}/USD (160 billable hours/month)."
    )

    HOURS = 160
    salary_data = [
        ("Frontend Dev (React/Next)",     15, 65,  "1–7 yrs"),
        ("Backend Dev (Python/Node)",     20, 80,  "1–8 yrs"),
        ("Full Stack Dev",                25, 90,  "2–8 yrs"),
        ("Mobile Dev (Flutter)",          20, 70,  "1–6 yrs"),
        ("WordPress Dev",                 10, 40,  "1–5 yrs"),
        ("Shopify Dev",                   15, 55,  "1–5 yrs"),
        ("DevOps / Cloud Eng",            35, 100, "2–8 yrs"),
        ("ML / AI / LLM Engineer",        40, 120, "2–8 yrs"),
        ("UI/UX Designer",                15, 55,  "1–7 yrs"),
        ("Graphic Designer",              10, 35,  "1–6 yrs"),
        ("Data Analyst / Scientist",      20, 60,  "1–6 yrs"),
        ("Data Engineer",                 30, 80,  "2–7 yrs"),
        ("Cybersecurity Specialist",      35, 90,  "2–7 yrs"),
        ("SEO Specialist",                12, 40,  "1–5 yrs"),
        ("Copywriter / Tech Writer",      10, 40,  "1–5 yrs"),
        ("Video Editor / Motion",         12, 45,  "1–5 yrs"),
        ("Smart Contract Dev",            50, 120, "2–6 yrs"),
        ("QA / Automation Engineer",      15, 50,  "1–5 yrs"),
        ("Golang Developer",              35, 85,  "2–7 yrs"),
        ("Rust Developer",                40, 90,  "2–7 yrs"),
    ]

    rows = []
    for role, lo, hi, exp in salary_data:
        mid = (lo + hi) / 2
        rows.append({
            "Role":               role,
            "Experience":         exp,
            "USD/hr (range)":     f"${lo}–${hi}",
            "Monthly USD (mid)":  f"${mid * HOURS:,.0f}",
            "Monthly PKR (low)":  f"₨ {lo  * HOURS * USD_PKR:,.0f}",
            "Monthly PKR (mid)":  f"₨ {mid * HOURS * USD_PKR:,.0f}",
            "Monthly PKR (high)": f"₨ {hi  * HOURS * USD_PKR:,.0f}",
            "_mid":               mid * HOURS,
        })

    sal_df = pd.DataFrame(rows)
    st.dataframe(sal_df.drop(columns=["_mid"]),
                 use_container_width=True, hide_index=True)

    st.divider()

    fig_sal = px.bar(
        sal_df.sort_values("_mid"),
        x="_mid", y="Role", orientation="h",
        color="_mid",
        color_continuous_scale=[[0, "#e8f5ee"], [1, "#01411C"]],
        text=sal_df.sort_values("_mid")["Monthly PKR (mid)"],
        labels={"_mid": "Monthly USD (mid-rate)", "Role": ""},
    )
    fig_sal.update_traces(textposition="outside")
    fig_sal.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0, r=0, t=10, b=50),
        coloraxis_showscale=False,
        xaxis=dict(title="Monthly USD (mid)", gridcolor="#f0f0f0"),
        yaxis=dict(showgrid=False),
        height=580,
    )
    st.plotly_chart(fig_sal, use_container_width=True)
    st.caption(
        f"PKR values use live rate ₨ {USD_PKR:,.1f}/USD. "
        "Rates are global remote market ranges — actual earnings vary by platform and niche."
    )
