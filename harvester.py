import os
import json
import requests
import feedparser
from collections import Counter
from supabase import create_client
from groq import Groq
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. CREDENTIALS
# ---------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

supabase     = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client  = Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# 2. HELPER — safe HTTP fetch with timeout + retries
# ---------------------------------------------------------------------------
def safe_get(url, retries=3, timeout=18, extra_headers=None):
    headers = {"User-Agent": "IDMI/4.0 (market-intelligence)"}
    if extra_headers:
        headers.update(extra_headers)
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  [WARN] Attempt {attempt + 1} failed for {url}: {e}")
    print(f"  [ERROR] All retries exhausted for {url}")
    return None


# ---------------------------------------------------------------------------
# 3. EXCHANGE RATES
# ---------------------------------------------------------------------------
def fetch_exchange_rates():
    print("  Fetching exchange rates...")
    data = safe_get("https://open.er-api.com/v6/latest/USD")
    if not data or data.get("result") != "success":
        print("  [ERROR] Exchange rate fetch failed.")
        return None

    rates = data["rates"]
    pkr   = round(rates.get("PKR", 0), 2)

    return {
        "usd_pkr":  pkr,
        "eur_pkr":  round(rates.get("PKR", 0) / rates.get("EUR", 1), 2),
        "gbp_pkr":  round(rates.get("PKR", 0) / rates.get("GBP", 1), 2),
        "sar_pkr":  round(rates.get("PKR", 0) / rates.get("SAR", 1), 2),
        "aed_pkr":  round(rates.get("PKR", 0) / rates.get("AED", 1), 2),
        "cad_pkr":  round(rates.get("PKR", 0) / rates.get("CAD", 1), 2),
        "aud_pkr":  round(rates.get("PKR", 0) / rates.get("AUD", 1), 2),
        "purchasing_power_index": round(100000 / pkr, 2) if pkr else 0,
    }


# ---------------------------------------------------------------------------
# 4. CRYPTO
# ---------------------------------------------------------------------------
def fetch_crypto_rates():
    print("  Fetching crypto rates...")
    data = safe_get(
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=tether,bitcoin&vs_currencies=usd,pkr"
    )
    if not data:
        return {"usdt_usd": 1.0, "usdt_pkr": None, "btc_usd": None}
    return {
        "usdt_usd": data.get("tether",  {}).get("usd", 1.0),
        "usdt_pkr": data.get("tether",  {}).get("pkr"),
        "btc_usd":  data.get("bitcoin", {}).get("usd"),
    }


