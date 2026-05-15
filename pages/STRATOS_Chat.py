"""
pages/6_🤖_STRATOS_Chat.py — IDMI AI Assistant

Features:
  - Session memory (full conversation history in st.session_state)
  - Voice input via Web Speech API (free, browser-native, no extra packages)
  - File upload: .txt, .py, .csv, .md, .json (text extracted and sent as context)
  - Image upload: .png, .jpg, .jpeg, .webp (sent to Groq vision model)
  - Market context: latest IDMI data injected into every system prompt
  - Uses Groq free tier — llama-3.3-70b-versatile (text) and
    llama-3.2-11b-vision-preview (images)
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
/* Voice button area */
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
/* Uploaded file pill */
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
/* Chat message tweaks */
[data-testid="stChatMessage"] {
    border-radius: 10px !important;
    margin-bottom: 6px !important;
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

# ── Market context from Supabase ──────────────────────────────────────────
@st.cache_data(ttl=600)
def get_market_context():
    """Build a concise market summary to inject into STRATOS system prompt."""
    try:
        df = load_data()
        if df.empty:
            return "No market data available yet."
        latest = get_latest(df)
        skills = parse_json_col(latest, "top_skills")
        top_skills_str = ", ".join([s["skill"] for s in skills[:5]]) if skills else "N/A"
        return (
            f"Live market data (Pakistan digital economy):\n"
            f"  USD/PKR: {latest.get('usd_pkr_rate', 'N/A')}\n"
            f"  EUR/PKR: {latest.get('eur_pkr_rate', 'N/A')}\n"
            f"  GBP/PKR: {latest.get('gbp_pkr_rate', 'N/A')}\n"
            f"  USDT/PKR: {latest.get('usdt_pkr_rate', 'N/A')}\n"
            f"  Purchasing Power Index: {latest.get('purchasing_power_index', 'N/A')}\n"
            f"  Live remote job listings: {latest.get('job_volume', 'N/A')}\n"
            f"  Top in-demand skills: {top_skills_str}\n"
            f"  Last updated: {str(latest.get('timestamp', ''))[:16]} UTC"
        )
    except Exception:
        return "Market data temporarily unavailable."

SYSTEM_PROMPT = """You are STRATOS, the AI assistant of IDMI (Indus Digital Market Intelligence) — a platform built for Pakistani freelancers and remote workers.

You have access to live market data and you help users with:
- Understanding exchange rates and when to convert USD to PKR
- Career advice for Pakistani freelancers (Upwork, Fiverr, Toptal)
- Skills to learn, job market trends, and platform comparisons
- Income calculations, FBR tax questions, and financial planning
- General tech and business questions

You are direct, practical, and specific to Pakistan's digital economy context.
When users upload files or images, analyze them and give actionable feedback.
Keep responses concise but complete. Use bullet points for lists. Avoid generic advice.

