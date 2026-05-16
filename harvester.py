"""
IDMI Harvester v4.0 — Indus Digital Market Intelligence
Multi-Platform Job Aggregation

Job sources (5 platforms):
  1. RemoteOK        — JSON API  (remoteok.com/api)
  2. Himalayas       — JSON API  (himalayas.app/jobs/api)
  3. We Work Remotely — RSS      (weworkremotely.com — 10 category feeds)
  4. Remotive        — JSON API  (remotive.com/api/remote-jobs)
  5. Arbeitnow       — JSON API  (arbeitnow.com/api/job-board-api)

All jobs are normalised to a shared schema, deduplicated by (title, company)
fingerprint across sources, and tagged via a shared skill alias map so the
demand counter is accurate even when sources spell tags differently
(e.g. "Node.js" / "node" / "nodejs" all map to canonical "node").
"""

import os
import re
import json
import hashlib
import requests
import feedparser
from collections import Counter
from supabase import create_client
from groq import Groq
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# ─────────────────────────────────────────────────────────────────────────
# 1. CREDENTIALS
# ─────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

supabase    = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


# ─────────────────────────────────────────────────────────────────────────
# 2. SHARED HTTP HELPERS
# ─────────────────────────────────────────────────────────────────────────
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; IDMI/4.0; "
        "+https://github.com/idmi-pk/idmi)"
    ),
    "Accept": "application/json, text/html, */*",
}


def safe_get_json(url: str, params: dict = None,
                  retries: int = 3, timeout: int = 20):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=_HEADERS,
                             timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            print(f"    [WARN] attempt {attempt+1} → {url}: {exc}")
    print(f"    [FAIL] gave up on {url}")
    return None


def safe_get_text(url: str, retries: int = 3, timeout: int = 20):
    hdrs = {**_HEADERS, "Accept": "application/xml, text/xml, */*"}
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=hdrs, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as exc:
            print(f"    [WARN] attempt {attempt+1} → {url}: {exc}")
    print(f"    [FAIL] gave up on {url}")
    return None


# ─────────────────────────────────────────────────────────────────────────
# 3. SKILL TAXONOMY  — shared by ALL 5 sources
# ─────────────────────────────────────────────────────────────────────────
# Canonical skill names stored in DB and displayed in charts
CANONICAL_SKILLS: set = {
    # Languages
    "python", "javascript", "typescript", "php", "golang", "rust",
    "ruby", "java", "scala", "elixir", "swift", "kotlin", "dart",
    "solidity", "bash", "sql", "cplusplus",
    # Frontend
    "react", "nextjs", "vue", "angular", "svelte", "tailwind",
    "webflow", "gatsby", "figma", "ui-ux", "css", "html",
    # Backend / frameworks
    "node", "django", "fastapi", "laravel", "rails", "spring",
    "flask", "express", "nestjs", "phoenix",
    # Mobile
    "flutter", "android", "ios", "react-native",
    # DevOps / Infra
    "devops", "docker", "kubernetes", "terraform", "aws", "gcp",
    "azure", "linux", "nginx", "ansible", "ci-cd",
    # Data / AI / ML
    "machine-learning", "data-science", "data-engineering",
    "tensorflow", "pytorch", "huggingface", "langchain", "llm",
    "openai", "computer-vision", "spark", "kafka", "dbt",
    "snowflake", "airflow", "tableau", "powerbi",
    # Databases
    "postgresql", "mongodb", "redis", "elasticsearch", "firebase",
    "supabase", "mysql", "sqlite",
    # CMS / E-commerce
    "wordpress", "shopify", "woocommerce",
    # Other tech
    "graphql", "rest", "grpc", "web3", "blockchain", "unity",
    "cybersecurity", "seo", "copywriting",
}

