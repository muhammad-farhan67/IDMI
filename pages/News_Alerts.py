"""
pages/4_📰_News___Alerts.py — Pakistani tech news feed + PKR rate alert setter.

News headlines are pulled from the JSON stored by harvester v2.
Alert system uses Streamlit session state — users set a threshold and see a
banner when the live rate crosses it. (For persistent alerts, a Telegram bot
section explains the one-time setup.)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import streamlit as st
from utils.db import load_data, get_latest, parse_json_col
from utils.theme import inject_css

st.set_page_config(page_title="News & Alerts | IDMI", page_icon="📰", layout="wide")
inject_css()

st.title("News & Alerts")
st.caption("Latest Pakistani tech headlines and USD/PKR rate alert triggers.")

df = load_data()
latest  = get_latest(df)
live_rate = float(latest.get("usd_pkr_rate", 0))
headlines = parse_json_col(latest, "news_headlines")

# ── News feed ──────────────────────────────────────────────────────────────
col_news, col_alerts = st.columns([3, 2], gap="large")

with col_news:
    st.subheader("Latest Headlines")

    if headlines:
        for item in headlines:
            title  = item.get("title", "")
            source = item.get("source", "")
            link   = item.get("link", "#")
            if not title:
                continue
            st.markdown(f"""
            <div class="news-card">
                <div class="source">{source}</div>
                <a class="headline" href="{link}" target="_blank">{title}</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(
            "No headlines yet — the harvester pipeline needs to run at least once "
            "with the updated harvester v2 that includes RSS fetching."
        )

    st.caption("Sources: Dawn Tech · The News · ProPakistani — via free RSS")

# ── Rate alerts ────────────────────────────────────────────────────────────
with col_alerts:
    st.subheader("Rate Alert")
    st.caption(f"Live USD/PKR: **₨ {live_rate}**")

    if "alert_threshold" not in st.session_state:
        st.session_state["alert_threshold"] = round(live_rate + 5, 0) if live_rate else 285.0
    if "alert_direction" not in st.session_state:
        st.session_state["alert_direction"] = "rises above"

    direction = st.selectbox(
        "Alert me when USD/PKR",
        ["rises above", "falls below"],
        key="alert_direction",
    )
    threshold = st.number_input(
        "Threshold (PKR)",
        value=st.session_state["alert_threshold"],
        step=1.0,
        key="alert_threshold",
    )

    # Check trigger
    triggered = False
    if direction == "rises above" and live_rate >= threshold:
        triggered = True
    elif direction == "falls below" and live_rate <= threshold:
        triggered = True

    if triggered and live_rate:
        st.error(
            f"🔔 **Alert triggered!**  \n"
            f"USD/PKR is ₨ {live_rate} — it has {direction.replace('s above', '')} "
            f"your threshold of ₨ {threshold:.0f}."
        )
    elif live_rate:
        diff = abs(live_rate - threshold)
        st.success(f"✓ No alert. Rate is ₨ {diff:.1f} away from threshold.")

    st.divider()

    # ── Telegram setup guide ───────────────────────────────────────────────
    st.subheader("Persistent Alerts via Telegram")
    st.caption(
        "Get notified on your phone instantly — completely free. "
        "Set up once, alerts fire from your GitHub Action."
    )

    with st.expander("Setup guide (5 minutes, free)"):
        st.markdown("""
**Step 1** — Create a Telegram bot  
Open Telegram → search `@BotFather` → send `/newbot` → give it a name → copy the **API token**.

**Step 2** — Get your Chat ID  
Start a conversation with your bot, then open:  
`https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`  
Copy the `"id"` value from the `"chat"` object.

**Step 3** — Add secrets to GitHub  
Go to your repo → **Settings → Secrets → Actions** → add:
- `TELEGRAM_BOT_TOKEN` — your bot token
- `TELEGRAM_CHAT_ID` — your chat ID

**Step 4** — Add this to your `harvester.py`  
```python
import os, requests

def send_telegram_alert(message):
    token   = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
    )

# Add inside run_ingestion_pipeline(), after fetching rates:
ALERT_THRESHOLD = 290  # your threshold
if pkr_rate > ALERT_THRESHOLD:
    send_telegram_alert(
        f"🚨 <b>IDMI Rate Alert</b>\\n"
        f"USD/PKR has risen to <b>₨ {pkr_rate}</b>\\n"
        f"Above your threshold of ₨ {ALERT_THRESHOLD}"
    )
```
That's it — free, instant, and works on every GitHub Action run.
        """)

st.divider()

# ── All-time news archive ──────────────────────────────────────────────────
st.subheader("News Archive")
st.caption("All headlines collected across pipeline runs.")

if "news_headlines" in df.columns:
    archive = []
    for _, row in df.iterrows():
        try:
            items = json.loads(row["news_headlines"]) if isinstance(row["news_headlines"], str) else []
            for item in items:
                item["snapshot_time"] = str(row["timestamp"])[:16]
                archive.append(item)
        except Exception:
            pass

    if archive:
        import pandas as pd
        archive_df = pd.DataFrame(archive).drop_duplicates(subset=["title"])
        archive_df = archive_df[["snapshot_time", "source", "title", "link"]]
        archive_df.columns = ["Snapshot", "Source", "Headline", "Link"]

        search = st.text_input("Search headlines", placeholder="e.g. dollar, freelance, rupee…")
        if search:
            archive_df = archive_df[
                archive_df["Headline"].str.contains(search, case=False, na=False)
            ]

        st.dataframe(archive_df, use_container_width=True, hide_index=True,
                     column_config={"Link": st.column_config.LinkColumn("Link")})
    else:
        st.info("No archived headlines yet.")
else:
    st.info("Headlines will appear here after the updated harvester runs.")
