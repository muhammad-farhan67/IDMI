"""
pages/Tech_Prices.py — Software subscription and hardware prices in PKR.
v3.0: Software tab now has search + clickable "Visit Site" links.
       Hardware tab has "Search Online" links.
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
    "Click any link to visit the official product page. Prices update automatically as exchange rates change."
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
# DATA — curated USD prices + official website URLs
# Tuple format: (Name, USD_price, period, description, website_url)
# ══════════════════════════════════════════════════════════════════════════

SOFTWARE = {
    "🤖 AI & Productivity": [
        ("ChatGPT Plus",         20.00, "mo", "GPT-4o, image gen, custom GPTs",            "https://chat.openai.com/"),
        ("Claude Pro",           20.00, "mo", "Claude Sonnet/Opus, extended context",       "https://claude.ai/"),
        ("Gemini Advanced",      19.99, "mo", "Google Gemini Ultra, Workspace AI",          "https://gemini.google.com/"),
        ("Perplexity Pro",       20.00, "mo", "AI search with citations",                   "https://www.perplexity.ai/"),
        ("Notion AI (add-on)",    8.00, "mo", "AI writing inside Notion",                   "https://www.notion.so/"),
        ("Otter.ai Pro",         16.99, "mo", "AI meeting transcription",                   "https://otter.ai/"),
    ],
    "💻 Developer Tools": [
        ("GitHub Copilot",       10.00, "mo", "AI code completion in any IDE",              "https://github.com/features/copilot"),
        ("GitHub Pro",            4.00, "mo", "Private repos, advanced CI/CD",              "https://github.com/pricing"),
        ("Cursor Pro",           20.00, "mo", "AI-first code editor",                       "https://www.cursor.com/"),
        ("JetBrains All",        24.90, "mo", "IntelliJ, PyCharm, WebStorm etc.",           "https://www.jetbrains.com/all/"),
        ("VS Code",               0.00, "mo", "Free and open source",                       "https://code.visualstudio.com/"),
        ("Postman Basic",         0.00, "mo", "Free tier available",                        "https://www.postman.com/"),
        ("Linear",                8.00, "mo", "Issue tracking for devs",                   "https://linear.app/"),
        ("Vercel Pro",           20.00, "mo", "Frontend deployment platform",               "https://vercel.com/pricing"),
        ("Railway Starter",       5.00, "mo", "Deploy any app easily",                      "https://railway.app/"),
        ("Supabase Pro",         25.00, "mo", "Postgres + Auth + Storage",                  "https://supabase.com/pricing"),
        ("PlanetScale Scaler",   29.00, "mo", "Serverless MySQL",                           "https://planetscale.com/pricing"),
        ("Cloudflare Pro",       20.00, "mo", "CDN, DNS, Workers",                          "https://www.cloudflare.com/plans/"),
    ],
    "🎨 Design & Creative": [
        ("Adobe CC All Apps",    54.99, "mo", "All Adobe desktop + mobile apps",            "https://www.adobe.com/creativecloud/plans.html"),
        ("Adobe Photoshop only", 22.99, "mo", "Single-app plan",                            "https://www.adobe.com/products/photoshop.html"),
        ("Figma Professional",   12.00, "mo", "UI/UX design & prototyping",                "https://www.figma.com/pricing/"),
        ("Canva Pro",            12.99, "mo", "Easy graphic design",                        "https://www.canva.com/canva-pro/"),
        ("Framer",               20.00, "mo", "No-code website builder",                    "https://www.framer.com/pricing/"),
        ("Loom Business",        12.50, "mo", "Screen recording & sharing",                 "https://www.loom.com/pricing"),
        ("Webflow CMS",          23.00, "mo", "Visual web development",                     "https://webflow.com/pricing"),
        ("Sketch",                9.00, "mo", "Mac-only UI design tool",                    "https://www.sketch.com/pricing/"),
    ],
    "📂 Business & Collaboration": [
        ("Google Workspace Starter", 6.00, "mo", "Gmail, Drive 30GB, Meet",                "https://workspace.google.com/pricing"),
        ("Microsoft 365 Business",   6.00, "mo", "Office apps + 1TB OneDrive",             "https://www.microsoft.com/en-us/microsoft-365/business/compare-all-plans"),
        ("Slack Pro",                7.25, "mo", "Team messaging & channels",               "https://slack.com/intl/en-us/pricing"),
        ("Zoom Pro",                13.32, "mo", "Video meetings up to 100",               "https://zoom.us/pricing"),
        ("Notion Plus",             10.00, "mo", "Notes, wikis, project management",        "https://www.notion.so/pricing"),
        ("Trello Standard",          5.00, "mo", "Kanban boards",                           "https://trello.com/pricing"),
        ("Monday.com Basic",        12.00, "mo", "Work OS & project tracking",              "https://monday.com/pricing/"),
        ("Dropbox Plus",            11.99, "mo", "2TB cloud storage",                       "https://www.dropbox.com/plans"),
        ("1Password Teams",          4.99, "mo", "Password manager per seat",               "https://1password.com/teams/"),
    ],
    "🚀 Freelance Platforms": [
        ("Upwork Freelancer Plus",  14.99, "mo", "Profile boost, connect refresh",         "https://www.upwork.com/freelancers/memberships"),
        ("Fiverr Seller Plus",      29.00, "mo", "Analytics, priority support",             "https://www.fiverr.com/seller_plus"),
        ("LinkedIn Premium Career", 29.99, "mo", "InMail, who viewed profile",             "https://premium.linkedin.com/"),
        ("Toptal",                   0.00, "mo", "Free to apply (invite-based)",            "https://www.toptal.com/"),
        ("Contra Pro",               0.00, "mo", "0% commission, free",                    "https://contra.com/"),
    ],
    "☁️ Cloud & Hosting": [
        ("AWS Free Tier",            0.00, "mo", "Free 12-month starter limits",            "https://aws.amazon.com/free/"),
        ("DigitalOcean Droplet",     4.00, "mo", "1 vCPU, 1GB RAM, 25GB SSD",              "https://www.digitalocean.com/pricing/"),
        ("Hetzner CX11",             3.29, "mo", "2 vCPU, 2GB RAM (EU)",                   "https://www.hetzner.com/cloud"),
        ("Namecheap .com domain",    8.88, "yr", "Domain registration/renewal",             "https://www.namecheap.com/"),
        ("Cloudflare R2",            0.00, "mo", "15GB free object storage",                "https://www.cloudflare.com/developer-platform/r2/"),
        ("Resend",                   0.00, "mo", "3000 emails/mo free tier",               "https://resend.com/pricing"),
    ],
    "🔐 VPN & Security": [
        ("NordVPN Standard",         4.49, "mo", "6 devices, ad blocker",                  "https://nordvpn.com/pricing/"),
        ("ExpressVPN",              12.95, "mo", "8 devices, fast servers",                "https://www.expressvpn.com/order"),
        ("ProtonVPN Plus",           7.99, "mo", "Privacy-focused, Swiss",                 "https://protonvpn.com/pricing"),
        ("Surfshark One",            3.19, "mo", "Unlimited devices",                      "https://surfshark.com/pricing"),
        ("Malwarebytes Premium",     3.75, "mo", "Real-time protection",                   "https://www.malwarebytes.com/pricing"),
    ],
}

# Hardware — format: (Name, USD_price, description, search_query_for_amazon)
HARDWARE = {
    "💻 Laptops": [
        ("MacBook Pro 14\" M4",       1_999, "Best-in-class for dev/design",                "MacBook+Pro+14+M4"),
        ("MacBook Air 13\" M3",       1_099, "Lightweight, fanless, great battery",          "MacBook+Air+13+M3"),
        ("MacBook Air 15\" M3",       1_299, "Larger screen, same M3 chip",                  "MacBook+Air+15+M3"),
        ("Dell XPS 15 (2024)",        1_499, "Windows powerhouse for devs",                  "Dell+XPS+15+2024"),
        ("Lenovo ThinkPad X1 Carbon", 1_200, "Business ultrabook, great keyboard",            "ThinkPad+X1+Carbon"),
        ("ASUS Zenbook 14 OLED",        699, "Budget OLED screen, Windows 11",               "ASUS+Zenbook+14+OLED"),
        ("Acer Swift 3 (Ryzen 7)",      649, "Affordable all-rounder",                       "Acer+Swift+3+Ryzen+7"),
    ],
    "🖥️ Monitors": [
        ("LG UltraWide 34\" QHD",     449, "Curved ultrawide, great for code",              "LG+UltraWide+34+QHD"),
        ("Dell U2723D 27\" 4K",       499, "IPS 4K, USB-C 90W charging",                    "Dell+U2723D"),
        ("LG 27UK850 27\" 4K",        399, "4K IPS, USB-C, HDR10",                          "LG+27UK850"),
        ("ASUS ProArt 27\" 4K",       549, "Factory calibrated, creators",                  "ASUS+ProArt+27+4K"),
        ("BenQ GW2780 27\" FHD",      199, "Budget 1080p IPS, easy on eyes",                "BenQ+GW2780"),
        ("Samsung Odyssey G5 27\"",   299, "1440p 165Hz gaming/dev dual use",               "Samsung+Odyssey+G5+27"),
    ],
    "⌨️ Keyboards & Mice": [
        ("Logitech MX Keys S",        109, "Wireless, backlit, cross-device",               "Logitech+MX+Keys+S"),
        ("Keychron K2 Pro",            89, "Mechanical, hot-swap, wireless",                "Keychron+K2+Pro"),
        ("Logitech MX Master 3S",      99, "Best ergonomic mouse for devs",                 "Logitech+MX+Master+3S"),
        ("Magic Keyboard (USB-C)",    129, "Mac-native, slim, quiet",                       "Apple+Magic+Keyboard+USB-C"),
        ("Keychron Q1 Pro",           199, "Premium gasket mount mechanical",               "Keychron+Q1+Pro"),
        ("Razer DeathAdder V3",        59, "Lightweight wired mouse",                       "Razer+DeathAdder+V3"),
    ],
    "🎧 Audio & Mic": [
        ("Sony WH-1000XM5",          349, "Best ANC headphones",                            "Sony+WH-1000XM5"),
        ("Apple AirPods Pro 2",      249, "Best for Mac/iPhone users",                      "AirPods+Pro+2"),
        ("Jabra Evolve2 55",         449, "Business headset, Teams certified",              "Jabra+Evolve2+55"),
        ("Blue Yeti USB Mic",        129, "Popular podcast/call mic",                       "Blue+Yeti+USB+Mic"),
        ("Rode NT-USB Mini",          99, "Compact studio USB mic",                         "Rode+NT-USB+Mini"),
        ("Elgato Wave 3",            149, "Streaming/recording mic",                        "Elgato+Wave+3"),
    ],
    "📱 Mobile & Tablets": [
        ("iPhone 16 Pro",            999, "Best iPhone, 48MP camera",                       "iPhone+16+Pro"),
        ("iPhone 15",                799, "Last year flagship, solid value",                "iPhone+15"),
        ("Samsung Galaxy S25",       799, "Best Android flagship 2025",                     "Samsung+Galaxy+S25"),
        ("iPad Pro 13\" M4",       1_099, "Best tablet for designers",                      "iPad+Pro+13+M4"),
        ("iPad Air 13\"",            799, "Value pick for creative work",                   "iPad+Air+13"),
        ("Samsung Galaxy Tab S9",    799, "Android tablet for productivity",                "Samsung+Galaxy+Tab+S9"),
    ],
    "🔌 Accessories": [
        ("CalDigit TS4 Thunderbolt Dock", 249, "Best dock for MacBook — 18 ports",          "CalDigit+TS4+Thunderbolt"),
        ("Anker 727 Thunderbolt Dock",    199, "12-in-1 Thunderbolt 4 hub",                 "Anker+727+Thunderbolt"),
        ("Elgato Stream Deck MK.2",       149, "Macro shortcuts, streaming",                "Elgato+Stream+Deck"),
        ("Logitech C920x HD Webcam",       69, "1080p/30fps, clear video calls",            "Logitech+C920x"),
        ("APC Back-UPS 1500VA",           160, "UPS — essential for Pakistan",              "APC+Back-UPS+1500VA"),
        ("Xiaomi 67W GaN Charger",         25, "Compact fast charger",                      "Xiaomi+67W+GaN+Charger"),
        ("SanDisk 1TB Portable SSD",       90, "Fast portable backup drive",               "SanDisk+1TB+Portable+SSD"),
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
# TAB 1 — SOFTWARE (with search + Visit Site links)
# ─────────────────────────────────────────────────────────────────────────
with tab_sw:
    # ── Search bar + free toggle ──────────────────────────────────────────
    sc1, sc2 = st.columns([4, 1])
    with sc1:
        sw_search = st.text_input(
            "Search software",
            placeholder="🔍  e.g. GitHub, Adobe, Figma, VPN, AI…",
            label_visibility="collapsed",
        )
    with sc2:
        show_free = st.toggle("Free only", value=False)

    search_lower = sw_search.strip().lower()

    # ── Build flat list for chart + budget calculator ─────────────────────
    all_sw_rows = []
    for category, items in SOFTWARE.items():
        for name, price_usd, period, desc, url in items:
            if show_free and price_usd > 0:
                continue
            if search_lower and search_lower not in name.lower() \
                             and search_lower not in desc.lower() \
                             and search_lower not in category.lower():
                continue
            all_sw_rows.append({
                "category": category,
                "name":     name,
                "price":    price_usd,
                "period":   period,
                "desc":     desc,
                "url":      url,
                "usd_mo":   price_usd if period == "mo" else round(price_usd / 12, 2),
                "pkr_mo":   to_pkr(price_usd) if period == "mo" else to_pkr(price_usd / 12),
                "pkr_yr":   to_pkr(price_usd * 12) if period == "mo" else to_pkr(price_usd),
            })

    if not all_sw_rows:
        st.info("No software tools match your search. Try a different keyword.")
    else:
        # Render grouped by category
        active_cats = []
        for cat in SOFTWARE:
            cat_items = [r for r in all_sw_rows if r["category"] == cat]
            if cat_items:
                active_cats.append((cat, cat_items))

        for cat, items in active_cats:
            st.markdown(f"#### {cat}")
            for item in items:
                col_name, col_price, col_pkr, col_link = st.columns([3, 1.2, 1.5, 1])
                with col_name:
                    st.markdown(
                        f"**{item['name']}**  \n"
                        f"<span style='font-size:12px;color:#5a7263'>{item['desc']}</span>",
                        unsafe_allow_html=True,
                    )
                with col_price:
                    if item["price"] == 0:
                        st.markdown("🟢 **Free**")
                    else:
                        period_label = "/mo" if item["period"] == "mo" else "/yr"
                        st.markdown(f"**${item['price']:.2f}**{period_label}")
                with col_pkr:
                    if item["price"] == 0:
                        st.markdown("Free")
                    else:
                        st.markdown(f"₨ {item['pkr_mo']:,}/mo")
                        st.caption(f"₨ {item['pkr_yr']:,}/yr")
                with col_link:
                    st.link_button("Visit ↗", item["url"], use_container_width=True)
            st.markdown("<hr style='margin:6px 0;border-color:#f0f0f0'>", unsafe_allow_html=True)

        st.divider()

        # ── Top 10 most expensive chart ───────────────────────────────────
        paid_rows = [r for r in all_sw_rows if r["price"] > 0]
        if paid_rows:
            top10_df = pd.DataFrame(paid_rows).nlargest(10, "usd_mo")
            st.subheader("Top 10 most expensive subscriptions (monthly USD)")
            fig_sw = px.bar(
                top10_df.sort_values("usd_mo"),
                x="usd_mo", y="name", orientation="h",
                color="usd_mo",
                color_continuous_scale=[[0,"#e8f5ee"],[1,"#01411C"]],
                text=top10_df.sort_values("usd_mo")["pkr_mo"].apply(lambda x: f"₨ {x:,}"),
                labels={"usd_mo":"USD / month","name":""},
            )
            fig_sw.update_traces(textposition="outside")
            fig_sw.update_layout(
                paper_bgcolor="white", plot_bgcolor="white",
                margin=dict(l=0,r=0,t=10,b=0),
                coloraxis_showscale=False,
                xaxis=dict(title="USD / month",gridcolor="#f0f0f0"),
                yaxis=dict(showgrid=False),
                height=380,
            )
            st.plotly_chart(fig_sw, use_container_width=True)

        # ── Budget calculator ─────────────────────────────────────────────
        st.divider()
        st.subheader("Budget Calculator")
        st.caption("Pick the tools you use and see your total monthly software cost in PKR.")

        paid_names = [(r["name"], r["usd_mo"]) for r in all_sw_rows if r["price"] > 0]
        selected_tools = st.multiselect(
            "My subscriptions",
            options=[n for n, _ in paid_names],
            default=[],
        )
        if selected_tools:
            price_map = {n: p for n, p in paid_names}
            total_usd = sum(price_map.get(t, 0) for t in selected_tools)
            total_pkr = to_pkr(total_usd)
            bc1, bc2, bc3 = st.columns(3)
            bc1.metric("Monthly USD", f"${total_usd:,.2f}")
            bc2.metric("Monthly PKR", f"₨ {total_pkr:,}")
            bc3.metric("Annual PKR",  f"₨ {total_pkr*12:,}")


# ─────────────────────────────────────────────────────────────────────────
# TAB 2 — HARDWARE (with search + Amazon search links)
# ─────────────────────────────────────────────────────────────────────────
with tab_hw:
    hw_search = st.text_input(
        "Search hardware", placeholder="🔍  e.g. MacBook, monitor, mic, UPS…",
        label_visibility="collapsed", key="hw_search"
    )
    hw_lower = hw_search.strip().lower()

    all_hw_rows = []
    for category, items in HARDWARE.items():
        for name, price_usd, desc, query in items:
            if hw_lower and hw_lower not in name.lower() \
                        and hw_lower not in desc.lower() \
                        and hw_lower not in category.lower():
                continue
            all_hw_rows.append({
                "Category": category,
                "name":     name,
                "usd":      price_usd,
                "pkr":      to_pkr(price_usd),
                "desc":     desc,
                "query":    query,
            })

    if not all_hw_rows:
        st.info("No hardware matches your search.")
    else:
        hw_df = pd.DataFrame(all_hw_rows)

        for cat in hw_df["Category"].unique():
            cat_df = hw_df[hw_df["Category"] == cat]
            st.markdown(f"#### {cat}")
            for _, row in cat_df.iterrows():
                h1, h2, h3, h4 = st.columns([3, 1, 1.5, 1])
                with h1:
                    st.markdown(
                        f"**{row['name']}**  \n"
                        f"<span style='font-size:12px;color:#5a7263'>{row['desc']}</span>",
                        unsafe_allow_html=True,
                    )
                with h2:
                    st.markdown(f"**${row['usd']:,}**")
                with h3:
                    st.markdown(f"₨ {row['pkr']:,}")
                with h4:
                    amazon_url = f"https://www.amazon.com/s?k={row['query']}"
                    st.link_button("Find ↗", amazon_url, use_container_width=True)
            st.markdown("<hr style='margin:6px 0;border-color:#f0f0f0'>", unsafe_allow_html=True)

        st.divider()

        # All hardware scatter
        st.subheader("Hardware price overview")
        fig_hw = px.scatter(
            hw_df, x="usd", y="Category",
            size="usd", color="Category",
            hover_name="name",
            hover_data={"pkr": True, "usd": False, "Category": False},
            labels={"usd":"USD price","Category":""},
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

        st.info(
            "🇵🇰 **Pakistan-specific tip** — A quality UPS (Uninterruptible Power Supply) "
            "is arguably the most important hardware purchase for a Pakistani freelancer. "
            "Load-shedding can corrupt work, disconnect from clients mid-call, and "
            "damage hardware. Budget ₨ 45,000–60,000 for a decent 1500VA unit. "
            "It's a business expense and tax-deductible."
        )

        # Single item converter
        st.divider()
        st.subheader("Single Item Converter")
        sc1, sc2 = st.columns(2)
        with sc1:
            item_usd = st.number_input("Item price (USD)", value=999.0, step=10.0)
        with sc2:
            st.metric("Price in PKR", f"₨ {to_pkr(item_usd):,}")
            st.caption(f"At ₨ {USD_PKR:,.1f} / USD")


# ─────────────────────────────────────────────────────────────────────────
# TAB 3 — AI PRICE SEARCH (STRATOS)
# ─────────────────────────────────────────────────────────────────────────
with tab_search:
    st.subheader("🧠 AI Price Search — Ask STRATOS")
    st.caption(
        "Ask about any software or hardware price, Pakistani availability, "
        "alternatives, or buying advice. Powered by Groq."
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
        if col.button(chip, use_container_width=True, key=f"chip_{chip[:12]}"):
            st.session_state.price_search_history.append({"role":"user","content":chip})

    user_q = st.chat_input("e.g. How much does Figma cost in PKR? Any cheaper alternatives?")
    if user_q:
        st.session_state.price_search_history.append({"role":"user","content":user_q})

    for msg in st.session_state.price_search_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

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

                    # Build software/hardware context summary for STRATOS
                    sw_summary = []
                    for cat, items in SOFTWARE.items():
                        for name, price, period, desc, url in items:
                            sw_summary.append(f"{name}: ${price}/{period} (₨ {to_pkr(price):,}/{'mo' if period=='mo' else 'yr'}) — {desc}")
                    hw_summary = []
                    for cat, items in HARDWARE.items():
                        for name, price, desc, _ in items:
                            hw_summary.append(f"{name}: ${price:,} (₨ {to_pkr(price):,}) — {desc}")

                    system = f"""You are STRATOS, the AI engine of IDMI — a Pakistani freelancer intelligence platform.

Current live data:
- USD/PKR rate: {USD_PKR:.2f}

KNOWN SOFTWARE PRICES (use these for accurate PKR conversion):
{chr(10).join(sw_summary[:40])}

KNOWN HARDWARE PRICES:
{chr(10).join(hw_summary[:30])}

When answering:
1. Check the known prices above first and use those USD values
2. Convert to PKR using the live rate ₨ {USD_PKR:.0f}/USD
3. Note if the product is available in Pakistan via official channels
4. Suggest 1–2 free or cheaper alternatives when relevant
5. Be specific and practical. No fluff.
6. For hardware, mention whether it's available at Hafeez Centre, Liberty Market, or import-only.
7. Always include the official website link if you know it."""

                    messages_api = [{"role":"system","content":system}] + \
                                   st.session_state.price_search_history

                    full_resp = ""
                    stream = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages_api,
                        temperature=0.3,
                        max_tokens=700,
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
        f"Software and hardware prices are maintained manually and converted using the live USD/PKR rate "
        f"(₨ {USD_PKR:,.1f}) from your IDMI pipeline. AI search uses Groq Llama 3.3 70B."
    )