# Raw tag strings → canonical skill (all lowercase, hyphen-separated)
SKILL_ALIASES: dict = {
    # Node
    "node.js": "node",  "nodejs": "node",
    # React family
    "react.js": "react",  "reactjs": "react",
    "react native": "react-native",  "react-native": "react-native",
    # Next / Vue / Angular
    "next.js": "nextjs",
    "nuxt": "vue",  "nuxt.js": "vue",
    "vue.js": "vue",  "vuejs": "vue",
    "angular.js": "angular",  "angularjs": "angular",
    # Go
    "go": "golang",  "go lang": "golang",  "go language": "golang",
    # Rails
    "ruby on rails": "rails",  "ruby-on-rails": "rails",  "ror": "rails",
    # Kubernetes
    "k8s": "kubernetes",
    # ML / AI
    "ml": "machine-learning",
    "machine learning": "machine-learning",
    "artificial intelligence": "machine-learning",
    "ai/ml": "machine-learning",
    "gen ai": "llm",  "generative ai": "llm",
    "gpt": "llm",  "large language models": "llm",  "claude": "llm",
    # Postgres
    "postgres": "postgresql",  "pg": "postgresql",
    # UI/UX
    "ui/ux": "ui-ux",  "ui design": "ui-ux",  "ux design": "ui-ux",
    "product design": "ui-ux",  "user experience": "ui-ux",
    "user-experience": "ui-ux",  "ux": "ui-ux",  "ui": "ui-ux",
    # CSS frameworks
    "tailwindcss": "tailwind",  "tailwind css": "tailwind",
    # DevOps
    "devsecops": "devops",  "sre": "devops",
    "site reliability engineering": "devops",
    "platform engineering": "devops",
    # Data
    "data science": "data-science",
    "data engineering": "data-engineering",
    "data analyst": "data-science",  "data analysis": "data-science",
    "computer vision": "computer-vision",
    # Cloud
    "amazon web services": "aws",
    "google cloud": "gcp",  "google cloud platform": "gcp",
    "microsoft azure": "azure",
    # CI/CD
    "github actions": "ci-cd",  "gitlab ci": "ci-cd",
    "jenkins": "ci-cd",  "circleci": "ci-cd",  "github-actions": "ci-cd",
    # Mobile
    "dart": "flutter",
    # Other
    "mariadb": "mysql",  "wp": "wordpress",
    "c++": "cplusplus",  "c/c++": "cplusplus",
}


def normalise_skill(raw: str):
    """Return canonical skill or None if not in taxonomy."""
    t = raw.strip().lower()
    # 1. exact alias
    if t in SKILL_ALIASES:
        return SKILL_ALIASES[t]
    # 2. hyphenated version alias
    th = re.sub(r"[\s./]+", "-", t).strip("-")
    if th in SKILL_ALIASES:
        return SKILL_ALIASES[th]
    # 3. direct canonical match
    if t in CANONICAL_SKILLS:
        return t
    if th in CANONICAL_SKILLS:
        return th
    return None


# ─────────────────────────────────────────────────────────────────────────
# 4. SHARED JOB SCHEMA + HELPERS
# ─────────────────────────────────────────────────────────────────────────
MAX_PER_SOURCE  = 100   # fetch ceiling per source
MAX_JOBS_STORED = 250   # stored in Supabase jobs_data JSON


def _fmt_salary(lo, hi, currency: str = "USD") -> str:
    sym = {"USD": "$", "GBP": "£", "EUR": "€",
           "CAD": "CA$", "AUD": "A$"}.get(str(currency).upper(), "$")
    try:
        lo = int(float(lo)) if lo else None
        hi = int(float(hi)) if hi else None
    except (TypeError, ValueError):
        return ""
    if lo and hi:
        return f"{sym}{lo:,} – {sym}{hi:,}/yr"
    if lo:
        return f"{sym}{lo:,}+/yr"
    if hi:
        return f"Up to {sym}{hi:,}/yr"
    return ""


def _fingerprint(title: str, company: str) -> str:
    key = f"{title.lower().strip()}|{company.lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()[:16]


def build_job(*, title: str, company: str, location: str, salary: str,
              tags: list, url: str, source: str, date: str = "") -> dict:
    """Normalise raw fields into the shared canonical job dict."""
    clean_tags = []
    for t in tags:
        canon = normalise_skill(str(t))
        if canon and canon not in clean_tags:
            clean_tags.append(canon)

    return {
        "id":       _fingerprint(title, company),
        "title":    title.strip(),
        "company":  company.strip(),
        "location": location.strip() or "Worldwide",
        "salary":   salary,
        "tags":     clean_tags[:10],
        "url":      url.strip(),
        "source":   source,
        "date":     date[:10] if date else "",
    }


