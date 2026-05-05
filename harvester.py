"""
IDMI Harvester v2.1 — Indus Digital Market Intelligence
All data sources are FREE with no paid API keys required.
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
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "IDMI/2.1"})
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
        "purchasing_power_index": round(100000 / pkr, 2) if pkr else 0,
    }


# ---------------------------------------------------------------------------
# 4. CRYPTO / STABLECOIN
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
# 5. REAL REMOTE JOBS
# ---------------------------------------------------------------------------
TRACKED_SKILLS = [
    "python", "javascript", "react", "node", "php", "wordpress",
    "django", "flutter", "android", "ios", "devops", "aws",
    "machine-learning", "data-science", "shopify", "laravel",
    "vue", "typescript", "postgresql", "mongodb", "docker",
    "graphic-design", "ui-ux", "figma", "seo", "copywriting",
]

def fetch_jobs_and_skills():
    print("  Fetching remote jobs from RemoteOK...")
    data = safe_get("https://remoteok.com/api")
    if not data:
        return {"job_volume": 0, "top_skills": json.dumps([])}

    jobs = [j for j in data if isinstance(j, dict) and "tags" in j]

    tag_counter = Counter()
    for job in jobs:
        for tag in job.get("tags", []):
            tag_lower = tag.lower().replace(" ", "-")
            if tag_lower in TRACKED_SKILLS:
                tag_counter[tag_lower] += 1

    top_skills = [{"skill": skill, "count": count}
                  for skill, count in tag_counter.most_common(10)]

    return {
        "job_volume":  len(jobs),
        "top_skills":  json.dumps(top_skills),
    }


# ---------------------------------------------------------------------------
# 6. NEWS HEADLINES — Diverse RSS feeds (Pakistan + global tech)
# ---------------------------------------------------------------------------
RSS_FEEDS = [
    # Pakistani sources
    ("Dawn Tech",        "https://www.dawn.com/feeds/technology"),
    ("The News Tech",    "https://www.thenews.com.pk/rss/2/12"),
    ("ProPakistani",     "https://propakistani.pk/feed/"),
    ("Profit Pakistan",  "https://profit.pakistantoday.com.pk/feed/"),
    ("ARY News Tech",    "https://arynews.tv/feed/"),
    # Global tech relevant to freelancers
    ("TechCrunch",       "https://techcrunch.com/feed/"),
    ("Hacker News",      "https://hnrss.org/frontpage"),
    ("Dev.to",           "https://dev.to/feed"),
]

def fetch_news_headlines(max_per_feed=2):
    """
    Pulls headlines from 8 RSS feeds — 5 Pakistani + 3 global tech.
    max_per_feed=2 keeps the mix balanced (cap 15 total).
    """
    print("  Fetching news headlines via RSS...")
    headlines = []
    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"  [WARN] No entries from {source_name}")
                continue
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                link  = entry.get("link", "")
                if title and link:
                    headlines.append({
                        "title":  title,
                        "source": source_name,
                        "link":   link,
                    })
        except Exception as e:
            print(f"  [WARN] RSS feed failed ({source_name}): {e}")

    print(f"  Collected {len(headlines)} headlines from {len(RSS_FEEDS)} feeds.")
    return json.dumps(headlines[:15])


# ---------------------------------------------------------------------------
# 7. AI MARKET BRIEFING
# ---------------------------------------------------------------------------
def generate_ai_insight(rates, jobs, top_skills_raw):
    print("  Generating AI market insight via Groq...")

    top_skills_list = ", ".join(
        [s["skill"] for s in json.loads(top_skills_raw)][:5]
    ) if top_skills_raw else "unavailable"

    prompt = f"""
You are STRATOS, the AI engine of IDMI (Indus Digital Market Intelligence).

Current market data:
- USD/PKR rate: {rates['usd_pkr']}
- EUR/PKR rate: {rates['eur_pkr']}
- GBP/PKR rate: {rates['gbp_pkr']}
- USDT/PKR rate: {rates.get('usdt_pkr', 'N/A')}
- Purchasing Power Index (PKR per $100k): {rates['purchasing_power_index']}
- Live remote job listings: {jobs['job_volume']}
- Top in-demand skills today: {top_skills_list}

Write exactly 3 sentences for Pakistani freelancers:
1. Currency outlook: Is now a good time to invoice in USD or hold dollars?
2. Job market: Which skills are seeing demand and what does that mean for earnings?
3. Action item: One specific, practical recommendation for this week.

Be direct, data-driven, and specific to Pakistan's freelance economy.
"""
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a concise financial analyst for Pakistan's digital economy. Never use bullet points. Always write exactly 3 sentences."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=200,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [ERROR] AI insight generation failed: {e}")
        return f"STRATOS unavailable. USD/PKR is at {rates['usd_pkr']} as of this snapshot."


# ---------------------------------------------------------------------------
# 8. MAIN PIPELINE
# ---------------------------------------------------------------------------
def run_ingestion_pipeline():
    now = datetime.now(timezone.utc)
    print(f"\n{'='*55}")
    print(f"  IDMI Ingestion Pipeline v2.1  |  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}")

    rates = fetch_exchange_rates()
    if not rates:
        print("[FATAL] Cannot proceed without exchange rate data. Aborting.")
        return

    crypto = fetch_crypto_rates()
    jobs   = fetch_jobs_and_skills()
    news   = fetch_news_headlines()

    rates.update(crypto)

    ai_insight = generate_ai_insight(rates, jobs, jobs["top_skills"])

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
        "news_headlines":         news,
        "ai_sentiment":           ai_insight,
    }

    print("  Storing to Supabase...")
    try:
        supabase.table("market_intel").insert(payload).execute()
        print(f"\n  Pipeline complete. {len(payload)} fields stored.")
        print(f"  USD/PKR: {rates['usd_pkr']} | Jobs: {jobs['job_volume']} | Headlines: {len(json.loads(news))}")
    except Exception as e:
        print(f"  [FATAL] Supabase insert failed: {e}")
        raise

    print(f"{'='*55}\n")


if __name__ == "__main__":
    run_ingestion_pipeline()