# ---------------------------------------------------------------------------
# 5. SKILL METADATA — salary bands + category for every tracked skill
#    salary_lo / salary_hi are USD/hr ranges from real market data (2025)
# ---------------------------------------------------------------------------
SKILL_METADATA = {
    # ── Agentic & LLM AI (highest-paying tier) ──────────────────────────
    "agentic-ai":        {"category": "Agentic AI",    "salary_lo": 65, "salary_hi": 140},
    "ai-agents":         {"category": "Agentic AI",    "salary_lo": 60, "salary_hi": 130},
    "mcp":               {"category": "Agentic AI",    "salary_lo": 60, "salary_hi": 125},
    "llmops":            {"category": "AI Ops",        "salary_lo": 65, "salary_hi": 135},
    "rag":               {"category": "AI/LLM",        "salary_lo": 55, "salary_hi": 120},
    "langchain":         {"category": "AI/LLM",        "salary_lo": 55, "salary_hi": 120},
    "langgraph":         {"category": "AI/LLM",        "salary_lo": 60, "salary_hi": 125},
    "llm":               {"category": "AI/LLM",        "salary_lo": 55, "salary_hi": 120},
    "openai":            {"category": "AI/LLM",        "salary_lo": 55, "salary_hi": 115},
    "ai-automation":     {"category": "AI Automation", "salary_lo": 50, "salary_hi": 115},
    "ai-workflows":      {"category": "AI Automation", "salary_lo": 50, "salary_hi": 115},
    "prompt-engineering":{"category": "AI/LLM",        "salary_lo": 45, "salary_hi": 100},
    "fine-tuning":       {"category": "AI/LLM",        "salary_lo": 60, "salary_hi": 130},
    "huggingface":       {"category": "AI/LLM",        "salary_lo": 55, "salary_hi": 120},
    "vector-database":   {"category": "AI Infra",      "salary_lo": 55, "salary_hi": 115},
    "pinecone":          {"category": "AI Infra",      "salary_lo": 55, "salary_hi": 115},
    "weaviate":          {"category": "AI Infra",      "salary_lo": 55, "salary_hi": 110},
    "cursor":            {"category": "AI Tools",      "salary_lo": 45, "salary_hi": 100},
    "n8n":               {"category": "AI Automation", "salary_lo": 40, "salary_hi":  90},
    "make":              {"category": "AI Automation", "salary_lo": 35, "salary_hi":  80},
    "zapier":            {"category": "AI Automation", "salary_lo": 30, "salary_hi":  70},
    "machine-learning":  {"category": "ML/AI",         "salary_lo": 45, "salary_hi": 120},
    "deep-learning":     {"category": "ML/AI",         "salary_lo": 50, "salary_hi": 125},
    "pytorch":           {"category": "ML/AI",         "salary_lo": 50, "salary_hi": 120},
    "tensorflow":        {"category": "ML/AI",         "salary_lo": 45, "salary_hi": 110},
    "data-science":      {"category": "Data",          "salary_lo": 35, "salary_hi":  90},
    "computer-vision":   {"category": "ML/AI",         "salary_lo": 50, "salary_hi": 120},
    "nlp":               {"category": "ML/AI",         "salary_lo": 50, "salary_hi": 115},
    # ── Infrastructure ────────────────────────────────────────────────────
    "devops":            {"category": "DevOps",        "salary_lo": 40, "salary_hi": 100},
    "aws":               {"category": "Cloud",         "salary_lo": 40, "salary_hi": 100},
    "kubernetes":        {"category": "DevOps",        "salary_lo": 45, "salary_hi": 105},
    "docker":            {"category": "DevOps",        "salary_lo": 35, "salary_hi":  85},
    "terraform":         {"category": "DevOps",        "salary_lo": 45, "salary_hi": 105},
    "gcp":               {"category": "Cloud",         "salary_lo": 40, "salary_hi": 100},
    "azure":             {"category": "Cloud",         "salary_lo": 40, "salary_hi": 100},
    # ── Backend ───────────────────────────────────────────────────────────
    "python":            {"category": "Backend",       "salary_lo": 35, "salary_hi":  80},
    "node":              {"category": "Backend",       "salary_lo": 30, "salary_hi":  70},
    "django":            {"category": "Backend",       "salary_lo": 30, "salary_hi":  70},
    "fastapi":           {"category": "Backend",       "salary_lo": 35, "salary_hi":  80},
    "golang":            {"category": "Backend",       "salary_lo": 45, "salary_hi": 100},
    "rust":              {"category": "Backend",       "salary_lo": 50, "salary_hi": 110},
    "postgresql":        {"category": "Backend",       "salary_lo": 30, "salary_hi":  70},
    "mongodb":           {"category": "Backend",       "salary_lo": 28, "salary_hi":  65},
    "laravel":           {"category": "Backend",       "salary_lo": 18, "salary_hi":  45},
    "php":               {"category": "Backend",       "salary_lo": 15, "salary_hi":  40},
    # ── Frontend ──────────────────────────────────────────────────────────
    "react":             {"category": "Frontend",      "salary_lo": 30, "salary_hi":  70},
    "next.js":           {"category": "Frontend",      "salary_lo": 32, "salary_hi":  75},
    "typescript":        {"category": "Frontend",      "salary_lo": 30, "salary_hi":  70},
    "javascript":        {"category": "Frontend",      "salary_lo": 25, "salary_hi":  60},
    "vue":               {"category": "Frontend",      "salary_lo": 25, "salary_hi":  60},
    # ── Mobile ────────────────────────────────────────────────────────────
    "flutter":           {"category": "Mobile",        "salary_lo": 25, "salary_hi":  60},
    "android":           {"category": "Mobile",        "salary_lo": 25, "salary_hi":  60},
    "ios":               {"category": "Mobile",        "salary_lo": 30, "salary_hi":  70},
    "swift":             {"category": "Mobile",        "salary_lo": 35, "salary_hi":  80},
    "kotlin":            {"category": "Mobile",        "salary_lo": 30, "salary_hi":  70},
    # ── E-Commerce / CMS ─────────────────────────────────────────────────
    "shopify":           {"category": "E-Commerce",    "salary_lo": 20, "salary_hi":  55},
    "wordpress":         {"category": "CMS",           "salary_lo": 15, "salary_hi":  40},
    # ── Design ───────────────────────────────────────────────────────────
    "ui-ux":             {"category": "Design",        "salary_lo": 20, "salary_hi":  55},
    "figma":             {"category": "Design",        "salary_lo": 20, "salary_hi":  50},
    "graphic-design":    {"category": "Design",        "salary_lo": 12, "salary_hi":  30},
    # ── Marketing / Content ───────────────────────────────────────────────
    "seo":               {"category": "Marketing",     "salary_lo": 12, "salary_hi":  35},
    "copywriting":       {"category": "Marketing",     "salary_lo": 15, "salary_hi":  45},
    # ── Blockchain ────────────────────────────────────────────────────────
    "solidity":          {"category": "Blockchain",    "salary_lo": 55, "salary_hi": 120},
    "web3":              {"category": "Blockchain",    "salary_lo": 50, "salary_hi": 110},
}