# ─────────────────────────────────────────────────────────────────────────
# 5. SOURCE 1 — REMOTEOK
#    API: https://remoteok.com/api
#    Response: JSON array; index-0 = metadata (skip). No auth required.
#    Job fields: position, company, location, tags[], salary_min,
#                salary_max, url, date (unix timestamp string)
# ─────────────────────────────────────────────────────────────────────────
def fetch_remoteok() -> list:
    print("    [RemoteOK] Fetching...")
    data = safe_get_json("https://remoteok.com/api", timeout=25)
    if not data:
        return []

    raw  = [j for j in data if isinstance(j, dict) and "position" in j]
    jobs = []
    for j in raw[:MAX_PER_SOURCE]:
        salary = _fmt_salary(
            j.get("salary_min") or j.get("salary_min_usd"),
            j.get("salary_max") or j.get("salary_max_usd"),
        )
        jobs.append(build_job(
            title    = j.get("position", ""),
            company  = j.get("company", ""),
            location = j.get("location", "Worldwide"),
            salary   = salary,
            tags     = j.get("tags", []),
            url      = j.get("url") or f"https://remoteok.com/remote-jobs/{j.get('id','')}",
            source   = "RemoteOK",
            date     = str(j.get("date", ""))[:10],
        ))

    print(f"    [RemoteOK] ✓ {len(jobs)} jobs")
    return jobs


# ─────────────────────────────────────────────────────────────────────────
# 6. SOURCE 2 — HIMALAYAS
#    API: https://himalayas.app/jobs/api
#    Params: limit, offset  |  No auth required
#    Job fields: title, company{name,logo}, locations[{name}], tags[{name}],
#                applicationLink, salaryMin, salaryMax, currency, createdAt, slug
# ─────────────────────────────────────────────────────────────────────────
def fetch_himalayas() -> list:
    print("    [Himalayas] Fetching...")
    data = safe_get_json(
        "https://himalayas.app/jobs/api",
        params={"limit": MAX_PER_SOURCE, "offset": 0},
    )
    if not data or "jobs" not in data:
        return []

    jobs = []
    for j in data["jobs"][:MAX_PER_SOURCE]:
        company  = (j.get("company") or {}).get("name", "") \
                   if isinstance(j.get("company"), dict) \
                   else str(j.get("company", ""))
        locs     = j.get("locations") or []
        location = locs[0].get("name", "Worldwide") if locs else "Worldwide"
        raw_tags = [
            t.get("name", "") if isinstance(t, dict) else str(t)
            for t in (j.get("tags") or [])
        ]
        salary   = _fmt_salary(j.get("salaryMin"), j.get("salaryMax"),
                               j.get("currency", "USD"))
        url      = (j.get("applicationLink")
                    or f"https://himalayas.app/jobs/{j.get('slug','')}")
        date_raw = str(j.get("createdAt") or "")
        date     = date_raw[:10] if date_raw else ""

        jobs.append(build_job(
            title    = j.get("title", ""),
            company  = company,
            location = location,
            salary   = salary,
            tags     = raw_tags,
            url      = url,
            source   = "Himalayas",
            date     = date,
        ))

    print(f"    [Himalayas] ✓ {len(jobs)} jobs")
    return jobs


# ─────────────────────────────────────────────────────────────────────────
# 7. SOURCE 3 — WE WORK REMOTELY  (RSS — 10 category feeds)
#    No JSON API.  RSS entry title format: "Company Name: Job Title"
#    WWR RSS does NOT expose salary or individual skill tags —
#    we derive fallback tags from the feed category.
# ─────────────────────────────────────────────────────────────────────────
_WWR_FEEDS = [
    ("https://weworkremotely.com/categories/remote-programming-jobs.rss",       "Programming"),
    ("https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",   "DevOps"),
    ("https://weworkremotely.com/categories/remote-design-jobs.rss",            "Design"),
    ("https://weworkremotely.com/categories/remote-product-jobs.rss",           "Product"),
    ("https://weworkremotely.com/categories/remote-management-jobs.rss",        "Management"),
    ("https://weworkremotely.com/categories/remote-marketing-jobs.rss",         "Marketing"),
    ("https://weworkremotely.com/categories/remote-finance-legal-jobs.rss",     "Finance"),
    ("https://weworkremotely.com/categories/remote-sales-jobs.rss",             "Sales"),
    ("https://weworkremotely.com/categories/remote-writing-jobs.rss",           "Writing"),
    ("https://weworkremotely.com/categories/remote-customer-support-jobs.rss",  "Support"),
]

