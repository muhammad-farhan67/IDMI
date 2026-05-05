import streamlit as st

IDMI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&display=swap');

/* ── Variables — light (default) ─────────────────────── */
:root {
    --green-dark:   #01411C;
    --green-mid:    #1a7a3c;
    --green-light:  #e8f5ee;
    --gold:         #C9A84C;
    --surface:      #f8faf9;
    --card-bg:      #ffffff;
    --border:       #e2e8e4;
    --text-primary: #0d1f15;
    --text-muted:   #5a7263;
    --font-mono:    'IBM Plex Mono', 'Courier New', monospace;
    --info-bg:      #eef7f1;
    --input-bg:     #ffffff;
}

/* ── Dark mode — Streamlit injects data-theme="dark" on <body> ── */
[data-theme="dark"] {
    --surface:      #111917;
    --card-bg:      #192419;
    --border:       #2d3f30;
    --text-primary: #e2ede6;
    --text-muted:   #8aab94;
    --green-light:  #1e3024;
    --info-bg:      #192419;
    --input-bg:     #192419;
    --gold:         #d4af5a;
}

/* ── Base ─────────────────────────────────────────────── */
.stApp { background: var(--surface) !important; }
div.block-container { padding-top: 2rem !important; }

/* Force ALL text in dark mode to be readable */
[data-theme="dark"] .stApp,
[data-theme="dark"] .stApp * {
    color: var(--text-primary);
}
/* But don't override Streamlit's own component colours */
[data-theme="dark"] [data-testid="stMetricDelta"] { color: inherit; }

/* ── Headings ─────────────────────────────────────────── */
h1 {
    font-size: 26px !important; font-weight: 700 !important;
    color: var(--text-primary) !important; letter-spacing: -0.5px;
}
h2 {
    font-size: 17px !important; font-weight: 600 !important;
    color: var(--green-mid) !important;
    text-transform: uppercase; letter-spacing: 1px;
    border-bottom: 2px solid var(--green-light);
    padding-bottom: 6px; margin-top: 32px !important;
}
h3 { font-size: 15px !important; font-weight: 600 !important; color: var(--text-primary) !important; }

[data-testid="stCaptionContainer"] p { color: var(--text-muted) !important; }
hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* ── Sidebar — always deep green ─────────────────────── */
[data-testid="stSidebar"] { background: var(--green-dark) !important; }
[data-testid="stSidebar"] * { color: #d4e8da !important; }
[data-testid="stSidebar"] a:hover,
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,0.08) !important; border-radius: 6px;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(201,168,76,0.25) !important;
    border-left: 3px solid var(--gold) !important;
    border-radius: 0 6px 6px 0 !important;
}
[data-testid="stSidebar"]::before {
    content: "IDMI"; display: block;
    font-family: var(--font-mono); font-size: 22px; font-weight: 700;
    color: #ffffff !important; letter-spacing: 4px;
    padding: 24px 20px 4px 20px;
}
[data-testid="stSidebar"]::after {
    content: "Market Intelligence"; display: block;
    font-size: 11px; color: var(--gold) !important;
    letter-spacing: 2px; text-transform: uppercase;
    padding: 0 20px 20px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 8px;
}

/* ── Metric cards ─────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px; padding: 18px 20px !important;
    box-shadow: 0 1px 4px rgba(1,65,28,0.06);
}
[data-testid="metric-container"] label {
    font-size: 11px !important; letter-spacing: 1.5px;
    text-transform: uppercase; color: var(--text-muted) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important; font-size: 26px !important;
    font-weight: 700 !important; color: var(--text-primary) !important;
}
[data-testid="stMetricDelta"] { font-family: var(--font-mono) !important; font-size: 13px !important; }

/* ── Alert boxes ──────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 8px !important; border-left-width: 4px !important;
    background: var(--info-bg) !important;
}

/* ── DataFrames ───────────────────────────────────────── */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 8px !important; }

/* ── Buttons ──────────────────────────────────────────── */
.stButton > button {
    background: var(--green-dark) !important; color: #ffffff !important;
    border: none !important; border-radius: 6px !important;
    font-weight: 600 !important; letter-spacing: 0.5px;
}
.stButton > button:hover {
    background: var(--green-mid) !important;
    box-shadow: 0 3px 10px rgba(1,65,28,0.3) !important;
}

/* ── Inputs ───────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    border-radius: 6px !important; border-color: var(--border) !important;
    font-family: var(--font-mono) !important;
    background: var(--input-bg) !important; color: var(--text-primary) !important;
}

/* ── Plotly chart wrapper ─────────────────────────────── */
.stPlotlyChart {
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 10px; padding: 8px;
}

/* ── Expander ─────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important; background: var(--card-bg) !important;
}

/* ── Live dot ─────────────────────────────────────────── */
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(0.85); }
}
.live-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #22c55e; border-radius: 50%;
    margin-right: 6px; animation: pulse 1.8s ease-in-out infinite;
}

/* ── News card ────────────────────────────────────────── */
.news-card {
    background: var(--card-bg); border: 1px solid var(--border);
    border-left: 4px solid var(--green-mid);
    border-radius: 0 8px 8px 0; padding: 12px 16px; margin-bottom: 10px;
}
.news-card .source {
    font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
    color: var(--gold); font-weight: 700; margin-bottom: 3px;
}
.badge-pk {
    display: inline-block; font-size: 9px; font-weight: 700;
    letter-spacing: 0.8px; text-transform: uppercase;
    background: rgba(1,65,28,0.15); color: var(--green-mid);
    border-radius: 3px; padding: 1px 5px; margin-left: 5px;
}
.badge-global {
    display: inline-block; font-size: 9px; font-weight: 700;
    letter-spacing: 0.8px; text-transform: uppercase;
    background: rgba(201,168,76,0.18); color: #8a6e20;
    border-radius: 3px; padding: 1px 5px; margin-left: 5px;
}
[data-theme="dark"] .badge-global { color: var(--gold); background: rgba(201,168,76,0.25); }
.news-card .headline {
    font-size: 14px; font-weight: 500;
    color: var(--text-primary); text-decoration: none;
    display: block; line-height: 1.45;
}
.news-card .headline:hover { color: var(--green-mid); text-decoration: underline; }

/* ── Calc card ────────────────────────────────────────── */
.calc-card {
    background: var(--green-dark); color: white;
    border-radius: 10px; padding: 24px; text-align: center;
}
.calc-card .label {
    font-size: 11px; letter-spacing: 2px; text-transform: uppercase;
    opacity: 0.7; color: white !important;
}
.calc-card .amount {
    font-family: var(--font-mono); font-size: 36px;
    font-weight: 700; color: var(--gold); margin: 4px 0;
}
</style>
"""

def inject_css():
    st.markdown(IDMI_CSS, unsafe_allow_html=True)