# All skill keys we want to track (union of SKILL_METADATA keys + extras)
TRACKED_SKILLS = set(SKILL_METADATA.keys()) | {
    "redis", "elasticsearch", "supabase", "bubble", "webflow",
    "airtable", "stable-diffusion", "midjourney", "comfyui",
    "crewai", "autogen", "react-native", "graphql", "stripe",
}

MAX_JOBS_DETAIL = 60

# Hiring-country extraction — look for these strings in location fields
COUNTRY_PATTERNS = {
    "USA":       ["usa", "united states", "us only", "u.s.", "america"],
    "UK":        ["uk", "united kingdom", "britain", "england"],
    "Germany":   ["germany", "german", "deutschland"],
    "Canada":    ["canada", "canadian"],
    "Australia": ["australia", "australian"],
    "Europe":    ["europe", "european union", "eu"],
    "Worldwide": ["worldwide", "anywhere", "remote", "global", ""],
}


def _parse_country(location_str):
    loc = (location_str or "").lower()
    for country, patterns in COUNTRY_PATTERNS.items():
        if any(p in loc for p in patterns if p):
            return country
    return "Other"


# ---------------------------------------------------------------------------
# 6. REMOTE JOBS + SKILL INTELLIGENCE
# ---------------------------------------------------------------------------
def fetch_jobs_and_skills():
    """
    Fetch RemoteOK jobs. Returns:
      job_volume, top_skills (JSON), jobs_data (JSON),
      skill_intelligence (JSON), hiring_countries (JSON).
    """
    print("  Fetching remote jobs from RemoteOK...")
    data = safe_get("https://remoteok.com/api")
    if not data:
        return {
            "job_volume":        0,
            "top_skills":        json.dumps([]),
            "jobs_data":         json.dumps([]),
            "skill_intelligence":json.dumps([]),
            "hiring_countries":  json.dumps([]),
        }

    jobs = [j for j in data if isinstance(j, dict) and "position" in j]

    # ── Tag counting ─────────────────────────────────────────────────────
    tag_counter   = Counter()
    country_counter = Counter()
    # salary tracking per skill: list of (min, max) pairs
    skill_salaries = {sk: [] for sk in TRACKED_SKILLS}

    for job in jobs:
        raw_tags = job.get("tags", [])
        sal_min  = job.get("salary_min") or job.get("salary_min_usd")
        sal_max  = job.get("salary_max") or job.get("salary_max_usd")
        loc      = job.get("location", "") or ""
        country_counter[_parse_country(loc)] += 1

        for tag in raw_tags:
            tl = tag.lower().replace(" ", "-")
            if tl in TRACKED_SKILLS:
                tag_counter[tl] += 1
                if sal_min and sal_max:
                    # convert annual → hourly (assume 2000 hrs/yr)
                    skill_salaries[tl].append(
                        (float(sal_min) / 2000, float(sal_max) / 2000)
                    )

    top_skills = [
        {"skill": sk, "count": cnt}
        for sk, cnt in tag_counter.most_common(15)
    ]

    # ── Build job records ─────────────────────────────────────────────────
    job_records = []
    for job in jobs[:MAX_JOBS_DETAIL]:
        sal_min = job.get("salary_min") or job.get("salary_min_usd") or None
        sal_max = job.get("salary_max") or job.get("salary_max_usd") or None
        if sal_min and sal_max:
            salary_str = f"${int(sal_min):,} – ${int(sal_max):,}/yr"
        elif sal_min:
            salary_str = f"${int(sal_min):,}+/yr"
        elif sal_max:
            salary_str = f"Up to ${int(sal_max):,}/yr"
        else:
            salary_str = ""
        tags = [t.lower() for t in job.get("tags", [])[:8]]
        loc  = (job.get("location") or "Worldwide").strip() or "Worldwide"
        job_records.append({
            "id":       str(job.get("id", "")),
            "title":    job.get("position", "").strip(),
            "company":  job.get("company",  "").strip(),
            "location": loc,
            "country":  _parse_country(loc),
            "salary":   salary_str,
            "tags":     tags,
            "url":      job.get("url", f"https://remoteok.com/remote-jobs/{job.get('id','')}"),
            "date":     str(job.get("date", ""))[:10],
        })

    # ── Hiring countries ─────────────────────────────────────────────────
    hiring_countries = [
        {"country": c, "count": n}
        for c, n in country_counter.most_common(8)
    ]

    print(f"  Jobs: {len(jobs)} | Stored: {len(job_records)} | "
          f"Top: {[s['skill'] for s in top_skills[:5]]}")

    return {
        "job_volume":        len(jobs),
        "top_skills":        json.dumps(top_skills),
        "jobs_data":         json.dumps(job_records),
        "skill_salaries_raw": skill_salaries,   # internal only — not stored
        "hiring_countries":  json.dumps(hiring_countries),
    }


