"""
pages/Tech_Prices.py — Software subscription and hardware prices in PKR.

All USD prices are multiplied by the live USD/PKR rate from IDMI's pipeline.
No paid APIs needed — prices are maintained as a curated dataset.
Tabs: Software | Hardware | AI Price Search (Groq)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import pandas as pd
from utils.db import load_data, get_latest
from utils.theme import inject_css

st.set_page_config(page_title="Tech Prices | IDMI", page_icon="💻", layout="wide")
inject_css()

st.title("Tech Prices in PKR")
st.caption(
    "Live USD → PKR conversion of popular software subscriptions and hardware. "
    "Prices update automatically as exchange rates change."
)

# ── Live rate ─────────────────────────────────────────────────────────────
df     = load_data()
latest = get_latest(df)
USD_PKR = float(latest.get("usd_pkr_rate") or 280.0)

st.markdown(
    f'<p style="font-size:13px;margin-bottom:4px;">'
    f'<span class="live-dot"></span>'
    f'Using live rate: <strong>₨ {USD_PKR:,.1f}</strong> per USD</p>',
    unsafe_allow_html=True,
)

def to_pkr(usd): return round(usd * USD_PKR)
def pkr_str(usd): return f"₨ {to_pkr(usd):,}"

# ══════════════════════════════════════════════════════════════════════════
# DATA  — curated USD prices (update these when prices change)
# ══════════════════════════════════════════════════════════════════════════

SOFTWARE = {
    "🤖 AI & Productivity": [
        ("ChatGPT Plus",           20.0,  "mo", "GPT-4o, image gen, custom GPTs"),
        ("Claude Pro",             20.0,  "mo", "Claude Sonnet/Opus, extended context"),
        ("Gemini Advanced",        19.99, "mo", "Google Gemini Ultra, Workspace AI"),
        ("Perplexity Pro",         20.0,  "mo", "AI search with citations"),
        ("Notion AI (add-on)",      8.0,  "mo", "AI writing inside Notion"),
        ("Otter.ai Pro",           16.99, "mo", "AI meeting transcription"),
    ],
    "💻 Developer Tools": [
        ("GitHub Copilot",         10.0,  "mo", "AI code completion in any IDE"),
        ("GitHub Pro",              4.0,  "mo", "Private repos, advanced CI/CD"),
        ("Cursor Pro",             20.0,  "mo", "AI-first code editor"),
        ("JetBrains All Products", 24.9,  "mo", "IntelliJ, PyCharm, WebStorm etc."),
        ("VS Code",                 0.0,  "mo", "Free and open source"),
        ("Postman Basic",           0.0,  "mo", "Free tier available"),
        ("Linear",                  8.0,  "mo", "Issue tracking for devs"),
        ("Vercel Pro",             20.0,  "mo", "Frontend deployment platform"),
        ("Railway Starter",         5.0,  "mo", "Deploy any app easily"),
        ("Supabase Pro",           25.0,  "mo", "Postgres + Auth + Storage"),
        ("PlanetScale Scaler",     29.0,  "mo", "Serverless MySQL"),
        ("Cloudflare Pro",         20.0,  "mo", "CDN, DNS, Workers"),
    ],
    "🎨 Design & Creative": [
        ("Adobe CC All Apps",      54.99, "mo", "All Adobe desktop + mobile apps"),
        ("Adobe Photoshop only",   22.99, "mo", "Single-app plan"),
        ("Figma Professional",     12.0,  "mo", "UI/UX design & prototyping"),
        ("Canva Pro",              12.99, "mo", "Easy graphic design"),
        ("Framer",                 20.0,  "mo", "No-code website builder"),
        ("Loom Business",          12.5,  "mo", "Screen recording & sharing"),
        ("Webflow CMS",            23.0,  "mo", "Visual web development"),
        ("Sketch",                  9.0,  "mo", "Mac-only UI design tool"),
    ],
    "📂 Business & Collaboration": [
        ("Google Workspace Starter", 6.0, "mo", "Gmail, Drive 30GB, Meet"),
        ("Microsoft 365 Business",   6.0, "mo", "Office apps + 1TB OneDrive"),
        ("Slack Pro",                7.25,"mo", "Team messaging & channels"),
        ("Zoom Pro",                13.32,"mo", "Video meetings up to 100"),
        ("Notion Plus",             10.0, "mo", "Notes, wikis, project management"),
        ("Trello Standard",          5.0, "mo", "Kanban boards"),
        ("Monday.com Basic",        12.0, "mo", "Work OS & project tracking"),
        ("Dropbox Plus",            11.99,"mo", "2TB cloud storage"),
        ("1Password Teams",          4.99,"mo", "Password manager per seat"),
    ],
    "🚀 Freelance Platforms": [
        ("Upwork Freelancer Plus",  14.99,"mo", "Profile boost, connect refresh"),
        ("Fiverr Seller Plus",      29.0, "mo", "Analytics, priority support"),
        ("LinkedIn Premium Career", 29.99,"mo", "InMail, who viewed profile"),
        ("Toptal",                   0.0, "mo", "Free to apply (invite-based)"),
        ("Contra Pro",               0.0, "mo", "0% commission, free"),
    ],
    "☁️ Cloud & Hosting": [
        ("AWS Free Tier",            0.0, "mo", "Free 12-month starter limits"),
        ("DigitalOcean Droplet",     4.0, "mo", "1 vCPU, 1GB RAM, 25GB SSD"),
        ("Hetzner CX11",             3.29,"mo", "2 vCPU, 2GB RAM (EU)"),
        ("Namecheap .com domain",    8.88,"yr", "Domain registration/renewal"),
        ("Cloudflare R2",            0.0, "mo", "15GB free object storage"),
        ("Resend",                   0.0, "mo", "3000 emails/mo free tier"),
    ],
    "🔐 VPN & Security": [
        ("NordVPN Standard",         4.49,"mo", "6 devices, ad blocker"),
        ("ExpressVPN",              12.95,"mo", "8 devices, fast servers"),
        ("ProtonVPN Plus",           7.99,"mo", "Privacy-focused, Swiss"),
        ("Surfshark One",            3.19,"mo", "Unlimited devices"),
        ("Malwarebytes Premium",     3.75,"mo", "Real-time protection"),
    ],
}

HARDWARE = {
    "💻 Laptops": [
        ("MacBook Pro 14\" M4",       1_999, "Best-in-class for dev/design"),
        ("MacBook Air 13\" M3",       1_099, "Lightweight, fanless, great battery"),
        ("MacBook Air 15\" M3",       1_299, "Larger screen, same M3 chip"),
        ("Dell XPS 15 (2024)",        1_499, "Windows powerhouse for devs"),
        ("Lenovo ThinkPad X1 Carbon", 1_200, "Business ultrabook, great keyboard"),
        ("ASUS Zenbook 14 OLED",        699, "Budget OLED screen, Windows 11"),
        ("Acer Swift 3 (Ryzen 7)",      649, "Affordable all-rounder"),
    ],
    "🖥️ Monitors": [
        ("LG UltraWide 34\" QHD",     449, "Curved ultrawide, great for code"),
        ("Dell U2723D 27\" 4K",       499, "IPS 4K, USB-C 90W charging"),
        ("LG 27UK850 27\" 4K",        399, "4K IPS, USB-C, HDR10"),
        ("ASUS ProArt 27\" 4K",       549, "Factory calibrated, creators"),
        ("BenQ GW2780 27\" FHD",      199, "Budget 1080p IPS, easy on eyes"),
        ("Samsung Odyssey G5 27\"",   299, "1440p 165Hz gaming/dev dual use"),
    ],
    "⌨️ Keyboards & Mice": [
        ("Logitech MX Keys S",        109, "Wireless, backlit, cross-device"),
        ("Keychron K2 Pro",            89, "Mechanical, hot-swap, wireless"),
        ("Logitech MX Master 3S",      99, "Best ergonomic mouse for devs"),
        ("Magic Keyboard (USB-C)",    129, "Mac-native, slim, quiet"),
        ("Keychron Q1 Pro",           199, "Premium gasket mount mechanical"),
        ("Razer DeathAdder V3",        59, "Lightweight wired mouse"),
    ],
    "🎧 Audio & Mic": [
        ("Sony WH-1000XM5",          349, "Best ANC headphones"),
        ("Apple AirPods Pro 2",      249, "Best for Mac/iPhone users"),
        ("Jabra Evolve2 55",         449, "Business headset, Teams certified"),
        ("Blue Yeti USB Mic",        129, "Popular podcast/call mic"),
        ("Rode NT-USB Mini",          99, "Compact studio USB mic"),
        ("Elgato Wave 3",            149, "Streaming/recording mic"),
    ],
    "📱 Mobile & Tablets": [
        ("iPhone 16 Pro",            999, "Best iPhone, 48MP camera"),
        ("iPhone 15",                799, "Last year flagship, solid value"),
        ("Samsung Galaxy S25",       799, "Best Android flagship 2025"),
        ("iPad Pro 13\" M4",       1_099, "Best tablet for designers"),
        ("iPad Air 13\"",             799, "Value pick for creative work"),
        ("Samsung Galaxy Tab S9",    799, "Android tablet for productivity"),
    ],
    "🔌 Accessories": [
        ("CalDigit TS4 Thunderbolt Dock",  249, "Best dock for MacBook — 18 ports"),
        ("Anker 727 Thunderbolt Dock",     199, "12-in-1 Thunderbolt 4 hub"),
        ("Elgato Stream Deck MK.2",        149, "Macro shortcuts, streaming"),
        ("Logitech C920x HD Webcam",        69, "1080p/30fps, clear video calls"),
        ("APC Back-UPS 1500VA",            160, "UPS — essential for Pakistan"),
        ("Xiaomi 67W GaN Charger",          25, "Compact fast charger"),
        ("SanDisk 1TB Portable SSD",        90, "Fast portable backup drive"),
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════
tab_sw, tab_hw, tab_search = st.tabs([
    "📦 Software Subscriptions",
    "🖥️ Hardware Prices",
    "🔍 AI Price Search",
])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 — SOFTWARE
# ─────────────────────────────────────────────────────────────────────────
with tab_sw:
    # Search + filter bar
    sc1, sc2 = st.columns([3, 1])
    with sc1:
        sw_search = st.text_input(
            "Search tools", placeholder="e.g. GitHub, Adobe, VPN…",
            label_visibility="collapsed"
        )
    with sc2:
        show_free = st.toggle("Free only", value=False)

    # Build flat dataframe for display / search
    all_sw_rows = []
    for category, items in SOFTWARE.items():
        for name, price_usd, period, desc in items:
            if show_free and price_usd > 0:
                continue
            if sw_search and sw_search.lower() not in name.lower() \
                         and sw_search.lower() not in desc.lower() \
                         and sw_search.lower() not in category.lower():
                continue
            all_sw_rows.append({
                "Category":  category,
                "Tool":      name,
                "USD / mo":  f"${price_usd:.2f}" if price_usd else "Free",
                "PKR / mo":  pkr_str(price_usd) if price_usd else "Free",
                "Annual PKR": pkr_str(price_usd * 12) if price_usd else "Free",
                "Note":      desc,
                "_usd":      price_usd,
            })

    if not all_sw_rows:
        st.info("No tools match your search.")
    else:
        sw_df = pd.DataFrame(all_sw_rows)

        # Show by category
        for cat in sw_df["Category"].unique():
            cat_df = sw_df[sw_df["Category"] == cat]
            st.markdown(f"#### {cat}")
            st.dataframe(
                cat_df[["Tool","USD / mo","PKR / mo","Annual PKR","Note"]],
                use_container_width=True, hide_index=True,
            )

        st.divider()

        # Top 10 most expensive chart
        top10 = sw_df[sw_df["_usd"] > 0].nlargest(10, "_usd")
        if not top10.empty:
            st.subheader("Top 10 most expensive subscriptions (monthly)")
            fig_sw = px.bar(
                top10.sort_values("_usd"),
                x="_usd", y="Tool", orientation="h",
                color="_usd",
                color_continuous_scale=[[0,"#e8f5ee"],[1,"#01411C"]],
                text=top10.sort_values("_usd")["PKR / mo"],
                labels={"_usd":"USD / month","Tool":""},
            )
            fig_sw.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0,r=0,t=10,b=0),
                coloraxis_showscale=False,
                xaxis=dict(title="USD / month",gridcolor="#f0f0f0"),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_sw, use_container_width=True)

        # Monthly budget calculator
        st.divider()
        st.subheader("Budget Calculator")
        st.caption("Pick the tools you use and see your total monthly software cost in PKR.")

        all_paid = sw_df[sw_df["_usd"] > 0][["Tool","_usd"]].values.tolist()
        selected_tools = st.multiselect(
            "My subscriptions",
            options=[t for t,_ in all_paid],
            default=[],
        )
        if selected_tools:
            price_map = {t:p for t,p in all_paid}
            total_usd = sum(price_map.get(t,0) for t in selected_tools)
            total_pkr = to_pkr(total_usd)
            bc1, bc2, bc3 = st.columns(3)
            bc1.metric("Monthly USD", f"${total_usd:,.2f}")
            bc2.metric("Monthly PKR", f"₨ {total_pkr:,}")
            bc3.metric("Annual PKR",  f"₨ {total_pkr*12:,}")


# ─────────────────────────────────────────────────────────────────────────
# TAB 2 — HARDWARE
# ─────────────────────────────────────────────────────────────────────────
with tab_hw:
    hw_search = st.text_input(
        "Search hardware", placeholder="e.g. MacBook, monitor, mic…",
        label_visibility="collapsed", key="hw_search"
    )

    all_hw_rows = []
    for category, items in HARDWARE.items():
        for name, price_usd, desc in items:
            if hw_search and hw_search.lower() not in name.lower() \
                         and hw_search.lower() not in desc.lower() \
                         and hw_search.lower() not in category.lower():
                continue
            all_hw_rows.append({
                "Category": category,
                "Item":     name,
                "USD":      f"${price_usd:,}",
                "PKR":      f"₨ {to_pkr(price_usd):,}",
                "Note":     desc,
                "_usd":     price_usd,
            })

    if not all_hw_rows:
        st.info("No hardware matches your search.")
    else:
        hw_df = pd.DataFrame(all_hw_rows)

        for cat in hw_df["Category"].unique():
            cat_df = hw_df[hw_df["Category"] == cat]
            st.markdown(f"#### {cat}")
            st.dataframe(
                cat_df[["Item","USD","PKR","Note"]],
                use_container_width=True, hide_index=True,
            )

        st.divider()

        # All hardware scatter — USD price vs PKR
        st.subheader("Hardware price overview")
        fig_hw = px.scatter(
            hw_df, x="_usd", y="Category",
            size="_usd", color="Category",
            hover_name="Item",
            hover_data={"PKR": True, "_usd": False, "Category": False},
            labels={"_usd":"USD price","Category":""},
            color_discrete_sequence=px.colors.qualitative.Dark24,
        )
        fig_hw.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(title="USD price",gridcolor="#f0f0f0"),
            yaxis=dict(showgrid=False),
            showlegend=False,
            height=360,
        )
        st.plotly_chart(fig_hw, use_container_width=True)

        # ── UPS callout — very relevant for Pakistan ──────────────────────
        st.info(
            "🇵🇰 **Pakistan-specific tip** — A quality UPS (Uninterruptible Power Supply) "
            "is arguably the most important hardware purchase for a Pakistani freelancer. "
            "Load-shedding can corrupt work, disconnect from clients mid-call, and "
            "damage hardware. Budget ₨ 45,000–60,000 for a decent 1500VA unit. "
            "It's a business expense and tax-deductible."
        )

        # ── Currency converter for single item ────────────────────────────
        st.divider()
        st.subheader("Single Item Converter")
        sc1, sc2 = st.columns(2)
        with sc1:
            item_usd = st.number_input("Item price (USD)", value=999.0, step=10.0)
        with sc2:
            st.metric("Price in PKR", f"₨ {to_pkr(item_usd):,}")
            st.caption(f"At ₨ {USD_PKR:,.1f} / USD")


# ─────────────────────────────────────────────────────────────────────────
# TAB 3 — AI PRICE SEARCH
# ─────────────────────────────────────────────────────────────────────────
with tab_search:
    st.subheader("AI Price Search")
    st.caption(
        "Ask STRATOS about any software or hardware price, Pakistani availability, "
        "alternatives, or buying advice. Powered by Groq (free tier)."
    )

    if "price_search_history" not in st.session_state:
        st.session_state.price_search_history = []

    # Quick prompt chips
    st.markdown("**Quick searches:**")
    chip_cols = st.columns(4)
    chips = [
        "Cost of Adobe CC in PKR?",
        "Cheapest way to get Microsoft Office?",
        "Best budget monitor for Pakistani devs?",
        "How to buy MacBook from Pakistan?",
    ]
    for col, chip in zip(chip_cols, chips):
        if col.button(chip, use_container_width=True, key=f"chip_{chip[:10]}"):
            st.session_state.price_search_history.append({"role":"user","content":chip})

    # Chat input
    user_q = st.chat_input("e.g. How much does Figma cost in PKR? Any cheaper alternatives?")
    if user_q:
        st.session_state.price_search_history.append({"role":"user","content":user_q})

    # Display history
    for msg in st.session_state.price_search_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Generate response if last message is from user
    if (st.session_state.price_search_history and
            st.session_state.price_search_history[-1]["role"] == "user"):

        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                from groq import Groq
                groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY",""))
                if not groq_key:
                    placeholder.error("GROQ_API_KEY not set in Streamlit secrets.")
                else:
                    client = Groq(api_key=groq_key)
                    system = f"""You are STRATOS, the AI engine of IDMI — a Pakistani freelancer intelligence platform.

