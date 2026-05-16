"""
pages/About.py — Project overview
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.db import load_data, get_latest, parse_json_col
from utils.theme import inject_css

st.set_page_config(page_title="About | IDMI", page_icon="ℹ️", layout="wide")
inject_css()

st.title("About IDMI")
st.caption("Indus Digital Market Intelligence — Pakistan's freelancer intelligence platform")

col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("""
## What is IDMI?

**Indus Digital Market Intelligence (IDMI)** is a real-time intelligence platform built for Pakistan's digital economy. It tracks exchange rates, live remote job listings, software prices in PKR, and AI-powered market briefings.

## Who is it for?

- **Freelancers** on Upwork, Fiverr, and Toptal who need to know the best time to convert USD earnings to PKR
- **Remote workers** tracking which tech skills are most in demand globally right now
- **Digital entrepreneurs** monitoring Pakistan's tech economy and software costs in PKR
- **Students** entering the freelance market who want real data to guide their skill choices

## How the Data Pipeline Works

A Python pipeline runs automatically via **GitHub Actions every 12 hours**, pulling:

- **Exchange rates** — USD, EUR, GBP, SAR, AED, USDT, BTC vs PKR from open APIs
- **Live remote jobs** — Full job listings from RemoteOK (title, company, salary, skills, apply link) with skill demand analytics
- **Tech prices** — Curated software subscriptions and hardware prices, auto-converted to PKR at the live exchange rate


All data is stored in **Supabase (PostgreSQL)** and the Streamlit app reads from it with a 10-minute cache.
""")

    st.divider()

    st.markdown("""
## 🧠 The STRATOS Engine

**STRATOS** (Strategic Tracking and Reporting AI for Opportunistic Signals) is the AI engine powering IDMI's intelligence layer. It appears in three places:

### 1. Automated Market Briefing
After every pipeline run, STRATOS analyses the freshest snapshot — exchange rates, live job titles, top skill demand, and news headlines — and generates a structured 3-part briefing:

> **Currency Outlook** — Is now a good time to invoice in USD, hold dollars, or convert?
>
> **Job Market** — Which specific skills and roles are seeing live demand right now?
>
> **Action Item** — One concrete, data-backed recommendation for this week.

The briefing is stored in Supabase and displayed on the Home page, Market Intelligence page, and the STRATOS Chat sidebar.

### 2. STRATOS Chat
The interactive chat assistant on the STRATOS Chat page has access to all live IDMI data — exchange rates, actual job listings and titles, top skill demand, news headlines, and tech prices in PKR — injected into every response. Ask it anything about Pakistan's digital economy.

### 3. Tech Price AI Search
The AI Price Search tab on the Tech Prices page lets you ask STRATOS about any software or hardware price, including Pakistani availability, import advice, and alternatives — using the live USD/PKR rate.

## Features

- **Live Job Listings** — Search and filter 60+ live remote jobs from RemoteOK with salary info and direct Apply links
- **Software Prices in PKR** — 50+ tools with live PKR conversion and direct "Visit Site" links
- **Hardware Prices** — Popular devices with PKR conversion and Amazon search links
- **Skills Radar** — Top 10 in-demand skills with historical trend charts
- **Platform Comparison** — Upwork vs Fiverr vs Toptal vs Contra with fee analysis
- **Salary Benchmarks** — 18 roles with USD/hr ranges and live PKR monthly equivalents
- **Income Calculator** — Multi-currency income with FBR tax brackets (Freelancer Tools page)
- **Voice Input** — Browser-native speech-to-text in STRATOS Chat (Chrome/Edge)
- **File & Image Analysis** — Upload PDFs, code files, CSV, or images for STRATOS to analyse

""")