# Category → canonical skill fallbacks (WWR has no per-job skill tags)
_WWR_CAT_TAGS = {
    "Programming": ["python", "javascript", "react", "node", "typescript"],
    "DevOps":      ["devops", "docker", "kubernetes", "aws", "terraform"],
    "Design":      ["ui-ux", "figma", "css"],
    "Product":     [],
    "Management":  [],
    "Marketing":   ["seo", "copywriting"],
    "Finance":     [],
    "Writing":     ["copywriting"],
    "Support":     [],
    "Sales":       [],
}


def _parse_wwr_rss(rss_text: str, category: str) -> list:
    jobs = []
    try:
        feed = feedparser.parse(rss_text)
        for entry in feed.entries[:30]:
            raw_title = entry.get("title", "").strip()
            # Skip the aggregate section header WWR emits as first entry
            if not raw_title or "we work remotely" in raw_title.lower():
                continue

            # "Company Name: Job Title"
            if ": " in raw_title:
                company, title = raw_title.split(": ", 1)
            else:
                company = ""
                title   = raw_title

            link     = entry.get("link", "")
            region   = getattr(entry, "region", "") or ""
            location = region if region and region.lower() not in ("", "anywhere") \
                       else "Worldwide"

            published = entry.get("published", "")
            try:
                date = parsedate_to_datetime(published).strftime("%Y-%m-%d") \
                       if published else ""
            except Exception:
                date = ""

            jobs.append(build_job(
                title    = title,
                company  = company,
                location = location,
                salary   = "",
                tags     = _WWR_CAT_TAGS.get(category, []),
                url      = link,
                source   = "WeWorkRemotely",
                date     = date,
            ))
    except Exception as exc:
        print(f"    [WWR] Parse error ({category}): {exc}")
    return jobs


def fetch_wwr() -> list:
    print("    [WeWorkRemotely] Fetching 10 RSS category feeds...")
    all_jobs = []
    for feed_url, category in _WWR_FEEDS:
        text = safe_get_text(feed_url)
        if not text:
            print(f"    [WWR] Skipped {category}")
            continue
        batch = _parse_wwr_rss(text, category)
        print(f"    [WWR] {category}: {len(batch)}")
        all_jobs.extend(batch)
    print(f"    [WeWorkRemotely] ✓ {len(all_jobs)} jobs total")
    return all_jobs


# ─────────────────────────────────────────────────────────────────────────
# 8. SOURCE 4 — REMOTIVE
#    API: https://remotive.com/api/remote-jobs
#    Params: category (str), limit (int)  |  No auth required
#    Job fields: id, url, title, company_name, category, tags[str],
#                job_type, publication_date, candidate_required_location,
#                salary (free-text, e.g. "$80k-$120k")
# ─────────────────────────────────────────────────────────────────────────
_REMOTIVE_CATS = [
    "software-dev", "devops", "design", "data",
    "product", "marketing", "writing", "finance",
    "customer-support", "all-others",
]


def fetch_remotive() -> list:
    print("    [Remotive] Fetching categories...")
    all_jobs = []
    seen_ids: set = set()

    for cat in _REMOTIVE_CATS:
        data = safe_get_json(
            "https://remotive.com/api/remote-jobs",
            params={"category": cat, "limit": 20},
        )
        if not data or "jobs" not in data:
            print(f"    [Remotive] No data for '{cat}'")
            continue

        batch = 0
        for j in data["jobs"]:
            jid = j.get("id")
            if jid in seen_ids:
                continue
            seen_ids.add(jid)

            location  = j.get("candidate_required_location", "Worldwide") or "Worldwide"
            salary_raw = (j.get("salary") or "").strip()
            salary     = salary_raw if 0 < len(salary_raw) < 50 else ""
            pub        = j.get("publication_date", "")
            date       = pub[:10] if pub else ""

            all_jobs.append(build_job(
                title    = j.get("title", ""),
                company  = j.get("company_name", ""),
                location = location,
                salary   = salary,
                tags     = j.get("tags", []),
                url      = j.get("url", "https://remotive.com"),
                source   = "Remotive",
                date     = date,
            ))
            batch += 1

        print(f"    [Remotive] {cat}: {batch}")

    print(f"    [Remotive] ✓ {len(all_jobs)} jobs total")
    return all_jobs