{market_context}"""

# ── Session state initialisation ──────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""

if "pending_files" not in st.session_state:
    st.session_state.pending_files = []   # list of {type, name, content/b64}

# ── Header ────────────────────────────────────────────────────────────────
col_title, col_clear = st.columns([5, 1])
with col_title:
    st.title("STRATOS Chat")
    st.caption("AI assistant with live IDMI market data · Voice input · File & image analysis")
with col_clear:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_files = []
        st.rerun()

st.divider()

# ── Sidebar — upload & settings ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### Attach Files")
    st.caption("Files are sent as context with your next message.")

    uploaded = st.file_uploader(
        "Upload file or image",
        type=["txt", "py", "md", "csv", "json", "png", "jpg", "jpeg", "webp", "pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded:
        new_files = []
        for f in uploaded:
            ext = f.name.split(".")[-1].lower()
            is_image = ext in ("png", "jpg", "jpeg", "webp")
            is_pdf   = ext == "pdf"

            if is_image:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
                new_files.append({
                    "type": "image", "name": f.name,
                    "b64": b64, "mime": mime,
                })
            elif is_pdf:
                # Basic PDF text extraction without pypdf
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(f.read()))
                    text = "\n".join(
                        page.extract_text() or "" for page in reader.pages[:10]
                    )
                    new_files.append({
                        "type": "text", "name": f.name,
                        "content": text[:8000],
                    })
                except Exception:
                    new_files.append({
                        "type": "text", "name": f.name,
                        "content": f"[PDF: {f.name} — install pypdf to extract text]",
                    })
            else:
                try:
                    content = f.read().decode("utf-8", errors="replace")
                    new_files.append({
                        "type": "text", "name": f.name,
                        "content": content[:8000],
                    })
                except Exception as e:
                    new_files.append({
                        "type": "text", "name": f.name,
                        "content": f"[Could not read file: {e}]",
                    })

        st.session_state.pending_files = new_files

    # Show pending files
    if st.session_state.pending_files:
        st.markdown("**Attached** (sends with next message):")
        for pf in st.session_state.pending_files:
            pill_class = "img-pill" if pf["type"] == "image" else "file-pill"
            icon = "🖼" if pf["type"] == "image" else "📄"
            st.markdown(
                f'<span class="{pill_class}">{icon} {pf["name"]}</span>',
                unsafe_allow_html=True,
            )
        if st.button("Clear attachments", use_container_width=True):
            st.session_state.pending_files = []
            st.rerun()

    st.divider()

    st.markdown("### Settings")
    temperature = st.slider("Response creativity", 0.0, 1.0, 0.5, 0.1,
                            help="Lower = more factual, Higher = more creative")
    max_tokens = st.select_slider(
        "Max response length",
        options=[256, 512, 1024, 2048],
        value=1024,
    )
    show_context = st.toggle("Show market data context", value=False,
                             help="Shows the live data injected into every prompt")
    if show_context:
        st.code(get_market_context(), language=None)

    st.divider()
    st.caption(f"💬 {len(st.session_state.messages)} messages in session")
    st.caption("Powered by Groq · Llama 3.3 70B · Free tier")

# ── Voice input component ─────────────────────────────────────────────────
# Uses Web Speech API (browser-native, free, no packages needed).
# JavaScript fills the Streamlit chat textarea via DOM manipulation.
VOICE_COMPONENT = """
<div style="
    background: #ffffff;
    border: 1px solid #e2e8e4;
    border-radius: 10px;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    font-family: 'IBM Plex Mono', monospace;
">
    <button id="micBtn" onclick="toggleVoice()" style="
        background: #01411C;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        white-space: nowrap;
        font-family: inherit;
    ">🎤 Hold to Speak</button>

    <span id="statusDot" style="
        width: 8px; height: 8px;
        background: #9ca3af;
        border-radius: 50%;
        flex-shrink: 0;
        transition: background 0.3s;
    "></span>

    <span id="transcriptDisplay" style="
        font-size: 13px;
        color: #5a7263;
        font-style: italic;
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    ">Click the button and speak…</span>
</div>

<script>
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isListening = false;

function setStatus(color, text, btnText) {
    document.getElementById('statusDot').style.background = color;
    document.getElementById('transcriptDisplay').textContent = text;
    document.getElementById('micBtn').innerHTML = btnText;
}

function fillChatInput(text) {
    // Find Streamlit's chat input textarea in parent frame
    try {
        const selectors = [
            'textarea[data-testid="stChatInputTextArea"]',
            'textarea[aria-label*="chat"]',
            'textarea[placeholder*="message"]',
            '.stChatInput textarea',
            'textarea'
        ];
        let textarea = null;
        for (const sel of selectors) {
            textarea = window.parent.document.querySelector(sel);
            if (textarea) break;
        }
        if (textarea) {
            // React-friendly value setter
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.parent.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(textarea, text);
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));
            textarea.focus();
            setStatus('#22c55e', '✓ Text sent to chat input — press Enter to send', '🎤 Hold to Speak');
        } else {
            setStatus('#f59e0b', '⚠ Auto-fill unavailable — copy text manually: ' + text, '🎤 Hold to Speak');
        }
    } catch(e) {
        setStatus('#f59e0b', 'Copy this text: ' + text, '🎤 Hold to Speak');
    }
}