# ---------------------------------------------------------------------------
# 7. SKILL INTELLIGENCE — growth trends + salary indicators + opportunity
# ---------------------------------------------------------------------------
def compute_skill_intelligence(current_skills_raw, skill_salaries_raw):
    """
    Build enriched per-skill intelligence by:
      1. Pulling the *previous* snapshot's top_skills from Supabase.
      2. Computing growth % for every skill.
      3. Merging curated salary bands from SKILL_METADATA.
      4. Computing live-data salary if enough jobs have salary data.
      5. Ranking top-paying and fastest-growing skills.
      6. Picking best_skill_month.

    Returns (skill_intelligence_json, best_skill_month_str,
             opportunity_alerts_json)
    """
    print("  Computing skill intelligence...")

    # Parse current
    current = {}
    try:
        for item in json.loads(current_skills_raw):
            current[item["skill"]] = item["count"]
    except Exception:
        pass

    # Pull previous snapshot
    previous = {}
    try:
        resp = (
            supabase.table("market_intel")
            .select("top_skills, timestamp")
            .order("timestamp", desc=True)
            .limit(2)
            .execute()
        )
        rows = resp.data or []
        if len(rows) >= 2:
            prev_raw = rows[1].get("top_skills", "[]")
            for item in json.loads(prev_raw):
                previous[item["skill"]] = item["count"]
    except Exception as e:
        print(f"  [WARN] Could not fetch previous snapshot: {e}")

    # Build enriched records
    records = []
    for skill, count in current.items():
        meta      = SKILL_METADATA.get(skill, {})
        sal_lo    = meta.get("salary_lo", 20)
        sal_hi    = meta.get("salary_hi", 60)
        sal_mid   = (sal_lo + sal_hi) / 2
        category  = meta.get("category", "Other")

        # Growth %
        prev_count = previous.get(skill, 0)
        if prev_count > 0:
            growth_pct = round(((count - prev_count) / prev_count) * 100, 1)
        elif prev_count == 0 and count > 0:
            growth_pct = 100.0   # new skill appearing
        else:
            growth_pct = 0.0

        # Live salary override if we have enough data points
        live_pairs = skill_salaries_raw.get(skill, [])
        if len(live_pairs) >= 3:
            sal_lo = round(sum(p[0] for p in live_pairs) / len(live_pairs), 1)
            sal_hi = round(sum(p[1] for p in live_pairs) / len(live_pairs), 1)
            sal_mid = (sal_lo + sal_hi) / 2

        records.append({
            "skill":      skill,
            "count":      count,
            "growth_pct": growth_pct,
            "category":   category,
            "salary_lo":  sal_lo,
            "salary_hi":  sal_hi,
            "salary_mid": round(sal_mid, 1),
            "monthly_usd_mid": round(sal_mid * 160, 0),
        })

    if not records:
        return json.dumps([]), "N/A", json.dumps([])

    # Sort helpers
    by_salary  = sorted(records, key=lambda x: x["salary_mid"], reverse=True)
    by_growth  = sorted(records, key=lambda x: x["growth_pct"], reverse=True)
    by_demand  = sorted(records, key=lambda x: x["count"],      reverse=True)

    # Best skill this month — highest composite score (salary_mid * count * growth bonus)
    for r in records:
        growth_bonus = max(1.0, 1 + r["growth_pct"] / 100)
        r["_score"] = r["salary_mid"] * (r["count"] ** 0.5) * growth_bonus
    best = max(records, key=lambda x: x["_score"])
    best_skill_month = best["skill"]

    # ── Opportunity alerts ───────────────────────────────────────────────
    alerts = []

    # 1. AI vs Frontend salary gap
    ai_skills  = [r for r in records if "AI" in r["category"] or "LLM" in r["category"] or "Agentic" in r["category"]]
    fe_skills  = [r for r in records if r["category"] == "Frontend"]
    if ai_skills and fe_skills:
        ai_sal = sum(r["salary_mid"] for r in ai_skills) / len(ai_skills)
        fe_sal = sum(r["salary_mid"] for r in fe_skills) / len(fe_skills)
        if fe_sal > 0:
            gap = round(((ai_sal - fe_sal) / fe_sal) * 100)
            if gap > 0:
                alerts.append({
                    "type": "salary_gap",
                    "icon": "💰",
                    "title": f"AI skills pay {gap}% more than frontend",
                    "detail": f"Average AI/LLM role: ${ai_sal:.0f}/hr vs Frontend: ${fe_sal:.0f}/hr. Upskilling in AI pays off fast.",
                    "severity": "high" if gap > 20 else "medium",
                })

    # 2. Fastest growing skill alert
    if by_growth and by_growth[0]["growth_pct"] > 0:
        top_grower = by_growth[0]
        alerts.append({
            "type": "growth",
            "icon": "🚀",
            "title": f"{top_grower['skill'].replace('-',' ').title()} demand up {top_grower['growth_pct']:+.1f}%",
            "detail": f"Now at {top_grower['count']} live listings. Early movers in this skill have pricing power.",
            "severity": "high" if top_grower["growth_pct"] > 30 else "medium",
        })

    # 3. Top-paying skill right now
    if by_salary:
        top_pay = by_salary[0]
        alerts.append({
            "type": "top_pay",
            "icon": "🏆",
            "title": f"Highest-paying tracked skill: {top_pay['skill'].replace('-',' ').title()}",
            "detail": f"${top_pay['salary_lo']}–${top_pay['salary_hi']}/hr (${top_pay['monthly_usd_mid']:,.0f}/mo at mid-rate). Category: {top_pay['category']}.",
            "severity": "info",
        })

    # 4. Python + AI combination premium
    py_count  = current.get("python", 0)
    llm_count = current.get("llm", 0) + current.get("openai", 0) + current.get("langchain", 0)
    if py_count > 0 and llm_count > 0:
        combined_pct = round(((py_count + llm_count) / max(py_count, 1) - 1) * 100)
        alerts.append({
            "type": "combination",
            "icon": "⚡",
            "title": f"Python + AI listed in {py_count + llm_count} combined jobs",
            "detail": "Python remains the #1 language for AI roles. Adding LLM/LangChain to Python skills unlocks the $55–$120/hr AI tier.",
            "severity": "medium",
        })

    # 5. Agentic AI emergence
    agentic_count = (current.get("ai-agents", 0) + current.get("agentic-ai", 0) +
                     current.get("mcp", 0) + current.get("langgraph", 0) +
                     current.get("crewai", 0))
    if agentic_count > 0:
        alerts.append({
            "type": "emerging",
            "icon": "🤖",
            "title": f"Agentic AI roles: {agentic_count} live listings",
            "detail": "AI Agents, MCP, and multi-agent orchestration (LangGraph, CrewAI) are 2025's fastest-emerging skill cluster. Avg rate $60–$135/hr.",
            "severity": "high",
        })

    print(f"  Skill intelligence: {len(records)} skills | "
          f"Best skill: {best_skill_month} | Alerts: {len(alerts)}")

    return json.dumps(records), best_skill_month, json.dumps(alerts)


