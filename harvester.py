"""
IDMI Harvester v3.0 — Indus Digital Market Intelligence

Changes from v2.2:
  - fetch_jobs_and_skills() now stores full job details (title, company,
    salary, location, url, tags) as jobs_data JSON for the UI to render.
  - generate_ai_insight() includes news headlines + job position titles
    so STRATOS briefings are more specific and actionable.
"""

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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# 2. HELPER — safe HTTP fetch with timeout + retries
# ---------------------------------------------------------------------------
def safe_get(url, retries=3, timeout=15):
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "IDMI/3.0"})
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
    pkr = round(rates.get("PKR", 0), 2)

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
        "usdt_usd": data.get("tether", {}).get("usd", 1.0),
        "usdt_pkr": data.get("tether", {}).get("pkr"),
        "btc_usd":  data.get("bitcoin", {}).get("usd"),
    }


# ---------------------------------------------------------------------------
# 5. REMOTE JOBS — full job details for the UI
# ---------------------------------------------------------------------------
TRACKED_SKILLS = [
    "python", "javascript", "react", "node", "php", "wordpress",
    "django", "flutter", "android", "ios", "devops", "aws",
    "machine-learning", "data-science", "shopify", "laravel",
    "vue", "typescript", "postgresql", "mongodb", "docker",
    "graphic-design", "ui-ux", "figma", "seo", "copywriting",
    "golang", "rust", "kubernetes", "terraform", "next.js",
    "openai", "llm", "fastapi", "swift", "kotlin",
]

# Max jobs to store in detail (keeps payload reasonable)
MAX_JOBS_DETAIL = 60


def fetch_jobs_and_skills():
    """
    Fetch RemoteOK jobs and return:
      - job_volume : total count of live listings
      - top_skills : JSON list of {skill, count} for top 10 skills
      - jobs_data  : JSON list of top MAX_JOBS_DETAIL job objects with
                     title, company, salary, location, url, tags
    """
    print("  Fetching remote jobs from RemoteOK...")
    data = safe_get("https://remoteok.com/api")
    if not data:
        return {
            "job_volume": 0,
            "top_skills": json.dumps([]),
            "jobs_data":  json.dumps([]),
        }

    # First element is RemoteOK metadata — skip it
    jobs = [j for j in data if isinstance(j, dict) and "position" in j]

    # ── Skill tag counting ────────────────────────────────────────────────
    tag_counter = Counter()
    for job in jobs:
        for tag in job.get("tags", []):
            tag_lower = tag.lower().replace(" ", "-")
            if tag_lower in TRACKED_SKILLS:
                tag_counter[tag_lower] += 1

    top_skills = [
        {"skill": skill, "count": count}
        for skill, count in tag_counter.most_common(10)
    ]

    # ── Build compact job detail records ─────────────────────────────────
    job_records = []
    for job in jobs[:MAX_JOBS_DETAIL]:
        salary_min = job.get("salary_min") or job.get("salary_min_usd") or None
        salary_max = job.get("salary_max") or job.get("salary_max_usd") or None

        # Format salary string
        if salary_min and salary_max:
            salary_str = f"${int(salary_min):,} – ${int(salary_max):,}/yr"
        elif salary_min:
            salary_str = f"${int(salary_min):,}+/yr"
        elif salary_max:
            salary_str = f"Up to ${int(salary_max):,}/yr"
        else:
            salary_str = ""

        tags = [t.lower() for t in job.get("tags", [])[:8]]  # cap tags at 8

        job_records.append({
            "id":       str(job.get("id", "")),
            "title":    job.get("position", "").strip(),
            "company":  job.get("company", "").strip(),
            "location": job.get("location", "Worldwide").strip() or "Worldwide",
            "salary":   salary_str,
            "tags":     tags,
            "url":      job.get("url", f"https://remoteok.com/remote-jobs/{job.get('id','')}"),
            "date":     str(job.get("date", ""))[:10],
        })

    print(f"  Collected {len(jobs)} jobs | {len(job_records)} stored in detail | "
          f"Top skills: {[s['skill'] for s in top_skills[:5]]}")

    return {
        "job_volume": len(jobs),
        "top_skills": json.dumps(top_skills),
        "jobs_data":  json.dumps(job_records),
    }