function toggleVoice() {
    if (!SpeechRecognition) {
        setStatus('#ef4444', '✗ Voice not supported in this browser (use Chrome/Edge)', '🎤 Not supported');
        return;
    }
    if (isListening) {
        recognition && recognition.stop();
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
        let final = '';
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
            'no-speech':          'No speech detected — try again',
            'audio-capture':      'Microphone not found',
            'not-allowed':        'Microphone permission denied — allow mic in browser',
            'network':            'Network error during recognition',
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
        # Display text content
        if isinstance(msg["content"], list):
            for block in msg["content"]:
                if block.get("type") == "text":
                    st.markdown(block["text"])
                elif block.get("type") == "image_url":
                    st.caption("🖼 Image attached")
        else:
            st.markdown(msg["content"])

        # Show attached file pills in history
        if msg.get("attached_files"):
            for af in msg["attached_files"]:
                pill_class = "img-pill" if af["type"] == "image" else "file-pill"
                icon = "🖼" if af["type"] == "image" else "📄"
                st.markdown(
                    f'<span class="{pill_class}">{icon} {af["name"]}</span>',
                    unsafe_allow_html=True,
                )

# ── Chat input & response ─────────────────────────────────────────────────
user_input = st.chat_input("Ask STRATOS anything about Pakistan's digital economy…")

if user_input:
    pending = st.session_state.pending_files.copy()
    has_image = any(f["type"] == "image" for f in pending)
    has_text_file = any(f["type"] == "text" for f in pending)

    # ── Build the user message content ────────────────────────────────────
    if has_image:
        # Vision model requires content as list of blocks
        content_blocks = []

        # Add text files as context text first
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
            content_blocks.append({"type": "text", "text": user_input})

        # Add images
        for f in pending:
            if f["type"] == "image":
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{f['mime']};base64,{f['b64']}"},
                })

        user_message = {"role": "user", "content": content_blocks,
                        "attached_files": pending}
        api_content = content_blocks  # send to Groq as-is

    elif has_text_file:
        # Text files — inject as context, use text model
        file_ctx = "\n\n".join(
            f"--- File: {f['name']} ---\n{f['content']}"
            for f in pending if f["type"] == "text"
        )
        full_text = (
            f"The user has attached the following file(s) for context:\n\n"
            f"{file_ctx}\n\n"
            f"User message: {user_input}"
        )
        user_message = {"role": "user", "content": full_text,
                        "attached_files": pending}
        api_content = full_text

    else:
        user_message = {"role": "user", "content": user_input}
        api_content  = user_input

    # ── Display user message ───────────────────────────────────────────────
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

    # ── Build API messages (history + system) ─────────────────────────────
    system_msg = {
        "role": "system",
        "content": SYSTEM_PROMPT.format(market_context=get_market_context()),
    }

    # Build history for API — strip attached_files metadata, keep content only
    api_history = []
    for m in st.session_state.messages[:-1]:  # exclude the one we just added
        api_history.append({"role": m["role"], "content": m["content"]})

    # Current message
    api_history.append({"role": "user", "content": api_content})

    # ── Call Groq ──────────────────────────────────────────────────────────
    model = "llama-3.2-11b-vision-preview" if has_image else "llama-3.3-70b-versatile"

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
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
            full_response = f"⚠ STRATOS error: {e}\n\nCheck that your GROQ_API_KEY is set in Streamlit secrets."
            placeholder.error(full_response)

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
    })

    # Clear pending attachments after sending
    st.session_state.pending_files = []
    st.rerun()
