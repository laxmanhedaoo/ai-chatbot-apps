
import asyncio
import os
import subprocess
import sys
import time
import base64
from pathlib import Path
from xml.sax.saxutils import escape

import psutil
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from outbound_calling import CallSettings, end_call, is_call_active, make_call
from utils.agent_utils.voice_catalog import (
    get_available_genders,
    get_available_languages,
    get_default_voice,
    get_language_locale,
    get_preview_text,
    get_voice_options,
)

PROJECT_ROOT = Path(__file__).parent
WORKER_LOG_PATH = PROJECT_ROOT / "outbound_worker.log"
WORKER_PID_KEY = "outbound_worker_pid"

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

st.set_page_config(
    page_title="Outbound Agent Studio",
    page_icon="Phone",
    layout="wide",
)

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(255, 210, 160, 0.42), transparent 28%),
                    radial-gradient(circle at top right, rgba(152, 220, 214, 0.30), transparent 22%),
                    linear-gradient(180deg, #fff7ec 0%, #fffdf9 46%, #edf6f5 100%);
            }
            html, body, [class*="css"] {
                font-family: "Avenir Next", "Trebuchet MS", sans-serif;
            }
            h1, h2, h3 {
                font-family: "Georgia", "Times New Roman", serif;
                letter-spacing: 0.02em;
            }

            input, textarea {
                caret-color: #1a2e3b !important;
            }

            ::placeholder {
                color: #8899a6 !important;
                opacity: 1 !important;
            }
            
            input::placeholder, textarea::placeholder {
                color: #8899a6 !important;
            }

            input:-webkit-autofill,
            input:-webkit-autofill:hover, 
            input:-webkit-autofill:focus,
            textarea:-webkit-autofill,
            textarea:-webkit-autofill:hover,
            textarea:-webkit-autofill:focus {
                -webkit-text-fill-color: #1a2e3b !important;
                -webkit-box-shadow: 0 0 0px 1000px white inset !important;
                transition: background-color 5000s ease-in-out 0s;
            }

            [data-testid="stMetricValue"], 
            [data-testid="stMetricLabel"] > div {
                color: #1a2e3b !important;
                -webkit-text-fill-color: #1a2e3b !important;
            }
            
            div[data-baseweb="select"] > div, 
            div[role="button"][aria-expanded],
            div[data-baseweb="base-input"], 
            textarea, 
            input {
                background-color: white !important;
                color: #1a2e3b !important;
            }

            div[data-testid="stSelectbox"] p, 
            div[data-testid="stSelectbox"] svg {
                color: #1a2e3b !important;
                fill: #1a2e3b !important;
            }

            div[data-testid="stButton"] button:not([kind="primary"]) {
                background-color: #ffffff !important;
                color: #1a2e3b !important;
                border: 1px solid rgba(79, 98, 118, 0.2) !important;
            }

            .hero-shell {
                display: flex;
                flex-direction: row;
                align-items: center;
                gap: 25px;
                padding: 1.25rem 1.5rem;
                border: 1px solid rgba(79, 98, 118, 0.14);
                border-radius: 24px;
                background: rgba(255, 255, 255, 0.82);
                box-shadow: 0 18px 50px rgba(79, 98, 118, 0.10);
                backdrop-filter: blur(10px);
                margin-bottom: 1rem;
            }
            .hero-text-box { flex: 1; }
            .hero-kicker { color: #a2551d; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; }
            .hero-copy { color: #415567; font-size: 1rem; }
            
            div[role="radiogroup"] label p { color: #1a2e3b !important; font-weight: 600 !important; }
            div[role="radiogroup"] label span:first-child { border: 2px solid #4a6375 !important; background: #F7F7FF !important; }
            
            .stApp h2, .stApp h3 { color: #4a6375 !important; }
            .stApp p, .stApp label, .stApp span { color: #1a2e3b; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def ensure_session_defaults() -> None:
    st.session_state.setdefault("agent_prompt", "")
    st.session_state.setdefault("phone_number", "")
    st.session_state.setdefault("call_started_at", None)
    st.session_state.setdefault("call_room_name", "")
    st.session_state.setdefault("call_status", "Idle")
    st.session_state.setdefault("call_error", "")
    st.session_state.setdefault("preview_voice_key", "")
    st.session_state.setdefault("preview_audio_bytes", None)

def clear_call_session_state() -> None:
    st.session_state["call_started_at"] = None
    st.session_state["call_status"] = "Idle"
    st.session_state["call_error"] = ""
    st.session_state["call_room_name"] = ""

def run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

@st.cache_data(show_spinner=False)
def synthesize_preview_audio(voice_id: str, language: str, text: str) -> bytes:
    speech_key = os.getenv("AZURE_SPEECH_API_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    if not speech_key or not speech_region:
        raise RuntimeError("AZURE_SPEECH_API_KEY or AZURE_SPEECH_REGION is missing in .env")

    locale = get_language_locale(language)
    endpoint = f"https://{speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
        "User-Agent": "streamlit-outbound-agent",
    }
    ssml = (
        f"<speak version='1.0' xml:lang='{locale}'>"
        f"<voice xml:lang='{locale}' name='{escape(voice_id)}'>"
        f"{escape(text)}"
        "</voice>"
        "</speak>"
    )
    response = requests.post(endpoint, headers=headers, data=ssml.encode("utf-8"), timeout=30)
    response.raise_for_status()
    return response.content

def get_worker_process() -> psutil.Process | None:
    worker_pid = st.session_state.get(WORKER_PID_KEY)
    if not worker_pid:
        return None
    try:
        process = psutil.Process(worker_pid)
        cmdline = " ".join(process.cmdline())
        if process.is_running() and "outbound_agent.py" in cmdline:
            return process
    except (psutil.Error, OSError):
        pass
    st.session_state.pop(WORKER_PID_KEY, None)
    return None

def start_worker() -> int:
    existing_process = get_worker_process()
    if existing_process:
        return existing_process.pid
    WORKER_LOG_PATH.touch(exist_ok=True)
    with WORKER_LOG_PATH.open("ab") as log_file:
        process = subprocess.Popen(
            [sys.executable, "outbound_agent.py"],
            cwd=str(PROJECT_ROOT),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    st.session_state[WORKER_PID_KEY] = process.pid
    return process.pid

def stop_worker() -> None:
    process = get_worker_process()
    if not process:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except psutil.TimeoutExpired:
        process.kill()
    finally:
        st.session_state.pop(WORKER_PID_KEY, None)

def render_timer(started_at: float) -> None:
    components.html(
        f"""
        <div style="
            border: 1px solid rgba(79, 98, 118, 0.14);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.90);
            padding: 0.9rem 1rem;
            box-shadow: 0 14px 28px rgba(79, 98, 118, 0.08);
        ">
            <div style="font-size: 0.82rem; letter-spacing: 0.08em; text-transform: uppercase; color: #7a5b40;">
                Call Timer
            </div>
            <div id="call-timer" style="font-family: 'Courier New', monospace; font-size: 1.85rem; color: #16374a; margin-top: 0.35rem;">
                00:00:00
            </div>
        </div>
        <script>
            const startedAt = {int(started_at * 1000)};
            const node = document.getElementById("call-timer");
            function pad(value) {{ return String(value).padStart(2, "0"); }}
            function tick() {{
                const elapsed = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
                const hours = Math.floor(elapsed / 3600);
                const minutes = Math.floor((elapsed % 3600) / 60);
                const seconds = elapsed % 60;
                node.innerText = `${{pad(hours)}}:${{pad(minutes)}}:${{pad(seconds)}}`;
            }}
            tick();
            setInterval(tick, 1000);
        </script>
        """,
        height=110,
    )

def render_sidebar() -> None:
    st.sidebar.markdown("## Worker Control")
    worker = get_worker_process()
    if worker:
        st.sidebar.markdown('<div class="status-chip">Worker running</div>', unsafe_allow_html=True)
        st.sidebar.caption(f"PID: {worker.pid}")
    else:
        st.sidebar.markdown('<div class="status-chip">Worker not started</div>', unsafe_allow_html=True)
    start_col, stop_col = st.sidebar.columns(2)
    if start_col.button("Start Worker", use_container_width=True, disabled=bool(worker)):
        pid = start_worker()
        st.sidebar.success(f"Worker started on PID {pid}")
    if stop_col.button("Stop Worker", use_container_width=True, disabled=not bool(worker)):
        stop_worker()
        st.sidebar.info("Worker stopped")
    if WORKER_LOG_PATH.exists():
        with st.sidebar.expander("Recent Worker Logs"):
            try:
                lines = WORKER_LOG_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
                st.code("\n".join(lines[-12:]) or "No logs yet.", language="text")
            except OSError:
                st.write("Could not read log file.")

def sync_live_call_state() -> bool:
    active_room_name = st.session_state.get("call_room_name", "").strip()
    if not active_room_name: return False
    try:
        call_is_active = run_async(is_call_active(active_room_name))
    except Exception as exc:
        st.session_state["call_error"] = str(exc)
        return True
    if call_is_active: return True
    clear_call_session_state()
    return False

@st.fragment(run_every="2s" if st.session_state.get("call_room_name") else None)
def render_call_controls(language: str, gender: str, voice_id: str) -> None:
    if st.session_state.get("call_room_name") and not sync_live_call_state():
        st.rerun()
    action_col, timer_col = st.columns([0.92, 1.08], gap="large")
    with action_col:
        is_calling = bool(st.session_state.get("call_room_name"))
        if st.button("Make Call", type="primary", use_container_width=True, disabled=is_calling):
            phone_number = st.session_state["phone_number"].strip()
            st.session_state["call_error"] = ""
            st.session_state["call_status"] = "Initiating..."
            if not phone_number:
                st.session_state["call_error"] = "Please enter a phone number."
                st.session_state["call_status"] = "Idle"
            else:
                time.sleep(0.5)
                settings = CallSettings(prompt=st.session_state["agent_prompt"].strip(), language=language, gender=gender, voice_id=voice_id)
                try:
                    room_name = run_async(make_call(phone_number=phone_number, call_settings=settings))
                    st.session_state["call_started_at"] = time.time()
                    st.session_state["call_room_name"] = room_name
                    st.session_state["call_status"] = f"Connected to {phone_number}"
                    st.rerun()
                except Exception as exc:
                    st.session_state["call_error"] = str(exc)
                    st.session_state["call_status"] = "Idle"
        st.markdown(f"**Status:** {st.session_state.get('call_status', 'Idle')}")
        if st.session_state.get("call_error"): st.error(st.session_state["call_error"])
        if st.button("Reset Session / End Call"):
            active_room_name = st.session_state.get("call_room_name", "").strip()
            if active_room_name:
                try: run_async(end_call(active_room_name))
                except: pass
            clear_call_session_state()
            st.rerun()
    with timer_col:
        started_at = st.session_state.get("call_started_at")
        if started_at: render_timer(started_at)
        else: st.metric("Call Timer", "00:00:00")

def main() -> None:
    inject_styles()
    ensure_session_defaults()
    render_sidebar()

    img_path = PROJECT_ROOT / "templates" / "image.png"
    img_b64 = get_base64_image(img_path)

    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="logo-box">
                <img src="data:image/png;base64,{img_b64}" style="height: 80px; width: auto;">
            </div>
            <div class="hero-text-box">
                <div class="hero-kicker">Outbound Calling Console</div>
                <h1 style="margin: 0; color: red;">Aceint Control Panel for your outbound agent</h1>
                <p class="hero-copy">
                    Pick the voice gender, language, and voice ID, preview the audio, write the agent prompt,
                    dial a phone number, and track the elapsed call time from one screen.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.05, 1.2], gap="large")
    with left_col:
        st.subheader("Voice Setup")
        gender = st.radio("Male or Female Audio", options=get_available_genders(), horizontal=True)
        languages = get_available_languages()
        language = st.selectbox("Language", options=languages, index=languages.index("Hindi") if "Hindi" in languages else 0)
        
        # --- VOICE ID HIDING LOGIC START ---
        voice_options = get_voice_options(language, gender)
        # We clean the labels here: hi-IN-SwaraNeural -> Swara
        clean_labels = [v["label"].split('-')[-1].replace("Neural", "") for v in voice_options]
        
        default_voice_full = get_default_voice(language, gender)
        # Find index based on the cleaned name
        default_idx = 0
        if default_voice_full:
            default_name_clean = default_voice_full.split('-')[-1].replace("Neural", "")
            if default_name_clean in clean_labels:
                default_idx = clean_labels.index(default_name_clean)

        selected_clean_name = st.selectbox("Voice ID", options=clean_labels, index=default_idx)
        
        # Map the clean name back to the actual technical ID needed for the API
        voice_id = voice_options[clean_labels.index(selected_clean_name)]["id"]
        # --- VOICE ID HIDING LOGIC END ---

        if st.button("Play Audio Preview", use_container_width=True):
            try:
                st.session_state["preview_audio_bytes"] = synthesize_preview_audio(voice_id, language, get_preview_text(language))
                st.session_state["preview_voice_key"] = f"{language}:{gender}:{voice_id}"
            except Exception as exc: st.error(f"Error: {exc}")

        if st.session_state.get("preview_voice_key") == f"{language}:{gender}:{voice_id}" and st.session_state.get("preview_audio_bytes"):
            st.audio(st.session_state["preview_audio_bytes"], format="audio/wav")

    with right_col:
        st.subheader("Call Setup")
        st.text_area("Agent Prompt", key="agent_prompt", height=220)
        st.text_input("Phone Call Number", key="phone_number", placeholder="+919999999999")

    render_call_controls(language, gender, voice_id)

    st.divider()
    st.subheader("Selected Call Configuration")
    c1, c2, c3 = st.columns(3)
    c1.metric("Voice Gender", gender)
    c2.metric("Language", language)

if __name__ == "__main__":
    main()