# ---------------------------------------------------------------------------
# 7. AI BRIEFING — STRATOS with richer context (news + job titles)
# ---------------------------------------------------------------------------
def generate_ai_insight(rates, jobs, top_skills_raw, news_raw):
    print("  Generating STRATOS AI market insight via Groq...")

    top_skills_list = "unavailable"
    if top_skills_raw:
        parsed = json.loads(top_skills_raw)
        top_skills_list = ", ".join([f"{s['skill']} ({s['count']} listings)" for s in parsed[:6]])

    # Sample job titles to give STRATOS concrete signal
    job_titles_sample = "unavailable"
    if jobs.get("jobs_data"):
        all_jobs = json.loads(jobs["jobs_data"])
        titles = [j["title"] for j in all_jobs[:8] if j.get("title")]
        job_titles_sample = " | ".join(titles) if titles else "unavailable"

    # Latest news headlines for context
    news_context = "unavailable"
    if news_raw:
        parsed_news = json.loads(news_raw)
        headlines = [f"[{n['source']}] {n['title']}" for n in parsed_news[:6]]
        news_context = "\n".join(headlines) if headlines else "unavailable"

    prompt = f"""
You are STRATOS, the AI engine of IDMI (Indus Digital Market Intelligence) — Pakistan's freelancer intelligence platform.

LIVE MARKET DATA (this snapshot):
- USD/PKR: {rates['usd_pkr']} | EUR/PKR: {rates['eur_pkr']} | GBP/PKR: {rates['gbp_pkr']}
- USDT/PKR: {rates.get('usdt_pkr', 'N/A')} | BTC/USD: ${rates.get('btc_usd', 'N/A'):,}
- Purchasing Power Index (PKR per $100k): {rates['purchasing_power_index']}
- Live remote job listings on RemoteOK: {jobs['job_volume']:,}
- Top skill demand: {top_skills_list}
- Sample live job titles: {job_titles_sample}

LATEST TECH/BUSINESS NEWS:
{news_context}

Write a STRATOS Market Briefing in exactly this format (3 labelled sentences, no bullet points, no markdown):

Currency Outlook: [Is now a good time for Pakistani freelancers to invoice in USD, hold dollars, or convert? Be specific about the rate and trend.]

Job Market: [Which specific skills/roles are seeing the most live demand right now, and what does that mean for a Pakistani freelancer's earnings this week?]

Action Item: [One concrete, actionable recommendation based on ALL the above data — rates, jobs, AND a relevant news item if applicable.]

Be specific, data-driven, and directly relevant to Pakistan's freelance economy. No fluff.
"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are STRATOS — a precise AI market analyst for Pakistan's digital economy. "
                        "Always output exactly 3 labelled sentences in the specified format. "
                        "Never use bullet points or markdown formatting. "
                        "Be specific with numbers and skill names. Never be generic."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
            max_tokens=280,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [ERROR] AI insight generation failed: {e}")
        return (
            f"Currency Outlook: USD/PKR is at {rates['usd_pkr']} — STRATOS briefing unavailable this cycle. "
            f"Job Market: {jobs['job_volume']:,} remote listings tracked; run the pipeline to get skill insights. "
            f"Action Item: Check back after the next pipeline run for a full market briefing."
        )


# ---------------------------------------------------------------------------
# 8. MAIN PIPELINE
# ---------------------------------------------------------------------------
def run_ingestion_pipeline():
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  IDMI Ingestion Pipeline v3.0  |  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    rates = fetch_exchange_rates()
    if not rates:
        print("[FATAL] Cannot proceed without exchange rate data. Aborting.")
        return

    crypto = fetch_crypto_rates()
    jobs   = fetch_jobs_and_skills()
    news   = fetch_news_headlines()
    rates.update(crypto)

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
        "jobs_data":              jobs["jobs_data"],   # NEW — full job details
        "news_headlines":         news,
        "ai_sentiment":           ai_insight,
    }

    print("  Storing to Supabase...")
    try:
        supabase.table("market_intel").insert(payload).execute()
        print(f"\n  ✓ Pipeline complete. {len(payload)} fields stored.")
        print(f"  USD/PKR: {rates['usd_pkr']} | "
              f"Jobs: {jobs['job_volume']} | "
              f"Headlines: {len(json.loads(news))}")
    except Exception as e:
        print(f"  [FATAL] Supabase insert failed: {e}")
        raise

    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_ingestion_pipeline()
