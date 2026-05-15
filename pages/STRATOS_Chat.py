"""
pages/STRATOS_Chat.py — IDMI AI Assistant v3.0

Changes:
  - get_market_context() now includes news headlines, live job listings
    sample, and tech prices context so STRATOS answers more accurately.
  - SYSTEM_PROMPT refined: clearer role, better guidance for price/job queries.
  - STRATOS briefing from DB shown as structured cards at the top.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import base64
import json
import io
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

from utils.db import load_data, get_latest, parse_json_col
from utils.theme import inject_css

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="STRATOS Chat | IDMI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Extra chat-specific CSS ───────────────────────────────────────────────
st.markdown("""
<style>
.voice-container {
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.file-pill {
    display: inline-block;
    background: var(--green-light);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    color: var(--green-dark);
    margin-right: 6px;
    margin-bottom: 6px;
}
.img-pill {
    background: #fff7e6;
    border-color: var(--gold);
    color: #7a5200;
}
[data-testid="stChatMessage"] {
    border-radius: 10px !important;
    margin-bottom: 6px !important;
}
.briefing-card {
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ── Groq client ───────────────────────────────────────────────────────────
@st.cache_resource
def get_groq_client():
    key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    if not key:
        st.error("GROQ_API_KEY not found in secrets. Add it to your Streamlit secrets.")
        st.stop()
    return Groq(api_key=key)

groq_client = get_groq_client()

# ── Market context from Supabase — comprehensive ──────────────────────────
@st.cache_data(ttl=600)
def get_market_context():
    """
    Build a rich market summary injected into every STRATOS system prompt.
    Includes: exchange rates, jobs volume + sample titles, top skills,
              news headlines, and a sample of tech prices.
    """
    try:
        df = load_data()
        if df.empty:
            return "No market data available yet."
        latest = get_latest(df)

        # ── Rates ─────────────────────────────────────────────────────────
        usd_pkr = latest.get("usd_pkr_rate", "N/A")

        rates_block = (
            f"  USD/PKR: {usd_pkr} | EUR/PKR: {latest.get('eur_pkr_rate','N/A')} | "
            f"GBP/PKR: {latest.get('gbp_pkr_rate','N/A')}\n"
            f"  USDT/PKR: {latest.get('usdt_pkr_rate','N/A')} | "
            f"BTC/USD: ${latest.get('btc_usd_rate','N/A')}\n"
            f"  Purchasing Power Index: {latest.get('purchasing_power_index','N/A')}"
        )

        # ── Jobs ──────────────────────────────────────────────────────────
        job_volume  = latest.get("job_volume", "N/A")
        skills      = parse_json_col(latest, "top_skills")
        top_skills_str = ", ".join([f"{s['skill']} ({s['count']})" for s in skills[:6]]) if skills else "N/A"

        jobs_data   = parse_json_col(latest, "jobs_data")
        job_titles  = [j["title"] for j in jobs_data[:6] if j.get("title")] if jobs_data else []
        jobs_sample = " | ".join(job_titles) if job_titles else "N/A"

        jobs_block = (
            f"  Live remote listings: {job_volume:,} (RemoteOK)\n"
            f"  Top in-demand skills: {top_skills_str}\n"
            f"  Sample live jobs: {jobs_sample}"
        )

        # ── News ──────────────────────────────────────────────────────────
        news = parse_json_col(latest, "news_headlines")
        news_lines = [f"  [{n['source']}] {n['title']}" for n in news[:8]] if news else []
        news_block = "\n".join(news_lines) if news_lines else "  N/A"

        # ── Key software prices in PKR (for quick answers) ────────────────
        try:
            usd = float(usd_pkr) if usd_pkr != "N/A" else 280.0
        except Exception:
            usd = 280.0

        prices_block = (
            f"  ChatGPT Plus: $20/mo = ₨ {round(20*usd):,} | "
            f"Claude Pro: $20/mo = ₨ {round(20*usd):,} | "
            f"GitHub Copilot: $10/mo = ₨ {round(10*usd):,}\n"
            f"  Adobe CC: $54.99/mo = ₨ {round(54.99*usd):,} | "
            f"Figma Pro: $12/mo = ₨ {round(12*usd):,} | "
            f"Notion Plus: $10/mo = ₨ {round(10*usd):,}\n"
            f"  NordVPN: $4.49/mo = ₨ {round(4.49*usd):,} | "
            f"Vercel Pro: $20/mo = ₨ {round(20*usd):,}"
        )

        last_updated = str(latest.get("timestamp",""))[:16]

        return (
            f"=== LIVE IDMI MARKET DATA (Pakistan digital economy) ===\n"
            f"Last updated: {last_updated} UTC\n\n"
            f"[EXCHANGE RATES]\n{rates_block}\n\n"
            f"[REMOTE JOB MARKET]\n{jobs_block}\n\n"
            f"[LATEST TECH/BUSINESS NEWS]\n{news_block}\n\n"
            f"[KEY SOFTWARE PRICES IN PKR (at live rate ₨ {usd:.0f}/USD)]\n{prices_block}"
        )
    except Exception as ex:
        return f"Market data temporarily unavailable ({ex})."


# ── STRATOS System Prompt ─────────────────────────────────────────────────
SYSTEM_PROMPT = """You are STRATOS — the AI engine of IDMI (Indus Digital Market Intelligence), Pakistan's premier freelancer intelligence platform.

You have access to LIVE market data (exchange rates, remote job listings, top skills, news headlines, and tech prices in PKR) injected below. Use this data to give accurate, specific answers.

Your expertise covers:
- Exchange rates: USD/PKR, EUR/PKR, GBP/PKR, USDT/PKR, BTC — when to convert and hold
- Freelance career: Upwork, Fiverr, Toptal, Contra — platform choice, pricing, proposals
- Skills & job market: which skills are in demand right now, what pays well, what to learn next
- Tech prices in PKR: software subscriptions, hardware, what's available in Pakistan vs import-only
- Income & taxes: FBR freelancer tax, Rozan, Payoneer, bank channels for USD receipt
- General tech & business questions

HOW TO ANSWER:
- Lead with data from the injected market context when relevant
- For price questions: always give USD price AND PKR equivalent using the live rate
- For job questions: reference the actual skill demand data and job titles from context
- For news: weave relevant headlines into your answer when applicable
- For hardware: mention Pakistani market availability (Hafeez Centre, Liberty Market, Alfatah, online import)
- Be direct, specific, and practical. No filler. Use bullet points for lists.
- If asked what you are or about STRATOS: explain you are the AI engine powering IDMI's market intelligence, chat, and automated briefings.

{market_context}"""

# ── Session state ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""
if "pending_files" not in st.session_state:
    st.session_state.pending_files = []

# ── Header ────────────────────────────────────────────────────────────────
col_title, col_clear = st.columns([5, 1])
with col_title:
    st.title("STRATOS Chat")
    st.caption("AI assistant · Live IDMI market data · Job listings · Tech prices · News · Voice · File & image analysis")
with col_clear:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_files = []
        st.rerun()

st.divider()

# ── STRATOS Latest Briefing (collapsible) ─────────────────────────────────
df     = load_data()
latest = get_latest(df)
raw_briefing = latest.get("ai_sentiment", "")

if raw_briefing:
    with st.expander("🧠 STRATOS Latest Market Briefing — click to expand", expanded=False):
        for line in raw_briefing.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("Currency Outlook:"):
                st.markdown(
                    f"<div class='briefing-card' style='background:#f0fdf4;border-left:4px solid #16a34a;'>"
                    f"<strong style='color:#15803d'>💱 Currency Outlook</strong><br>"
                    f"{line.replace('Currency Outlook:','').strip()}</div>",
                    unsafe_allow_html=True,
                )
            elif line.startswith("Job Market:"):
                st.markdown(
                    f"<div class='briefing-card' style='background:#fffbeb;border-left:4px solid #d97706;'>"
                    f"<strong style='color:#b45309'>📋 Job Market</strong><br>"
                    f"{line.replace('Job Market:','').strip()}</div>",
                    unsafe_allow_html=True,
                )
            elif line.startswith("Action Item:"):
                st.markdown(
                    f"<div class='briefing-card' style='background:#eff6ff;border-left:4px solid #2563eb;'>"
                    f"<strong style='color:#1d4ed8'>⚡ Action Item</strong><br>"
                    f"{line.replace('Action Item:','').strip()}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='briefing-card' style='background:#f9fafb;border-left:4px solid #9ca3af;'>"
                    f"{line}</div>",
                    unsafe_allow_html=True,
                )
        st.caption(f"Generated: {str(latest.get('timestamp',''))[:16]} UTC")

st.divider()

# ── Sidebar — upload & settings ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 STRATOS Engine")
    st.caption(
        "STRATOS is the AI engine powering IDMI's market briefings, "
        "job analysis, and this chat. It runs on Groq's fast inference "
        "with live Pakistan market data injected into every response."
    )
    st.divider()

    st.markdown("### Attach Files")
    st.caption("Files are sent as context with your next message.")

    uploaded = st.file_uploader(
        "Upload file or image",
        type=["txt","py","md","csv","json","png","jpg","jpeg","webp","pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded:
        new_files = []
        for f in uploaded:
            ext = f.name.split(".")[-1].lower()
            is_image = ext in ("png","jpg","jpeg","webp")
            is_pdf   = ext == "pdf"

            if is_image:
                b64  = base64.b64encode(f.read()).decode("utf-8")
                mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
                new_files.append({"type":"image","name":f.name,"b64":b64,"mime":mime})
            elif is_pdf:
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(f.read()))
                    text = "\n".join(page.extract_text() or "" for page in reader.pages[:10])
                    new_files.append({"type":"text","name":f.name,"content":text[:8000]})
                except Exception:
                    new_files.append({"type":"text","name":f.name,
                                      "content":f"[PDF: {f.name} — install pypdf to extract text]"})
            else:
                try:
                    content = f.read().decode("utf-8", errors="replace")
                    new_files.append({"type":"text","name":f.name,"content":content[:8000]})
                except Exception:
                    new_files.append({"type":"text","name":f.name,"content":f"[Could not read {f.name}]"})

        if new_files:
            st.session_state.pending_files = new_files
            for pf in new_files:
                icon = "🖼" if pf["type"] == "image" else "📄"
                pill_class = "img-pill" if pf["type"] == "image" else "file-pill"
                st.markdown(
                    f'<span class="{pill_class}">{icon} {pf["name"]}</span>',
                    unsafe_allow_html=True,
                )

    st.divider()
    st.markdown("### Settings")
    temperature = st.slider("Response creativity", 0.0, 1.0, 0.4, 0.05,
                            help="Lower = more factual; higher = more creative")
    max_tokens  = st.select_slider("Max response length",
                                   options=[300, 500, 800, 1200, 2000],
                                   value=800)

    st.divider()
    st.markdown("### Quick prompts")
    quick_prompts = [
        "What's today's USD/PKR rate and should I convert now?",
        "Which remote skills are most in demand right now?",
        "How much does ChatGPT Plus cost in PKR?",
        "What's the latest tech news relevant to Pakistani freelancers?",
        "Best platform for a Python dev: Upwork vs Toptal?",
        "How does FBR tax work for Pakistani freelancers?",
    ]
    for qp in quick_prompts:
        if st.button(qp, key=f"qp_{qp[:20]}", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":qp})
            st.rerun()

# ── Voice input component ──────────────────────────────────────────────────
VOICE_COMPONENT = """
<div class="voice-container" style="font-family:sans-serif;">
  <button id="micBtn" onclick="toggleVoice()"
    style="background:#01411C;color:white;border:none;border-radius:8px;
           padding:8px 16px;cursor:pointer;font-weight:600;font-size:13px;min-width:140px;">
    🎤 Hold to Speak
  </button>
  <span id="statusDot" style="width:8px;height:8px;border-radius:50%;
        background:#9ca3af;display:inline-block;flex-shrink:0;"></span>
  <span id="transcriptDisplay"
    style="font-size:13px;color:#5a7263;flex:1;font-style:italic;">
    Click the mic button, speak, then send your message below.
  </span>
</div>

<script>
let recognition = null;
let isListening  = false;

function setStatus(color, text, btnText) {
    document.getElementById('statusDot').style.background = color;
    document.getElementById('transcriptDisplay').textContent = text;
    document.getElementById('micBtn').textContent = btnText;
}

function fillChatInput(text) {
    // Streamlit chat_input uses a textarea — find it and set its value
    const inputs = parent.document.querySelectorAll('textarea[data-testid="stChatInputTextArea"]');
    if (inputs.length > 0) {
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value'
        ).set;
        nativeInputValueSetter.call(inputs[0], text);
        inputs[0].dispatchEvent(new Event('input', {bubbles:true}));
    }
    setStatus('#22c55e', '✓ Transcribed — press Enter to send', '🎤 Hold to Speak');
    document.getElementById('transcriptDisplay').textContent = '✓ ' + text;
}

function toggleVoice() {
    if (isListening && recognition) {
        recognition.stop();
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        setStatus('#ef4444', 'Speech recognition not supported — use Chrome or Edge', '🎤 Hold to Speak');
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
        isListening = true;
        setStatus('#ef4444', '🔴 Listening… speak now', '⏹ Stop listening');
        document.getElementById('micBtn').style.background = '#dc2626';
    };

    recognition.onresult = (event) => {
        let interim = '';
        let final   = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const t = event.results[i][0].transcript;
            if (event.results[i].isFinal) final += t;
            else interim += t;
        }
        if (final) {
            fillChatInput(final.trim());
        } else {
            document.getElementById('transcriptDisplay').textContent = '…' + interim;
        }
    };

    recognition.onerror = (e) => {
        const msgs = {
            'no-speech':     'No speech detected — try again',
            'audio-capture': 'Microphone not found',
            'not-allowed':   'Microphone permission denied — allow mic in browser',
            'network':       'Network error during recognition',
        };
        setStatus('#ef4444', '✗ ' + (msgs[e.error] || e.error), '🎤 Hold to Speak');
        document.getElementById('micBtn').style.background = '#01411C';
        isListening = false;
    };

    recognition.onend = () => {
        isListening = false;
        document.getElementById('micBtn').style.background = '#01411C';
        if (document.getElementById('statusDot').style.background === 'rgb(239, 68, 68)') {
            setStatus('#9ca3af', 'No speech heard — try again', '🎤 Hold to Speak');
        }
    };

    recognition.start();
}
</script>
"""

components.html(VOICE_COMPONENT, height=58)

# ── Chat history display ──────────────────────────────────────────────────
for msg in st.session_state.messages:
    role = msg["role"]
    with st.chat_message(role):
        if isinstance(msg["content"], list):
            for block in msg["content"]:
                if block.get("type") == "text":
                    st.markdown(block["text"])
                elif block.get("type") == "image_url":
                    st.caption("🖼 Image attached")
        else:
            st.markdown(msg["content"])

        if msg.get("attached_files"):
            for af in msg["attached_files"]:
                pill_class = "img-pill" if af["type"] == "image" else "file-pill"
                icon = "🖼" if af["type"] == "image" else "📄"
                st.markdown(
                    f'<span class="{pill_class}">{icon} {af["name"]}</span>',
                    unsafe_allow_html=True,
                )

# ── Chat input & response ─────────────────────────────────────────────────
user_input = st.chat_input("Ask STRATOS — exchange rates, job listings, tech prices, career advice…")

if user_input:
    pending     = st.session_state.pending_files.copy()
    has_image   = any(f["type"] == "image" for f in pending)
    has_text_file = any(f["type"] == "text" for f in pending)

    # Build user message content
    if has_image:
        content_blocks = []
        if has_text_file:
            file_ctx = "\n\n".join(
                f"[File: {f['name']}]\n{f['content']}"
                for f in pending if f["type"] == "text"
            )
            content_blocks.append({
                "type": "text",
                "text": f"Context from uploaded files:\n{file_ctx}\n\nUser message: {user_input}",
            })
        else:
            content_blocks.append({"type":"text","text":user_input})

        for f in pending:
            if f["type"] == "image":
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{f['mime']};base64,{f['b64']}"},
                })

        user_message = {"role":"user","content":content_blocks,"attached_files":pending}
        api_content  = content_blocks

    elif has_text_file:
        file_ctx = "\n\n".join(
            f"--- File: {f['name']} ---\n{f['content']}"
            for f in pending if f["type"] == "text"
        )
        full_text = (
            f"The user has attached the following file(s) for context:\n\n"
            f"{file_ctx}\n\nUser message: {user_input}"
        )
        user_message = {"role":"user","content":full_text,"attached_files":pending}
        api_content  = full_text

    else:
        user_message = {"role":"user","content":user_input}
        api_content  = user_input

    # Display user message
    st.session_state.messages.append(user_message)
    with st.chat_message("user"):
        st.markdown(user_input)
        if pending:
            for pf in pending:
                pill_class = "img-pill" if pf["type"] == "image" else "file-pill"
                icon = "🖼" if pf["type"] == "image" else "📄"
                st.markdown(
                    f'<span class="{pill_class}">{icon} {pf["name"]}</span>',
                    unsafe_allow_html=True,
                )
                if pf["type"] == "image":
                    img_bytes = base64.b64decode(pf["b64"])
                    st.image(img_bytes, width=280)

    # Build API messages
    system_msg = {
        "role": "system",
        "content": SYSTEM_PROMPT.format(market_context=get_market_context()),
    }

    api_history = []
    for m in st.session_state.messages[:-1]:
        api_history.append({"role": m["role"], "content": m["content"]})
    api_history.append({"role":"user","content":api_content})

    model = "llama-3.2-11b-vision-preview" if has_image else "llama-3.3-70b-versatile"

    with st.chat_message("assistant"):
        placeholder    = st.empty()
        full_response  = ""
        try:
            stream = groq_client.chat.completions.create(
                model=model,
                messages=[system_msg] + api_history,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full_response += delta
                placeholder.markdown(full_response + "▋")
            placeholder.markdown(full_response)
        except Exception as e:
            full_response = (
                f"⚠ STRATOS error: {e}\n\n"
                "Check that your GROQ_API_KEY is set in Streamlit secrets."
            )
            placeholder.error(full_response)

    st.session_state.messages.append({"role":"assistant","content":full_response})
    st.session_state.pending_files = []
    st.rerun()