# ─────────────────────────────────────────────────────────────────────────
# 9. SOURCE 5 — ARBEITNOW  (replaces LinkedIn — no public API exists)
#    API: https://www.arbeitnow.com/api/job-board-api
#    Params: page (1-based)  |  No auth required
#    All listings are remote-first by platform design.
#    Job fields: slug, company_name, title, description (HTML), remote (bool),
#                tags[str], job_types[str], location, created_at (unix ts), url
# ─────────────────────────────────────────────────────────────────────────
def fetch_arbeitnow() -> list:
    print("    [Arbeitnow] Fetching pages 1-3...")
    all_jobs = []

    for page in range(1, 4):
        data = safe_get_json(
            "https://www.arbeitnow.com/api/job-board-api",
            params={"page": page},
        )
        if not data or not data.get("data"):
            print(f"    [Arbeitnow] No data on page {page}")
            break

        for j in data["data"]:
            location = j.get("location", "Worldwide") or "Worldwide"
            ts = j.get("created_at")
            try:
                date = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d") \
                       if ts else ""
            except Exception:
                date = ""

            raw_tags = list(j.get("tags") or []) + list(j.get("job_types") or [])

            all_jobs.append(build_job(
                title    = j.get("title", ""),
                company  = j.get("company_name", ""),
                location = location,
                salary   = "",
                tags     = raw_tags,
                url      = j.get("url", "https://www.arbeitnow.com"),
                source   = "Arbeitnow",
                date     = date,
            ))

        print(f"    [Arbeitnow] Page {page}: {len(data['data'])} listings")

    print(f"    [Arbeitnow] ✓ {len(all_jobs)} jobs total")
    return all_jobs


# ─────────────────────────────────────────────────────────────────────────
# 10. AGGREGATOR — merge, dedup, count skills, build payload
# ─────────────────────────────────────────────────────────────────────────
def aggregate_jobs() -> dict:
    """Run all 5 fetchers, deduplicate, count skills, return payload dict."""
    print("\n  ── Multi-Platform Job Aggregation ──")

    _SOURCES = [
        ("RemoteOK",        fetch_remoteok),
        ("Himalayas",       fetch_himalayas),
        ("WeWorkRemotely",  fetch_wwr),
        ("Remotive",        fetch_remotive),
        ("Arbeitnow",       fetch_arbeitnow),
    ]

    source_stats: dict = {}
    all_jobs:     list = []

    for name, fetcher in _SOURCES:
        try:
            batch              = fetcher()
            source_stats[name] = len(batch)
            all_jobs.extend(batch)
        except Exception as exc:
            print(f"    [ERROR] {name} crashed: {exc}")
            source_stats[name] = 0

    # ── Cross-source deduplication ─────────────────────────────────────
    seen_fps:    set  = set()
    unique_jobs: list = []
    for j in all_jobs:
        fp = j["id"]
        if fp not in seen_fps:
            seen_fps.add(fp)
            unique_jobs.append(j)

    dupes = len(all_jobs) - len(unique_jobs)

    # ── Skill demand counter (canonical tags, all sources) ─────────────
    counter: Counter = Counter()
    for j in unique_jobs:
        for skill in j["tags"]:
            counter[skill] += 1

    top_skills = [
        {"skill": s, "count": c}
        for s, c in counter.most_common(15)
    ]

    stored = unique_jobs[:MAX_JOBS_STORED]

    # ── Log summary ────────────────────────────────────────────────────
    print(f"\n  ── Aggregation Summary ──")
    print(f"    Total fetched   : {len(all_jobs):>5,}")
    print(f"    Duplicates rm   : {dupes:>5,}")
    print(f"    Unique jobs     : {len(unique_jobs):>5,}")
    print(f"    Stored (capped) : {len(stored):>5,}")
    for src, cnt in source_stats.items():
        print(f"    {src:<22}: {cnt:>4,}")
    print(f"    Top skills      : {[s['skill'] for s in top_skills[:8]]}")

    return {
        "job_volume":   len(unique_jobs),
        "top_skills":   json.dumps(top_skills),
        "jobs_data":    json.dumps(stored),
        "source_stats": json.dumps(source_stats),
    }


