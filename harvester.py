"""
IDMI Harvester v2 — Indus Digital Market Intelligence
All data sources are FREE with no paid API keys required.

Free sources used:
  - open.er-api.com     → multi-currency exchange rates (no key needed)
  - api.coingecko.com   → USDT/crypto prices (free, no key needed)
  - remoteok.com/api    → real remote job listings + skill tags (free, no key)
  - feedparser RSS      → Dawn Tech + The News headlines (free)
  - Groq API            → AI market briefing (free tier, already in your repo)
  - Supabase            → storage (free tier, already in your repo)
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
# 1. CREDENTIALS  (set these in GitHub Actions Secrets / Streamlit Secrets)
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
    """Fetch a URL with retries. Returns parsed JSON or None on failure."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "IDMI/2.0"})
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  [WARN] Attempt {attempt + 1} failed for {url}: {e}")
    print(f"  [ERROR] All retries exhausted for {url}")
    return None


# ---------------------------------------------------------------------------
# 3. EXCHANGE RATES  — open.er-api.com (no API key, truly free)
# ---------------------------------------------------------------------------
def fetch_exchange_rates():
    """
    Returns a dict with PKR rates for currencies Pakistani freelancers care about:
      USD (Upwork/Fiverr default), EUR, GBP, SAR (Saudi remittance),
      AED (UAE remittance), CNY (China trade)
    Also returns purchasing power index: how many PKR you get for $100.
    """
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
# 4. CRYPTO / STABLECOIN  — CoinGecko free API (no key needed)
# ---------------------------------------------------------------------------
def fetch_crypto_rates():
    """
    USDT is how many Pakistani freelancers receive and hold money.
    Returns USDT price in USD and PKR.
    """
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
# 5. REAL REMOTE JOBS  — RemoteOK public API (free, no key)
# ---------------------------------------------------------------------------
# Skills most relevant to Pakistani freelancers on global platforms
TRACKED_SKILLS = [
    "python", "javascript", "react", "node", "php", "wordpress",
    "django", "flutter", "android", "ios", "devops", "aws",
    "machine-learning", "data-science", "shopify", "laravel",
    "vue", "typescript", "postgresql", "mongodb", "docker",
    "graphic-design", "ui-ux", "figma", "seo", "copywriting",
]

def fetch_jobs_and_skills():
    """
    Pulls real job listings from RemoteOK (free public JSON API).
    Counts skill tag frequency to produce a skills demand ranking.
    Returns total job count and top 10 skills as JSON.
    """
    print("  Fetching remote jobs from RemoteOK...")
    data = safe_get("https://remoteok.com/api")
    if not data:
        return {"job_volume": 0, "top_skills": json.dumps([])}

    # First item is a legal notice dict, skip it
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
# 6. NEWS HEADLINES  — Free RSS feeds, no API key needed
# ---------------------------------------------------------------------------
RSS_FEEDS = [
    ("Dawn Tech",     "https://www.dawn.com/feeds/technology"),
    ("The News Tech", "https://www.thenews.com.pk/rss/2/12"),
    ("ProPakistani",  "https://propakistani.pk/feed/"),
]

def fetch_news_headlines(max_per_feed=3):
    """
    Pulls latest tech/business headlines from Pakistani news RSS feeds.
    Returns a JSON list of {title, source, link} dicts.
    feedparser is free, open-source, requires no API key.
    """
    print("  Fetching news headlines via RSS...")
    headlines = []
    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                headlines.append({
                    "title":  entry.get("title", ""),
                    "source": source_name,
                    "link":   entry.get("link", ""),
                })
        except Exception as e:
            print(f"  [WARN] RSS feed failed ({source_name}): {e}")

    return json.dumps(headlines[:10])  # cap at 10 headlines total


# ---------------------------------------------------------------------------
# 7. AI MARKET BRIEFING  — Groq free tier (Llama 3.3 70B)
# ---------------------------------------------------------------------------
def generate_ai_insight(rates, jobs, top_skills_raw):
    """
    Sends real data to Groq and gets a 3-sentence market briefing.
    Groq free tier: 14,400 req/day — more than enough for hourly runs.
    """
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
    print(f"  IDMI Ingestion Pipeline v2  |  {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}")

    # --- Harvest ---
    rates  = fetch_exchange_rates()
    if not rates:
        print("[FATAL] Cannot proceed without exchange rate data. Aborting.")
        return

    crypto = fetch_crypto_rates()
    jobs   = fetch_jobs_and_skills()
    news   = fetch_news_headlines()

    # Merge crypto into rates dict for AI prompt
    rates.update(crypto)

    ai_insight = generate_ai_insight(rates, jobs, jobs["top_skills"])

    # --- Build payload ---
    payload = {
        "timestamp":              now.isoformat(),

        # Exchange rates
        "usd_pkr_rate":           rates["usd_pkr"],
        "eur_pkr_rate":           rates["eur_pkr"],
        "gbp_pkr_rate":           rates["gbp_pkr"],
        "sar_pkr_rate":           rates["sar_pkr"],
        "aed_pkr_rate":           rates["aed_pkr"],
        "purchasing_power_index": rates["purchasing_power_index"],

        # Crypto
        "usdt_pkr_rate":          rates.get("usdt_pkr"),
        "btc_usd_rate":           rates.get("btc_usd"),

        # Jobs
        "job_volume":             jobs["job_volume"],
        "top_skills":             jobs["top_skills"],   # JSON string

        # News
        "news_headlines":         news,                 # JSON string

        # AI
        "ai_sentiment":           ai_insight,
    }

    # --- Store ---
    print("  Storing to Supabase...")
    try:
        supabase.table("market_intel").insert(payload).execute()
        print(f"\n  Pipeline complete. {len(payload)} fields stored.")
        print(f"  USD/PKR: {rates['usd_pkr']} | Jobs: {jobs['job_volume']} | Skills: {jobs['top_skills'][:60]}...")
    except Exception as e:
        print(f"  [FATAL] Supabase insert failed: {e}")
        raise

    print(f"{'='*55}\n")


if __name__ == "__main__":
    run_ingestion_pipeline()
