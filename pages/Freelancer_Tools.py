"""
pages/2_💰_Freelancer_Tools.py — Income calculator for Pakistani freelancers.

Calculates net PKR take-home from USD earnings after:
  - Platform fees (Upwork tiered, Fiverr, Freelancer.com, Direct)
  - FBR income tax (Pakistan 2024-25 brackets for salaried/business individuals)
  - Purchasing power comparison vs 2020 baseline
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from utils.db import load_data, get_latest
from utils.theme import inject_css

st.set_page_config(page_title="Freelancer Tools | IDMI", page_icon="💰", layout="wide")
inject_css()

st.title("Freelancer Tools")
st.caption("Calculate your real take-home in PKR after platform fees and Pakistani taxes.")

df = load_data()
latest = get_latest(df)
live_rate = latest.get("usd_pkr_rate", 280.0)

# ── Platform fee structures ────────────────────────────────────────────────
PLATFORMS = {
    "Upwork (tiered)":   None,        # handled separately
    "Fiverr (20% flat)": 0.20,
    "Freelancer.com":    0.10,
    "PeoplePerHour":     0.20,
    "Direct / PayPal":   0.02,        # PayPal ~2% receiving fee
    "Toptal":            0.00,
}

def upwork_fee(usd):
    """Upwork tiered: 20% on first $500, 10% up to $10k, 5% above."""
    if usd <= 500:
        return usd * 0.20
    elif usd <= 10_000:
        return 500 * 0.20 + (usd - 500) * 0.10
    else:
        return 500 * 0.20 + 9_500 * 0.10 + (usd - 10_000) * 0.05

def platform_fee(platform, usd):
    if platform == "Upwork (tiered)":
        return upwork_fee(usd)
    return usd * PLATFORMS[platform]

# ── FBR tax 2024-25 (business/freelance income) ────────────────────────────
def fbr_tax(annual_pkr):
    """
    Pakistan FBR tax for non-salaried / business income (freelancers).
    2024-25 brackets.
    """
    if annual_pkr <= 600_000:
        return 0
    elif annual_pkr <= 1_200_000:
        return (annual_pkr - 600_000) * 0.15
    elif annual_pkr <= 1_600_000:
        return 90_000 + (annual_pkr - 1_200_000) * 0.20
    elif annual_pkr <= 3_200_000:
        return 170_000 + (annual_pkr - 1_600_000) * 0.30
    elif annual_pkr <= 5_600_000:
        return 650_000 + (annual_pkr - 3_200_000) * 0.40
    else:
        return 1_610_000 + (annual_pkr - 5_600_000) * 0.45

# ── UI ─────────────────────────────────────────────────────────────────────
col_in, col_out = st.columns([1, 1], gap="large")

with col_in:
    st.subheader("Your Earnings")

    monthly_usd = st.number_input(
        "Monthly earnings (USD)", min_value=0.0, value=1000.0, step=50.0,
        help="Your gross USD income before any fees."
    )
    platform = st.selectbox("Platform", list(PLATFORMS.keys()))

    custom_rate = st.toggle("Override exchange rate", value=False)
    if custom_rate:
        rate = st.number_input("Custom USD/PKR rate", value=float(live_rate), step=0.5)
    else:
        rate = float(live_rate)
        st.caption(f"Using live rate: **₨ {rate}** per USD")

    tax_registered = st.toggle("I am FBR tax registered (NTN holder)", value=True)
    st.caption("Unregistered filers pay 2× standard rate on some income types.")

    st.divider()
    st.subheader("Savings Goal")
    savings_pct = st.slider("Save this % of net income", 0, 50, 20)

# ── Calculations ──────────────────────────────────────────────────────────
fee_usd       = platform_fee(platform, monthly_usd)
after_fee_usd = monthly_usd - fee_usd
after_fee_pkr = after_fee_usd * rate
annual_pkr    = after_fee_pkr * 12

annual_tax    = fbr_tax(annual_pkr)
monthly_tax   = annual_tax / 12
multiplier    = 2.0 if not tax_registered else 1.0
monthly_tax  *= multiplier

net_monthly_pkr  = after_fee_pkr - monthly_tax
savings_monthly  = net_monthly_pkr * (savings_pct / 100)
spendable        = net_monthly_pkr - savings_monthly

# ── Output ────────────────────────────────────────────────────────────────
with col_out:
    st.subheader("Take-Home Breakdown")

    st.markdown(f"""
    <div class="calc-card">
      <div class="label">Monthly Net Take-Home</div>
      <div class="amount">₨ {net_monthly_pkr:,.0f}</div>
      <div class="label">≈ USD {net_monthly_pkr / rate:,.0f} equivalent</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("&nbsp;", unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    m1.metric("Gross USD", f"${monthly_usd:,.0f}")
    m2.metric(f"Platform fee ({platform.split('(')[0].strip()})",
              f"−${fee_usd:,.0f}", f"{fee_usd/monthly_usd*100:.1f}%" if monthly_usd else None,
              delta_color="inverse")

    m3, m4 = st.columns(2)
    m3.metric("After-fee in PKR", f"₨ {after_fee_pkr:,.0f}")
    m4.metric("Monthly FBR tax", f"−₨ {monthly_tax:,.0f}",
              delta_color="inverse")

    m5, m6 = st.columns(2)
    m5.metric(f"Savings ({savings_pct}%)", f"₨ {savings_monthly:,.0f}")
    m6.metric("Spendable", f"₨ {spendable:,.0f}")

    st.divider()

    # Annual summary
    st.subheader("Annual Projection")
    a1, a2, a3 = st.columns(3)
    a1.metric("Annual gross USD",  f"${monthly_usd * 12:,.0f}")
    a2.metric("Annual FBR tax",    f"₨ {annual_tax * multiplier:,.0f}")
    a3.metric("Annual net PKR",    f"₨ {net_monthly_pkr * 12:,.0f}")

# ── Purchasing power comparison ────────────────────────────────────────────
st.divider()
st.subheader("Purchasing Power Over Time")
st.caption(
    "How much PKR your USD $1,000/month would have yielded in previous years."
)

HISTORICAL_RATES = {
    "2019": 140, "2020": 160, "2021": 170,
    "2022": 200, "2023": 270, "2024": 278,
    "Now":  rate,
}

import plotly.graph_objects as go

years  = list(HISTORICAL_RATES.keys())
pkr_vals = [monthly_usd * r for r in HISTORICAL_RATES.values()]

fig = go.Figure(go.Bar(
    x=years, y=pkr_vals,
    marker_color=["#d1d5db"] * (len(years) - 1) + ["#1a7a3c"],
    text=[f"₨{v/1000:.0f}k" for v in pkr_vals],
    textposition="outside",
))
fig.update_layout(
    paper_bgcolor="white", plot_bgcolor="white",
    margin=dict(l=0, r=0, t=20, b=0),
    xaxis=dict(title="", showgrid=False),
    yaxis=dict(title="Monthly PKR", gridcolor="#f0f0f0"),
    showlegend=False,
)
st.plotly_chart(fig, use_container_width=True)

# ── Tips ───────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Smart Money Tips for Pakistani Freelancers")

tip1, tip2, tip3 = st.columns(3)
with tip1:
    st.info("**Hold USD** · If PKR is weakening, delay conversion. Keep 1-2 months in USD before cashing out.")
with tip2:
    st.info("**Get NTN** · Registered filers pay standard FBR rates. Unregistered pay double on many income types.")
with tip3:
    st.info("**Use USDT** · Many Pakistani freelancers hold earnings as USDT stablecoin to avoid PKR devaluation risk.")
