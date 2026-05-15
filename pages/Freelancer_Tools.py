"""
pages/Freelancer_Tools.py — Multi-currency income calculator for Pakistani freelancers.

Supports: USD, EUR, GBP, CAD, AUD, SAR, AED, USDT
Deductions: platform fees + FBR 2024-25 tax brackets
Extras: purchasing power history, savings planner, currency comparison table
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.db import load_data, get_latest
from utils.theme import inject_css

st.set_page_config(page_title="Freelancer Tools | IDMI", page_icon="💰", layout="wide")
inject_css()

st.title("Freelancer Tools")
st.caption("Multi-currency income calculator — see your real PKR take-home after platform fees and FBR tax.")

df   = load_data()
latest = get_latest(df)

# ── Live rates from DB (fallback to sensible defaults if DB empty) ─────────
LIVE_RATES = {
    "USD": float(latest.get("usd_pkr_rate") or 280.0),
    "EUR": float(latest.get("eur_pkr_rate") or 305.0),
    "GBP": float(latest.get("gbp_pkr_rate") or 357.0),
    "SAR": float(latest.get("sar_pkr_rate") or 74.6),
    "AED": float(latest.get("aed_pkr_rate") or 76.2),
    "USDT": float(latest.get("usdt_pkr_rate") or 280.0),
    # CAD and AUD not in harvester — derive from USD rate with typical cross rates
    "CAD": round(float(latest.get("usd_pkr_rate") or 280.0) * 0.735, 2),
    "AUD": round(float(latest.get("usd_pkr_rate") or 280.0) * 0.652, 2),
}

CURRENCY_SYMBOLS = {
    "USD":"$", "EUR":"€", "GBP":"£", "CAD":"CA$",
    "AUD":"A$", "SAR":"﷼", "AED":"د.إ", "USDT":"₮",
}

# ── Platform fee logic ─────────────────────────────────────────────────────
PLATFORMS = {
    "Upwork (tiered)":    None,
    "Fiverr (20% flat)":  0.20,
    "Freelancer.com":     0.10,
    "PeoplePerHour":      0.20,
    "Direct / PayPal":    0.029,
    "Toptal":             0.00,
    "Contra (0%)":        0.00,
    "Guru":               0.089,
}

def upwork_fee(amount):
    """Upwork tiered: 20% → first 500, 10% → up to 10k, 5% → above."""
    if amount <= 500:        return amount * 0.20
    elif amount <= 10_000:   return 100 + (amount - 500)  * 0.10
    else:                    return 100 + 950 + (amount - 10_000) * 0.05

def calc_platform_fee(platform, amount):
    if platform == "Upwork (tiered)": return upwork_fee(amount)
    return amount * PLATFORMS[platform]

# ── FBR 2024-25 non-salaried / freelance brackets ─────────────────────────
def fbr_annual_tax(annual_pkr, registered=True):
    if annual_pkr <= 600_000:    tax = 0
    elif annual_pkr <= 1_200_000: tax = (annual_pkr - 600_000)   * 0.15
    elif annual_pkr <= 1_600_000: tax = 90_000  + (annual_pkr - 1_200_000) * 0.20
    elif annual_pkr <= 3_200_000: tax = 170_000 + (annual_pkr - 1_600_000) * 0.30
    elif annual_pkr <= 5_600_000: tax = 650_000 + (annual_pkr - 3_200_000) * 0.40
    else:                         tax = 1_610_000 + (annual_pkr - 5_600_000) * 0.45
    return tax * (1.0 if registered else 2.0)

# ══════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════
tab_calc, tab_compare, tab_history, tab_tips = st.tabs([
    "💰 Income Calculator",
    "📊 Currency Comparison",
    "📈 Purchasing Power History",
    "💡 Money Tips",
])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1 — INCOME CALCULATOR
# ─────────────────────────────────────────────────────────────────────────
with tab_calc:
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.subheader("Your Earnings")

        earn_currency = st.selectbox(
            "Earning currency",
            list(LIVE_RATES.keys()),
            index=0,
            help="The currency your client pays you in.",
        )
        sym = CURRENCY_SYMBOLS[earn_currency]
        live_pkr_rate = LIVE_RATES[earn_currency]

        monthly_gross = st.number_input(
            f"Monthly earnings ({earn_currency})",
            min_value=0.0, value=1000.0, step=50.0,
            help=f"Your gross income before any fees — in {earn_currency}.",
        )

        platform = st.selectbox("Platform / payment method", list(PLATFORMS.keys()))

        st.markdown("**Exchange rate**")
        use_custom_rate = st.toggle("Override live rate", value=False)
        if use_custom_rate:
            pkr_rate = st.number_input(
                f"Custom {earn_currency}/PKR rate",
                value=live_pkr_rate, step=0.5,
            )
        else:
            pkr_rate = live_pkr_rate
            st.caption(f"Live rate: **₨ {pkr_rate:,.2f}** per {earn_currency}")

        tax_registered = st.toggle("FBR registered (NTN holder)", value=True)
        st.caption("Unregistered filers pay 2× rate on most income types.")

        st.divider()
        st.subheader("Savings Goal")
        savings_pct = st.slider("Save this % of net income", 0, 50, 20)

    # ── Maths ────────────────────────────────────────────────────────────
    fee_fc        = calc_platform_fee(platform, monthly_gross)
    after_fee_fc  = monthly_gross - fee_fc
    after_fee_pkr = after_fee_fc * pkr_rate
    annual_pkr    = after_fee_pkr * 12

    annual_tax    = fbr_annual_tax(annual_pkr, tax_registered)
    monthly_tax   = annual_tax / 12

    net_monthly   = after_fee_pkr - monthly_tax
    savings_amt   = net_monthly * (savings_pct / 100)
    spendable     = net_monthly - savings_amt

    fee_pct = (fee_fc / monthly_gross * 100) if monthly_gross else 0
    eff_tax = (monthly_tax / after_fee_pkr * 100) if after_fee_pkr else 0

    with col_out:
        st.subheader("Take-Home Breakdown")

        st.markdown(f"""
        <div class="calc-card">
          <div class="label">Monthly Net Take-Home</div>
          <div class="amount">₨ {net_monthly:,.0f}</div>
          <div class="label" style="margin-top:6px">
            {sym} {after_fee_fc:,.0f} {earn_currency} after platform fee
            &nbsp;·&nbsp; ≈ USD {net_monthly / LIVE_RATES['USD']:,.0f}
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        m1, m2 = st.columns(2)
        m1.metric(f"Gross ({earn_currency})", f"{sym}{monthly_gross:,.0f}")
        m2.metric("Platform fee", f"−{sym}{fee_fc:,.1f}",
                  f"{fee_pct:.1f}% of gross", delta_color="inverse")

        m3, m4 = st.columns(2)
        m3.metric("After-fee in PKR", f"₨ {after_fee_pkr:,.0f}")
        m4.metric("Monthly FBR tax",  f"−₨ {monthly_tax:,.0f}",
                  f"{eff_tax:.1f}% effective", delta_color="inverse")

        m5, m6 = st.columns(2)
        m5.metric(f"Savings ({savings_pct}%)", f"₨ {savings_amt:,.0f}")
        m6.metric("Spendable",                 f"₨ {spendable:,.0f}")

        st.divider()
        st.subheader("Annual Projection")
        a1, a2, a3 = st.columns(3)
        a1.metric(f"Annual gross ({earn_currency})", f"{sym}{monthly_gross*12:,.0f}")
        a2.metric("Annual FBR tax",                   f"₨ {annual_tax:,.0f}")
        a3.metric("Annual net PKR",                   f"₨ {net_monthly*12:,.0f}")

        # Waterfall chart
        fig_wf = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative","relative","relative","total"],
            x=["Gross (PKR)","Platform fee","FBR tax","Net take-home"],
            y=[
                monthly_gross * pkr_rate,
                -(fee_fc * pkr_rate),
                -monthly_tax,
                0,
            ],
            connector={"line":{"color":"#e2e8e4"}},
            decreasing={"marker":{"color":"#ef4444"}},
            increasing={"marker":{"color":"#1a7a3c"}},
            totals={"marker":{"color":"#C9A84C"}},
            text=[
                f"₨{monthly_gross*pkr_rate:,.0f}",
                f"−₨{fee_fc*pkr_rate:,.0f}",
                f"−₨{monthly_tax:,.0f}",
                f"₨{net_monthly:,.0f}",
            ],
            textposition="outside",
        ))
        fig_wf.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0,r=0,t=20,b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(title="PKR",gridcolor="#f0f0f0"),
            showlegend=False, height=260,
        )
        st.plotly_chart(fig_wf, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────
# TAB 2 — CURRENCY COMPARISON
# ─────────────────────────────────────────────────────────────────────────
with tab_compare:
    st.subheader("What does the same income look like in every currency?")
    st.caption("Enter a monthly amount in each currency and compare PKR take-home side by side.")

    ref_amount = st.number_input(
        "Monthly earnings amount (same number, different currency)",
        min_value=0.0, value=1000.0, step=50.0,
    )
    cmp_platform = st.selectbox("Platform", list(PLATFORMS.keys()), key="cmp_plat")
    cmp_registered = st.toggle("FBR registered", value=True, key="cmp_reg")

    rows = []
    for ccy, rate in LIVE_RATES.items():
        fee_a    = calc_platform_fee(cmp_platform, ref_amount)
        after_fee = ref_amount - fee_a
        pkr_gross = after_fee * rate
        ann_pkr   = pkr_gross * 12
        tax       = fbr_annual_tax(ann_pkr, cmp_registered) / 12
        net_pkr   = pkr_gross - tax
        rows.append({
            "Currency": ccy,
            "Rate (PKR)": f"₨ {rate:,.2f}",
            f"Gross {ccy}": f"{CURRENCY_SYMBOLS[ccy]}{ref_amount:,.0f}",
            "Platform fee": f"{CURRENCY_SYMBOLS[ccy]}{fee_a:,.1f}",
            "After-fee PKR": f"₨ {pkr_gross:,.0f}",
            "FBR tax/mo": f"₨ {tax:,.0f}",
            "Net PKR / mo": f"₨ {net_pkr:,.0f}",
            "_net": net_pkr,
        })

    cmp_df = pd.DataFrame(rows).sort_values("_net", ascending=False)

    st.dataframe(
        cmp_df.drop(columns=["_net"]),
        use_container_width=True,
        hide_index=True,
    )

    # Bar chart of net PKR per currency
    fig_cmp = go.Figure(go.Bar(
        x=[r["Currency"] for r in rows],
        y=[r["_net"] for r in rows],
        marker_color=["#1a7a3c" if r["Currency"]=="USD" else "#C9A84C" if r["Currency"]=="USDT"
                      else "#2563eb" for r in rows],
        text=[f"₨{r['_net']:,.0f}" for r in rows],
        textposition="outside",
    ))
    fig_cmp.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0,r=0,t=20,b=0),
        xaxis=dict(title="Currency",showgrid=False),
        yaxis=dict(title="Net PKR / month",gridcolor="#f0f0f0"),
        showlegend=False,
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    st.info(
        "💡 **Insight** — Even though GBP/PKR rate is highest, USD is still the most "
        "liquid currency for freelancers because most global platforms pay in USD. "
        "SAR and AED are relevant for remittances from Saudi Arabia and UAE."
    )