# ─────────────────────────────────────────────────────────────────────────
# 11. EXCHANGE RATES
# ─────────────────────────────────────────────────────────────────────────
def fetch_exchange_rates():
    print("  Fetching exchange rates...")
    data = safe_get_json("https://open.er-api.com/v6/latest/USD")
    if not data or data.get("result") != "success":
        print("  [ERROR] Exchange rate fetch failed.")
        return None

    rates = data["rates"]
    pkr   = round(rates.get("PKR", 0), 2)
    return {
        "usd_pkr":                pkr,
        "eur_pkr":                round(pkr / rates.get("EUR", 1), 2),
        "gbp_pkr":                round(pkr / rates.get("GBP", 1), 2),
        "sar_pkr":                round(pkr / rates.get("SAR", 1), 2),
        "aed_pkr":                round(pkr / rates.get("AED", 1), 2),
        "cad_pkr":                round(pkr / rates.get("CAD", 1), 2),
        "aud_pkr":                round(pkr / rates.get("AUD", 1), 2),
        "purchasing_power_index": round(100_000 / pkr, 2) if pkr else 0,
    }


# ─────────────────────────────────────────────────────────────────────────
# 12. CRYPTO
# ─────────────────────────────────────────────────────────────────────────
def fetch_crypto_rates():
    print("  Fetching crypto rates...")
    data = safe_get_json(
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=tether,bitcoin&vs_currencies=usd,pkr"
    )
    if not data:
        return {"usdt_usd": 1.0, "usdt_pkr": None, "btc_usd": None}
    return {
        "usdt_usd": data.get("tether", {}).get("usd", 1.0),
        "usdt_pkr": data.get("tether", {}).get("pkr"),
        "btc_usd":  data.get("bitcoin", {}).get("usd"),
    }


# ─────────────────────────────────────────────────────────────────────────
# 13. NEWS — RSS from PK + global tech feeds
# ─────────────────────────────────────────────────────────────────────────
_RSS_FEEDS = [
    {"name": "ProPakistani",    "url": "https://propakistani.pk/feed/",                             "pk": True,  "max": 3},
    {"name": "Profit Pakistan", "url": "https://profit.pakistantoday.com.pk/feed/",                 "pk": True,  "max": 3},
    {"name": "Hacker News",     "url": "https://hnrss.org/frontpage",                               "pk": False, "max": 3},
    {"name": "TechCrunch",      "url": "https://techcrunch.com/feed/",                              "pk": False, "max": 2},
    {"name": "The Verge",       "url": "https://www.theverge.com/rss/index.xml",                    "pk": False, "max": 2},
    {"name": "Ars Technica",    "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",  "pk": False, "max": 1},
]

_TECH_KWS = {
    "software","app","tech","ai","startup","digital","code","python",
    "developer","freelance","remote","crypto","bitcoin","cyber","cloud",
    "data","android","ios","internet","online","platform","api","open source",
    "dollar","pkr","rupee","economy","market","investment","fiverr","upwork",
    "github","tool","launch","product","funding","acquisition","llm","gpt",
}


def fetch_news_headlines() -> str:
    print("  Fetching news headlines via RSS...")
    headlines = []
    for cfg in _RSS_FEEDS:
        try:
            feed  = feedparser.parse(cfg["url"])
            count = 0
            for entry in feed.entries:
                if count >= cfg["max"]:
                    break
                title = entry.get("title", "").strip()
                link  = entry.get("link",  "").strip()
                if not title or not link:
                    continue
                if cfg["pk"] and not any(kw in title.lower() for kw in _TECH_KWS):
                    continue
                headlines.append({
                    "title":  title,
                    "source": cfg["name"],
                    "link":   link,
                    "pk":     cfg["pk"],
                })
                count += 1
        except Exception as exc:
            print(f"  [WARN] RSS {cfg['name']}: {exc}")

    print(f"  Collected {len(headlines)} headlines.")
    return json.dumps(headlines[:15])


