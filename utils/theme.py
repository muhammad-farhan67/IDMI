import streamlit as st

IDMI_CSS = """
<style>
/* ── Brand variables ─────────────────────────────────── */
:root {
    --green-dark:   #01411C;
    --green-mid:    #1a7a3c;
    --green-light:  #e8f5ee;
    --gold:         #C9A84C;
    --surface:      #f8faf9;
    --border:       #e2e8e4;
    --text-primary: #0d1f15;
    --text-muted:   #5a7263;
    --font-mono:    'IBM Plex Mono', 'Courier New', monospace;
}

/* ── Sidebar ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--green-dark) !important;
}
[data-testid="stSidebar"] * {
    color: #d4e8da !important;
}
[data-testid="stSidebar"] a:hover,
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,0.08) !important;
    border-radius: 6px;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(201,168,76,0.25) !important;
    border-left: 3px solid var(--gold) !important;
    border-radius: 0 6px 6px 0 !important;
}
/* Sidebar brand header */
[data-testid="stSidebar"]::before {
    content: "IDMI";
    display: block;
    font-family: var(--font-mono);
    font-size: 22px;
    font-weight: 700;
    color: #ffffff !important;
    letter-spacing: 4px;
    padding: 24px 20px 4px 20px;
}
[data-testid="stSidebar"]::after {
    content: "Market Intelligence";
    display: block;
    font-size: 11px;
    color: var(--gold) !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 0 20px 20px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 8px;
}

/* ── Main layout ─────────────────────────────────────── */
.stApp { background: var(--surface) !important; }
div.block-container { padding-top: 2rem !important; }

/* ── Metric cards ────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px !important;
    box-shadow: 0 1px 4px rgba(1,65,28,0.06);
}
[data-testid="metric-container"] label {
    font-size: 11px !important;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-muted) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}
[data-testid="stMetricDelta"] {
    font-family: var(--font-mono) !important;
    font-size: 13px !important;
}

/* ── Page headers ────────────────────────────────────── */
h1 { 
    font-size: 26px !important; 
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.5px;
}
h2 { 
    font-size: 17px !important; 
    font-weight: 600 !important;
    color: var(--green-dark) !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 2px solid var(--green-light);
    padding-bottom: 6px;
    margin-top: 32px !important;
}
h3 { font-size: 15px !important; font-weight: 600 !important; }

/* ── Divider ─────────────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* ── Info / warning boxes ────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border-left-width: 4px !important;
}

/* ── DataFrames ──────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── Buttons ─────────────────────────────────────────── */
[data-testid="baseButton-primary"],
.stButton > button {
    background: var(--green-dark) !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
}
.stButton > button:hover {
    background: var(--green-mid) !important;
    box-shadow: 0 3px 10px rgba(1,65,28,0.3) !important;
}

/* ── Select / Input ──────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
    border-radius: 6px !important;
    border-color: var(--border) !important;
    font-family: var(--font-mono) !important;
}

/* ── Plotly chart container ──────────────────────────── */
.stPlotlyChart {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px;
}

/* ── Live dot animation ──────────────────────────────── */
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(0.85); }
}
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 1.8s ease-in-out infinite;
}

/* ── News card ───────────────────────────────────────── */
.news-card {
    background: #ffffff;
    border: 1px solid var(--border);
    border-left: 4px solid var(--green-mid);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.news-card .source {
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--gold);
    font-weight: 600;
}
.news-card .headline {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
    margin-top: 2px;
    text-decoration: none;
    display: block;
}
.news-card .headline:hover { color: var(--green-mid); }

/* ── Calc result card ────────────────────────────────── */
.calc-card {
    background: var(--green-dark);
    color: white;
    border-radius: 10px;
    padding: 24px;
    text-align: center;
}
.calc-card .label {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: 0.7;
}
.calc-card .amount {
    font-family: var(--font-mono);
    font-size: 36px;
    font-weight: 700;
    color: var(--gold);
    margin: 4px 0;
}
</style>
"""

def inject_css():
    st.markdown(IDMI_CSS, unsafe_allow_html=True)