# ---------------------------------------------------------------------------
# 8. NEWS — Tech-specific RSS feeds
# ---------------------------------------------------------------------------
RSS_FEEDS = [
    {"name": "ProPakistani",    "url": "https://propakistani.pk/feed/",                            "pk": True,  "max": 3},
    {"name": "Profit Pakistan", "url": "https://profit.pakistantoday.com.pk/feed/",                "pk": True,  "max": 3},
    {"name": "Hacker News",     "url": "https://hnrss.org/frontpage",                              "pk": False, "max": 3},
    {"name": "TechCrunch",      "url": "https://techcrunch.com/feed/",                             "pk": False, "max": 2},
    {"name": "The Verge",       "url": "https://www.theverge.com/rss/index.xml",                   "pk": False, "max": 2},
    {"name": "Ars Technica",    "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "pk": False, "max": 1},
    {"name": "VentureBeat AI",  "url": "https://venturebeat.com/ai/feed/",                        "pk": False, "max": 2},
]

TECH_KEYWORDS = [
    "software", "app", "tech", "ai", "startup", "digital", "code", "python",
    "developer", "freelance", "remote", "crypto", "bitcoin", "cyber", "cloud",
    "data", "android", "ios", "internet", "online", "platform", "api", "open source",
    "dollar", "pkr", "rupee", "economy", "market", "investment", "fiverr", "upwork",
    "github", "tool", "launch", "product", "funding", "acquisition", "llm", "gpt",
    "openai", "anthropic", "agent", "langchain", "cursor", "automation", "rag",
]


def is_tech_relevant(title):
    tl = title.lower()
    return any(kw in tl for kw in TECH_KEYWORDS)


def fetch_news_headlines():
    print("  Fetching news headlines via RSS...")
    headlines = []
    for feed_cfg in RSS_FEEDS:
        source = feed_cfg["name"]
        url    = feed_cfg["url"]
        is_pk  = feed_cfg["pk"]
        max_n  = feed_cfg["max"]
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                continue
            count = 0
            for entry in feed.entries:
                if count >= max_n:
                    break
                title = entry.get("title", "").strip()
                link  = entry.get("link",  "")
                if not title or not link:
                    continue
                if is_pk and not is_tech_relevant(title):
                    continue
                headlines.append({"title": title, "source": source, "link": link, "pk": is_pk})
                count += 1
        except Exception as e:
            print(f"  [WARN] RSS feed failed ({source}): {e}")

    print(f"  Collected {len(headlines)} headlines.")
    return json.dumps(headlines[:15])


# ---------------------------------------------------------------------------
# 9. AI BRIEFING — STRATOS v4 with full skill intelligence
# ---------------------------------------------------------------------------
def generate_ai_insight(rates, jobs, top_skills_raw, news_raw,
                        skill_intel_raw, opp_alerts_raw, best_skill):
    print("  Generating STRATOS AI insight via Groq...")

    # Top skills summary
    top_skills_list = "unavailable"
    try:
        parsed = json.loads(top_skills_raw)
        top_skills_list = ", ".join([f"{s['skill']} ({s['count']})" for s in parsed[:6]])
    except Exception:
        pass

    # Job titles sample
    job_titles_sample = "unavailable"
    try:
        all_jobs = json.loads(jobs.get("jobs_data", "[]"))
        titles   = [j["title"] for j in all_jobs[:8] if j.get("title")]
        job_titles_sample = " | ".join(titles) if titles else "unavailable"
    except Exception:
        pass

    # News context
    news_context = "unavailable"
    try:
        parsed_news = json.loads(news_raw)
        headlines   = [f"[{n['source']}] {n['title']}" for n in parsed_news[:5]]
        news_context = "\n".join(headlines) if headlines else "unavailable"
    except Exception:
        pass

    # Skill intelligence summary
    skill_intel_summary = "unavailable"
    try:
        intel  = json.loads(skill_intel_raw)
        by_pay = sorted(intel, key=lambda x: x["salary_mid"], reverse=True)[:3]
        by_gr  = sorted(intel, key=lambda x: x["growth_pct"],  reverse=True)[:3]
        pay_str    = ", ".join([f"{r['skill']} (${r['salary_lo']}–${r['salary_hi']}/hr)" for r in by_pay])
        growth_str = ", ".join([f"{r['skill']} ({r['growth_pct']:+.1f}%)" for r in by_gr if r['growth_pct'] > 0])
        skill_intel_summary = f"Top-paying: {pay_str}. Fastest growing: {growth_str or 'stable'}."
    except Exception:
        pass

    # Opportunity alerts summary
    alerts_summary = "unavailable"
    try:
        alerts = json.loads(opp_alerts_raw)
        alerts_summary = " | ".join([a["title"] for a in alerts[:3]])
    except Exception:
        pass

    prompt = f"""
You are STRATOS, the AI engine of IDMI (Indus Digital Market Intelligence) — Pakistan's freelancer intelligence platform.

LIVE MARKET DATA:
- USD/PKR: {rates['usd_pkr']} | EUR/PKR: {rates['eur_pkr']} | GBP/PKR: {rates['gbp_pkr']}
- USDT/PKR: {rates.get('usdt_pkr', 'N/A')} | BTC/USD: ${rates.get('btc_usd', 'N/A')}
- Purchasing Power Index: {rates['purchasing_power_index']}
- Remote job listings: {jobs['job_volume']:,}
- Live skill demand: {top_skills_list}
- Sample job titles: {job_titles_sample}
- SKILL INTELLIGENCE — {skill_intel_summary}
- Best skill this pipeline run: {best_skill}
- Opportunity alerts: {alerts_summary}

LATEST TECH/BUSINESS NEWS:
{news_context}

Write a STRATOS Market Briefing in exactly this format — 3 labelled paragraphs, no bullet points, no markdown:

Currency Outlook: [Specific advice on USD/PKR — hold, convert, or invoice? Use the actual rate number.]

Job Market: [Which specific AI/tech skills are surging, which pay best, and what the growth trend means for a Pakistani freelancer RIGHT NOW. Mention skill names and salary ranges.]

Action Item: [One concrete, data-backed recommendation combining rates + skill intelligence + an opportunity alert. Be specific: skill name, expected hourly rate, platform to target.]

Be direct, data-driven, Pakistan-centric. Never be generic.
"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are STRATOS — a precise AI market analyst for Pakistan's digital economy. "
                        "Always output exactly 3 labelled paragraphs. "
                        "Never use bullet points or markdown. "
                        "Mention specific skill names, salary figures, and platform names. "
                        "Never be generic."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
            max_tokens=320,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [ERROR] AI insight generation failed: {e}")
        return (
            f"Currency Outlook: USD/PKR is at {rates['usd_pkr']} — STRATOS briefing unavailable this cycle. "
            f"Job Market: {jobs['job_volume']:,} remote listings tracked; best skill this run is {best_skill}. "
            f"Action Item: Check back after the next pipeline run for a full market briefing."
        )


# ---------------------------------------------------------------------------
# 10. MAIN PIPELINE
# ---------------------------------------------------------------------------
def run_ingestion_pipeline():
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  IDMI Ingestion Pipeline v4.0  |  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    rates = fetch_exchange_rates()
    if not rates:
        print("[FATAL] Cannot proceed without exchange rate data. Aborting.")
        return

    crypto = fetch_crypto_rates()
    rates.update(crypto)

    jobs   = fetch_jobs_and_skills()
    news   = fetch_news_headlines()

    # Compute skill intelligence (queries Supabase for previous snapshot internally)
    skill_intel_json, best_skill_month, opp_alerts_json = compute_skill_intelligence(
        jobs["top_skills"],
        jobs.pop("skill_salaries_raw", {}),   # internal only, remove before payload
    )

    ai_insight = generate_ai_insight(
        rates, jobs, jobs["top_skills"], news,
        skill_intel_json, opp_alerts_json, best_skill_month,
    )

    payload = {
        "timestamp":              now.isoformat(),
        "usd_pkr_rate":           rates["usd_pkr"],
        "eur_pkr_rate":           rates["eur_pkr"],
        "gbp_pkr_rate":           rates["gbp_pkr"],
        "sar_pkr_rate":           rates["sar_pkr"],
        "aed_pkr_rate":           rates["aed_pkr"],
        "purchasing_power_index": rates["purchasing_power_index"],
        "usdt_pkr_rate":          rates.get("usdt_pkr"),
        "btc_usd_rate":           rates.get("btc_usd"),
        "job_volume":             jobs["job_volume"],
        "top_skills":             jobs["top_skills"],
        "jobs_data":              jobs["jobs_data"],
        "hiring_countries":       jobs["hiring_countries"],
        "skill_intelligence":     skill_intel_json,    # NEW v4
        "opportunity_alerts":     opp_alerts_json,     # NEW v4
        "best_skill_month":       best_skill_month,    # NEW v4
        "news_headlines":         news,
        "ai_sentiment":           ai_insight,
    }

    print("  Storing to Supabase...")
    try:
        supabase.table("market_intel").insert(payload).execute()
        print(f"\n  ✓ Pipeline v4.0 complete. {len(payload)} fields stored.")
        print(f"  USD/PKR: {rates['usd_pkr']} | Jobs: {jobs['job_volume']} | "
              f"Best skill: {best_skill_month}")
    except Exception as e:
        print(f"  [FATAL] Supabase insert failed: {e}")
        raise

    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_ingestion_pipeline()