# ─────────────────────────────────────────────────────────────────────────
# 14. AI BRIEFING — STRATOS with full 5-source context
# ─────────────────────────────────────────────────────────────────────────
def generate_ai_insight(rates: dict, jobs: dict,
                        top_skills_raw: str, news_raw: str) -> str:
    print("  Generating STRATOS briefing via Groq...")

    # Format top skills
    skills_str = "unavailable"
    if top_skills_raw:
        parsed     = json.loads(top_skills_raw)
        skills_str = ", ".join(f"{s['skill']} ({s['count']})" for s in parsed[:8])

    # Sample live job titles
    titles_str = "unavailable"
    if jobs.get("jobs_data"):
        all_j  = json.loads(jobs["jobs_data"])
        titles = [j["title"] for j in all_j[:10] if j.get("title")]
        titles_str = " | ".join(titles) if titles else "unavailable"

    # Source breakdown
    src_str = "unavailable"
    if jobs.get("source_stats"):
        stats   = json.loads(jobs["source_stats"])
        src_str = ", ".join(f"{k}: {v}" for k, v in stats.items())

    # News context
    news_str = "unavailable"
    if news_raw:
        parsed_n = json.loads(news_raw)
        lines    = [f"[{n['source']}] {n['title']}" for n in parsed_n[:6]]
        news_str = "\n".join(lines) if lines else "unavailable"

    prompt = f"""
You are STRATOS, the AI engine of IDMI — Pakistan's freelancer intelligence platform.

LIVE MARKET DATA:
- USD/PKR: {rates['usd_pkr']} | EUR/PKR: {rates['eur_pkr']} | GBP/PKR: {rates['gbp_pkr']}
- USDT/PKR: {rates.get('usdt_pkr', 'N/A')} | BTC/USD: ${rates.get('btc_usd', 'N/A'):,}
- Purchasing Power Index: {rates['purchasing_power_index']}

AGGREGATED JOB MARKET (5 platforms: RemoteOK, Himalayas, We Work Remotely, Remotive, Arbeitnow):
- Total unique remote listings: {jobs['job_volume']:,}
- Source breakdown: {src_str}
- Top skills in demand: {skills_str}
- Sample live job titles: {titles_str}

LATEST TECH/BUSINESS NEWS:
{news_str}

Write a STRATOS Market Briefing in EXACTLY this format — 3 labelled lines only:

Currency Outlook: [Specific advice on USD/PKR at {rates['usd_pkr']} — convert now, hold, or invoice in USD? Give a concrete reason.]

Job Market: [Which specific skills are hottest across all 5 platforms right now? Name the exact skills and roles. What does this mean for a Pakistani freelancer's earning potential this week?]

Action Item: [One concrete, specific action for a Pakistani freelancer this week — tie it to the rate, the top skills, and a relevant headline if possible.]
"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are STRATOS — a precise AI market analyst for Pakistan's digital economy. "
                        "Output EXACTLY 3 lines starting with 'Currency Outlook:', 'Job Market:', 'Action Item:'. "
                        "No bullet points. No markdown. Reference specific numbers and skill names. "
                        "Always mention multiple platforms and skill names. Never be vague."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.28,
            max_tokens=320,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        print(f"  [ERROR] STRATOS briefing: {exc}")
        return (
            f"Currency Outlook: USD/PKR is at {rates['usd_pkr']} — STRATOS briefing unavailable this cycle. "
            f"Job Market: {jobs['job_volume']:,} unique remote listings tracked across 5 platforms. "
            f"Action Item: Check the Market Intelligence page for live skill demand and job listings."
        )


# ─────────────────────────────────────────────────────────────────────────
# 15. MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────
def run_ingestion_pipeline():
    now = datetime.now(timezone.utc)
    print(f"\n{'='*64}")
    print(f"  IDMI Ingestion Pipeline v4.0  |  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*64}")

    rates = fetch_exchange_rates()
    if not rates:
        print("[FATAL] Exchange rates unavailable. Aborting.")
        return

    crypto = fetch_crypto_rates()
    rates.update(crypto)

    jobs = aggregate_jobs()
    news = fetch_news_headlines()

    ai_insight = generate_ai_insight(rates, jobs, jobs["top_skills"], news)

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
        "source_stats":           jobs["source_stats"],
        "news_headlines":         news,
        "ai_sentiment":           ai_insight,
    }

    print("\n  Storing snapshot to Supabase...")
    try:
        supabase.table("market_intel").insert(payload).execute()
        print(f"  ✓ Pipeline complete — {len(payload)} fields stored.")
        print(f"  USD/PKR: {rates['usd_pkr']} | "
              f"Unique jobs: {jobs['job_volume']:,} | "
              f"Headlines: {len(json.loads(news))}")
    except Exception as exc:
        print(f"  [FATAL] Supabase insert failed: {exc}")
        raise

    print(f"{'='*64}\n")


if __name__ == "__main__":
    run_ingestion_pipeline()