Current live data:
- USD/PKR rate: {USD_PKR:.2f}

When asked about prices:
1. Give the USD price first
2. Convert to PKR using the live rate above
3. Note if the product is available in Pakistan via official channels
4. Always suggest 1-2 free or cheaper alternatives when relevant
5. Be specific and practical. No fluff.
6. If asking about hardware, mention whether it's available in local Pakistani markets (Hafeez Centre, Liberty Market etc.) or only importable."""

                    messages_api = [{"role":"system","content":system}] + \
                                   st.session_state.price_search_history

                    full_resp = ""
                    stream = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages_api,
                        temperature=0.3,
                        max_tokens=600,
                        stream=True,
                    )
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content or ""
                        full_resp += delta
                        placeholder.markdown(full_resp + "▋")
                    placeholder.markdown(full_resp)

                    st.session_state.price_search_history.append(
                        {"role":"assistant","content":full_resp}
                    )
            except Exception as e:
                placeholder.error(f"Search error: {e}")

    if st.session_state.price_search_history:
        if st.button("Clear search history", key="clear_price"):
            st.session_state.price_search_history = []
            st.rerun()

    st.divider()
    st.caption(
        "Prices in the Software and Hardware tabs are maintained manually and "
        "converted using the live USD/PKR rate from your IDMI pipeline. "
        "AI search responses use Groq Llama 3.3 70B with current rate context."
    )