# ─────────────────────────────────────────────────────────────────────────
# TAB 3 — PURCHASING POWER HISTORY
# ─────────────────────────────────────────────────────────────────────────
with tab_history:
    st.subheader("Purchasing Power Over Time")
    st.caption(
        "How much PKR your earnings would have yielded historically — "
        "a stark visualisation of PKR devaluation."
    )

    hist_ccy   = st.selectbox("Currency", list(LIVE_RATES.keys()), key="hist_ccy")
    hist_amount = st.number_input(
        f"Monthly earnings ({hist_ccy})", value=1000.0, step=50.0, key="hist_amt"
    )

    # Historical USD/PKR rates; for other currencies scale by typical cross-rate
    USD_HISTORY = {
        "2018":134, "2019":154, "2020":160, "2021":176,
        "2022":220, "2023":285, "2024":278, "Now": LIVE_RATES["USD"],
    }
    # Approximate multipliers to USD for other currencies (rough historical cross)
    CCY_MULT = {
        "USD":1.00, "EUR":1.12, "GBP":1.28, "CAD":0.75,
        "AUD":0.69, "SAR":0.267,"AED":0.272,"USDT":1.00,
    }
    mult = CCY_MULT.get(hist_ccy, 1.0)

    years   = list(USD_HISTORY.keys())
    pkr_vals = [hist_amount * mult * r for r in USD_HISTORY.values()]

    colors = ["#d1d5db"] * (len(years) - 1) + ["#1a7a3c"]
    fig_h = go.Figure(go.Bar(
        x=years, y=pkr_vals,
        marker_color=colors,
        text=[f"₨{v/1000:.0f}k" for v in pkr_vals],
        textposition="outside",
    ))
    fig_h.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(l=0,r=0,t=30,b=0),
        xaxis=dict(title="", showgrid=False),
        yaxis=dict(title="Monthly PKR", gridcolor="#f0f0f0"),
        showlegend=False,
    )
    st.plotly_chart(fig_h, use_container_width=True)

    pwr_2018 = pkr_vals[0]
    pwr_now  = pkr_vals[-1]
    pct_chg  = (pwr_now - pwr_2018) / pwr_2018 * 100
    st.metric(
        f"PKR received for {CURRENCY_SYMBOLS[hist_ccy]}{hist_amount:,.0f}/mo",
        f"₨ {pwr_now:,.0f} today",
        f"{pct_chg:+.1f}% vs 2018",
    )
    st.caption(
        "Note: Historical cross-rates are approximate averages. "
        "'Now' uses the live rate from your IDMI pipeline."
    )

    # Also show live DB trend if available
    if not df.empty and "usd_pkr_rate" in df.columns:
        st.divider()
        st.markdown("**Live pipeline data — USD/PKR snapshots**")
        fig_live = px.line(
            df.dropna(subset=["usd_pkr_rate"]),
            x="timestamp", y="usd_pkr_rate",
            line_shape="spline",
            color_discrete_sequence=["#01411C"],
            labels={"usd_pkr_rate":"PKR per USD","timestamp":""},
        )
        fig_live.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="#f0f0f0"),
        )
        st.plotly_chart(fig_live, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────
# TAB 4 — MONEY TIPS
# ─────────────────────────────────────────────────────────────────────────
with tab_tips:
    st.subheader("Smart Money Moves for Pakistani Freelancers")

    tips = [
        ("🏦","Hold USD strategically",
         "If PKR is weakening (rate rising), delay conversion. Keep 1-2 months "
         "of earnings in USD before cashing out. Use Payoneer or Wise to hold "
         "multiple currencies without immediate conversion."),
        ("📋","Get your NTN (Free)",
         "Register on FBR's IRIS portal — it's free and takes 30 minutes. "
         "Unregistered filers pay double tax on many income types. With NTN you "
         "also unlock lower withholding tax rates from clients and platforms."),
        ("₮","Use USDT as a buffer",
         "Many Pakistani freelancers convert USD → USDT via a local exchange "
         "instead of PKR. USDT tracks USD 1:1 so you avoid PKR devaluation risk "
         "while staying liquid. Cash out to PKR only when needed."),
        ("💸","Diversify your invoice currencies",
         "Saudi and UAE clients often pay in SAR/AED. These convert to PKR at "
         "favourable rates and Middle East remittances have lower banking friction "
         "for Pakistani accounts than US transfers."),
        ("🏦","Open a freelancer-friendly bank account",
         "JS Bank, HBL and Meezan offer dedicated freelancer accounts with lower "
         "forex conversion fees and faster USD clearing. Avoid using a regular "
         "savings account for international payments — fees are higher."),
        ("📊","Track your effective tax rate",
         "FBR tax is on annual income, not monthly. If you earn more than ₨1.6M/year "
         "(≈ $5,700 USD at current rates), you enter the 30% bracket. "
         "Consider splitting income across two tax years when a project is large."),
        ("🔄","Use Wise for lower conversion fees",
         "Wise (formerly TransferWise) often offers better USD→PKR mid-market rates "
         "than traditional banks and charges 0.4-1% fees vs 2-4% at banks. "
         "Compare rates before every conversion."),
        ("💼","Invoice in USD, pay expenses in PKR",
         "If you have recurring USD earnings, invoice upfront so you lock in "
         "the rate. Pay your local PKR expenses (rent, utilities) from PKR "
         "converted only when needed — this minimises exchange risk."),
    ]

    col_a, col_b = st.columns(2, gap="large")
    for i, (icon, title, body) in enumerate(tips):
        col = col_a if i % 2 == 0 else col_b
        with col:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8e4;border-radius:10px;
                        padding:16px;margin-bottom:14px;">
              <div style="font-size:22px;margin-bottom:6px">{icon}</div>
              <div style="font-weight:700;font-size:14px;color:#01411C;margin-bottom:6px">{title}</div>
              <div style="font-size:13px;color:#374151;line-height:1.6">{body}</div>
            </div>""", unsafe_allow_html=True)
