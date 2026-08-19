"""
🎮 MEDALLION DATA QUEST 🎮
A gamified Streamlit pipeline for epic data transformations.
"""
import json
import sys
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.orchestrator import approve_bronze, approve_gold, approve_silver, start_pipeline
from agents.reporter import ask_question
from core.auth import load_progress, register_user, save_progress, verify_user
from core.config import LANDING_DIR
from core.llm import is_llm_configured

# ═════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🎮 Medallion Data Quest",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═════════════════════════════════════════════════════════════════════════════
if "state" not in st.session_state:
    st.session_state.state = None
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "level" not in st.session_state:
    st.session_state.level = 1
if "achievements" not in st.session_state:
    st.session_state.achievements = []
if "oracle_answer" not in st.session_state:
    st.session_state.oracle_answer = None
if "oracle_query_count" not in st.session_state:
    st.session_state.oracle_query_count = 0
if "oracle_prompted" not in st.session_state:
    st.session_state.oracle_prompted = False
if "show_restart_prompt" not in st.session_state:
    st.session_state.show_restart_prompt = False
if "view_stage" not in st.session_state:
    st.session_state.view_stage = None
if "username" not in st.session_state:
    st.session_state.username = None
if "progress_loaded" not in st.session_state:
    st.session_state.progress_loaded = False
if "disclaimer_ack" not in st.session_state:
    st.session_state.disclaimer_ack = False


# ═════════════════════════════════════════════════════════════════════════════
# ACCOUNT LOGIN — gate the whole app behind a per-user account
# ═════════════════════════════════════════════════════════════════════════════
def render_login_page():
    st.markdown("<h1 style='text-align:center;'>⚔️ MEDALLION DATA QUEST ⚔️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Sign in to resume your quest, or create a new account.</p>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        tab_login, tab_signup = st.tabs(["🔑 Login", "🛡️ Create Account"])
        with tab_login:
            u = st.text_input("Username", key="login_user")
            p = st.text_input("Password", type="password", key="login_pass")
            if st.button("⚔️ Enter the Realm", width='stretch'):
                if verify_user(u, p):
                    st.session_state.username = u.strip().lower()
                    st.session_state.progress_loaded = False
                    st.session_state.disclaimer_ack = False
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        with tab_signup:
            nu = st.text_input("Choose a username", key="signup_user")
            np_ = st.text_input("Choose a password", type="password", key="signup_pass")
            if st.button("🛡️ Create Account", width='stretch'):
                err = register_user(nu, np_)
                if err:
                    st.error(err)
                else:
                    st.success("Account created! Switch to the Login tab to enter.")


if not st.session_state.username:
    render_login_page()
    st.stop()

if not st.session_state.progress_loaded:
    saved = load_progress(st.session_state.username)
    st.session_state.xp = saved.get("xp", 0)
    st.session_state.level = saved.get("level", 1)
    st.session_state.achievements = saved.get("achievements", [])
    st.session_state.oracle_query_count = saved.get("oracle_query_count", 0)
    st.session_state.oracle_prompted = saved.get("oracle_prompted", False)
    st.session_state.state = saved.get("state")
    st.session_state.oracle_answer = saved.get("oracle_answer")
    st.session_state.progress_loaded = True


# ═════════════════════════════════════════════════════════════════════════════
# WELCOME DISCLAIMER — shown once per login, before the app is usable
# ═════════════════════════════════════════════════════════════════════════════
def render_disclaimer_page():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
        .main { background: linear-gradient(135deg, #0a0e27 0%, #1a1a3e 50%, #0d0f2d 100%); }

        .briefing-title {
            font-family: 'Press Start 2P', monospace;
            font-size: 30px;
            text-align: center;
            color: #ff1493;
            text-shadow: 0 0 10px #00ff88, 0 0 20px #ff1493;
            animation: briefGlow 2s ease-in-out infinite;
            margin-bottom: 4px;
        }
        @keyframes briefGlow {
            0%, 100% { text-shadow: 0 0 10px #00ff88, 0 0 20px #ff1493; }
            50% { text-shadow: 0 0 22px #00ff88, 0 0 40px #ff1493; }
        }

        .briefing-float-row { position: relative; height: 40px; margin-bottom: 8px; }
        .briefing-float-row span {
            position: absolute;
            font-size: 22px;
            animation: briefFloat 3.5s ease-in-out infinite;
        }
        @keyframes briefFloat {
            0%, 100% { transform: translateY(0) rotate(-4deg); }
            50% { transform: translateY(-10px) rotate(4deg); }
        }

        .briefing-card {
            background: linear-gradient(135deg, #1a1a3e 0%, #2d2d5f 100%);
            border: 2px solid #00ff88;
            border-radius: 14px;
            padding: 24px 28px;
            box-shadow: 0 0 25px rgba(0, 255, 136, 0.35);
            animation: briefPulseBorder 2.4s ease-in-out infinite;
        }
        @keyframes briefPulseBorder {
            0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.25); }
            50% { box-shadow: 0 0 35px rgba(255, 20, 147, 0.4); }
        }
        .briefing-card h4 {
            color: #00ffff;
            text-shadow: 0 0 8px #00ffff;
            margin: 0 0 10px 0;
        }
        .briefing-card p, .briefing-card li { color: #e0e0e0; }

        .quest-obj {
            opacity: 0;
            transform: translateX(-16px);
            animation: briefSlideIn 0.5s ease forwards;
            margin: 10px 0;
            padding: 10px 14px;
            border-left: 3px solid #ff1493;
            background: rgba(255, 20, 147, 0.08);
            border-radius: 0 8px 8px 0;
        }
        .quest-obj:nth-child(1) { animation-delay: 0.15s; }
        .quest-obj:nth-child(2) { animation-delay: 0.45s; }
        .quest-obj:nth-child(3) { animation-delay: 0.75s; }
        .quest-obj:nth-child(4) { animation-delay: 1.05s; }
        @keyframes briefSlideIn {
            to { opacity: 1; transform: translateX(0); }
        }

        .briefing-note {
            margin-top: 16px;
            padding: 12px 14px;
            border-radius: 8px;
            background: rgba(0, 255, 255, 0.08);
            border: 1px dashed #00ffff;
            font-size: 13px;
            color: #b8f5ff;
        }

        div[data-testid="stButton"] button[kind="primary"] {
            animation: briefBtnPulse 1.4s ease-in-out infinite;
            font-weight: 700;
        }
        @keyframes briefBtnPulse {
            0%, 100% { box-shadow: 0 0 10px rgba(0, 255, 136, 0.5); }
            50% { box-shadow: 0 0 25px rgba(0, 255, 136, 0.9); }
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="briefing-float-row">'
                '<span style="left:8%; animation-delay:0s;">⚔️</span>'
                '<span style="left:30%; animation-delay:0.6s;">🛡️</span>'
                '<span style="left:52%; animation-delay:1.2s;">💰</span>'
                '<span style="left:74%; animation-delay:0.3s;">🏆</span>'
                '<span style="left:90%; animation-delay:0.9s;">🔮</span>'
                '</div>', unsafe_allow_html=True)
    st.markdown('<div class="briefing-title">📜 QUEST BRIEFING 📜</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#e0e0e0;'>Read your orders, adventurer, before you enter the realm.</p>", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        st.markdown("""
        <div class="briefing-card">
            <h4>🗺️ YOUR MISSION</h4>
            <p>Medallion Data Quest turns a real Bronze/Silver/Gold data pipeline into a game.
            Upload raw data files and the pipeline will guide you through 4 boss battles:</p>
            <div class="quest-obj">🥉 <b>Bronze</b> — profile your data and propose rename/cast rules</div>
            <div class="quest-obj">🥈 <b>Silver</b> — cleanse nulls, dedupe, and cast types (you approve every rule)</div>
            <div class="quest-obj">🥇 <b>Gold</b> — join and aggregate into analytics-ready tables</div>
            <div class="quest-obj">🔮 <b>The Oracle</b> — ask questions in plain English, answered with real SQL over your own data</div>
            <div class="briefing-note">
                ⚡ Your XP, badges, and quest progress are saved to your account.<br>
                🔒 Files stay local on this machine \u2014 only the question/SQL text is sent to the LLM.<br>
                🛠️ Demo-grade auth: fine for local use, not hardened for production.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("✅ OK, LET'S GO!", width='stretch', type="primary"):
            st.session_state.disclaimer_ack = True
            st.rerun()


if not st.session_state.disclaimer_ack:
    render_disclaimer_page()
    st.stop()

QUEST_STAGES = [
    ("🗺️", "Upload"),
    ("🥉", "Bronze"),
    ("🥈", "Silver"),
    ("🥇", "Gold"),
    ("🏆", "Report"),
]
STATUS_TO_STAGE = {
    None: 0,
    "awaiting_bronze_approval": 1,
    "awaiting_silver_approval": 2,
    "awaiting_gold_approval": 3,
    "complete": 4,
}


def render_quest_progress(state: dict | None) -> None:
    """Clickable stage row: past stages can be viewed read-only, current/future can't."""
    status = state["status"] if state else None
    failed = status == "failed"
    current = STATUS_TO_STAGE.get(status, 4 if failed else 0)
    reached_keys = [
        True,
        bool(state and state.get("sttm_bronze_path")),
        bool(state and state.get("sttm_silver_path")),
        bool(state and state.get("sttm_gold_path")),
        bool(state and state.get("report")),
    ]

    st.markdown('<div class="stage-row-wrap">', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (icon, label) in enumerate(QUEST_STAGES):
        reached = reached_keys[i]
        with cols[i]:
            if i == current and not failed:
                btn_type = "primary"
            elif i < current or status == "complete":
                btn_type = "secondary"
            else:
                btn_type = "secondary"
            if st.button(f"{icon} {label}", key=f"stage_btn_{i}", type=btn_type, disabled=not reached, width='stretch'):
                st.session_state.view_stage = i
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_stage_preview(state: dict, stage_idx: int) -> None:
    """Read-only look back at a past stage — no edits, just a peek."""
    icon, label = QUEST_STAGES[stage_idx]
    st.markdown('<div class="phase-card">', unsafe_allow_html=True)
    header_col, close_col = st.columns([5, 1])
    with header_col:
        st.markdown(f"### {icon} Viewing: {label} (read-only)")
    with close_col:
        if st.button("✖ Close", key="close_preview", width='stretch'):
            st.session_state.view_stage = None
            st.rerun()

    if stage_idx == 0:
        st.markdown(f"**Quest Objective:** {state.get('business_intent', '')}")
        st.markdown("**Uploaded files:**")
        for p in state.get("uploaded_files", []):
            st.caption(f"📄 {Path(p).name}")
        profile_path = state.get("profile_path")
        if profile_path and Path(profile_path).exists():
            profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
            st.markdown("**Quality notes:**")
            for note in profile.get("quality_notes", []) or ["None"]:
                st.caption(f"• {note}")
    elif stage_idx in (1, 2, 3):
        sttm_key = {1: "sttm_bronze_path", 2: "sttm_silver_path", 3: "sttm_gold_path"}[stage_idx]
        output_key = {1: "bronze_output_paths", 2: "silver_output_paths", 3: "gold_output_paths"}[stage_idx]
        sttm_path = state.get(sttm_key)
        if sttm_path and Path(sttm_path).exists():
            st.markdown("**Approved transformation rules:**")
            st.dataframe(pd.read_csv(sttm_path), width='stretch', hide_index=True)
        for p in state.get(output_key, []) or []:
            try:
                df = pd.read_parquet(p)
                with st.expander(f"🏺 {Path(p).stem} ({len(df):,} rows)"):
                    st.dataframe(df.head(20), width='stretch', hide_index=True)
            except Exception:
                pass
    elif stage_idx == 4:
        report = state.get("report", {})
        if report:
            st.success(safe_md(report.get("answer", "")))
            if report.get("sql"):
                with st.expander("View SQL"):
                    st.code(report["sql"], language="sql")

    st.markdown('</div>', unsafe_allow_html=True)

PHASE_TIPS = {
    None: ("🗺️", "Upload your data scrolls (CSVs) and state your quest objective to begin."),
    "awaiting_bronze_approval": ("🥉", "Review the rename/cast rules below, then strike to defeat the Bronze Guardian."),
    "awaiting_silver_approval": ("🥈", "Check the null-handling & dedup rules, then strike down the Silver Sentinel."),
    "awaiting_gold_approval": ("🥇", "Confirm the join/aggregate rules, then finish the Gold Dragon for good."),
    "complete": ("🏆", "Quest complete! Consult the Oracle below to ask follow-up questions about your treasure."),
    "failed": ("💀", "The quest was interrupted. Check the error above, then start a new adventure."),
}


def _save_uploads(files) -> tuple:
    run_id = uuid.uuid4().hex[:12]
    out_dir = LANDING_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for f in files:
        path = out_dir / f.name
        path.write_bytes(f.getvalue())
        paths.append(str(path))
    return run_id, paths


def add_xp(amount):
    st.session_state.xp += amount
    st.session_state.level = 1 + (st.session_state.xp // 500)


def add_achievement(name):
    if name not in st.session_state.achievements:
        st.session_state.achievements.append(name)


def safe_md(text: str) -> str:
    """Escape $ so Streamlit doesn't mis-parse dollar amounts as LaTeX math delimiters."""
    return (text or "").replace("$", "\\$")


def reset_quest():
    st.session_state.state = None
    st.session_state.xp = 0
    st.session_state.level = 1
    st.session_state.achievements = []
    st.session_state.oracle_answer = None
    st.session_state.oracle_query_count = 0
    st.session_state.oracle_prompted = False
    st.session_state.show_restart_prompt = False
    st.session_state.view_stage = None


def persist_progress():
    """Save this account's quest state to disk so it's there next time they log in."""
    if not st.session_state.get("username"):
        return
    state_copy = None
    if st.session_state.state:
        state_copy = dict(st.session_state.state)
        if state_copy.get("report"):
            state_copy["report"] = {k: v for k, v in state_copy["report"].items() if k != "chart"}
    oracle_copy = None
    if st.session_state.oracle_answer:
        oracle_copy = {k: v for k, v in st.session_state.oracle_answer.items() if k != "chart"}
    save_progress(st.session_state.username, {
        "xp": st.session_state.xp,
        "level": st.session_state.level,
        "achievements": st.session_state.achievements,
        "oracle_query_count": st.session_state.oracle_query_count,
        "oracle_prompted": st.session_state.oracle_prompted,
        "state": state_copy,
        "oracle_answer": oracle_copy,
    })


# ═════════════════════════════════════════════════════════════════════════════
# EPIC GAMING STYLES
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    
    * {
        font-family: 'Arial', sans-serif;
    }
    
    .main { background: linear-gradient(135deg, #0a0e27 0%, #1a1a3e 50%, #0d0f2d 100%); }
    
    /* Arcade/Gaming Title */
    .arcade-title {
        font-family: 'Press Start 2P', monospace;
        font-size: 48px;
        color: #ff1493;
        text-shadow: 0 0 10px #00ff88, 0 0 20px #ff1493;
        text-align: center;
        margin: 20px 0;
        animation: glow 2s ease-in-out infinite;
        letter-spacing: 2px;
    }
    
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 10px #00ff88, 0 0 20px #ff1493; }
        50% { text-shadow: 0 0 20px #00ff88, 0 0 40px #ff1493; }
    }
    
    /* Sidebar Gaming */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1a1a3e 0%, #2d2d5f 100%);
        border-right: 3px solid #ff1493;
        box-shadow: -5px 0 20px rgba(255, 20, 147, 0.3);
    }
    [data-testid="stSidebar"] * { color: #00ff88 !important; }
    
    /* Header */
    .quest-header {
        background: linear-gradient(135deg, #ff1493 0%, #00ff88 100%);
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        margin: -16px -16px 24px -16px;
        text-align: center;
    }
    
    .quest-header h1 {
        font-family: 'Press Start 2P', monospace;
        color: #0a0e27;
        margin: 0;
        font-size: 32px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .quest-header p {
        color: #0a0e27;
        font-weight: bold;
        margin: 0;
    }
    
    /* Stats Panel */
    .stats-panel {
        background: linear-gradient(135deg, #ff1493 0%, #ff69b4 100%);
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #00ff88;
        box-shadow: 0 0 20px rgba(255, 20, 147, 0.4);
        margin: 15px 0;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        margin: 10px 0;
        font-weight: bold;
        color: #0a0e27;
    }
    
    .xp-bar {
        background: rgba(0, 255, 136, 0.2);
        border-radius: 4px;
        overflow: hidden;
        height: 20px;
        border: 2px solid #00ff88;
    }
    
    .xp-fill {
        height: 100%;
        background: linear-gradient(90deg, #00ff88 0%, #00ffff 100%);
        animation: glow-bar 1s ease-in-out infinite;
    }
    
    @keyframes glow-bar {
        0%, 100% { box-shadow: 0 0 10px #00ff88 inset; }
        50% { box-shadow: 0 0 20px #00ffff inset; }
    }
    
    /* Boss Encounter / Approval Gate */
    .boss-encounter {
        background: linear-gradient(135deg, #8b0000 0%, #ff4500 100%);
        padding: 25px;
        border-radius: 12px;
        border: 3px dashed #ff1493;
        box-shadow: 0 0 30px rgba(255, 69, 0, 0.6);
        text-align: center;
        margin: 20px 0;
        animation: shake 0.5s infinite;
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    .boss-encounter h3 {
        color: #ff1493;
        font-family: 'Press Start 2P', monospace;
        margin: 0 0 15px 0;
        font-size: 20px;
        text-shadow: 0 0 10px #ff1493;
    }
    
    .boss-health {
        background: rgba(0, 0, 0, 0.5);
        border: 2px solid #ff1493;
        border-radius: 6px;
        height: 30px;
        margin: 15px 0;
        overflow: hidden;
    }
    
    .boss-health-fill {
        height: 100%;
        background: linear-gradient(90deg, #ff1493 0%, #ff69b4 100%);
        transition: width 0.5s ease;
        animation: pulse 1s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Content Card */
    .phase-card {
        background: linear-gradient(135deg, #1a2a4e 0%, #2d2d5f 100%);
        padding: 30px;
        border-radius: 12px;
        border: 2px solid #00ff88;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        animation: fadeInUp 0.6s ease;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .phase-card h2 {
        color: #00ff88;
        font-family: 'Press Start 2P', monospace;
        font-size: 24px;
        margin: 0 0 15px 0;
        text-shadow: 0 0 10px #00ff88;
    }
    
    .phase-card h3 {
        color: #00ffff;
        margin: 15px 0 10px 0;
    }
    
    .phase-card p, .phase-card label, .phase-card small {
        color: #e0e0e0;
    }
    
    /* Buttons */
    .approve-btn {
        background: linear-gradient(135deg, #00ff88 0%, #00ffcc 100%);
        color: #0a0e27;
        border: 2px solid #00ff88;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 700;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.5);
    }
    
    .approve-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 0 25px rgba(0, 255, 136, 0.8);
        text-shadow: 0 0 10px #00ff88;
    }
    
    .reject-btn {
        background: linear-gradient(135deg, #ff4500 0%, #ff1493 100%);
        color: white;
        border: 2px solid #ff1493;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 700;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 0 15px rgba(255, 69, 0, 0.5);
    }
    
    .reject-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 0 25px rgba(255, 69, 0, 0.8);
    }
    
    /* Chat Panel */
    .chat-container {
        background: linear-gradient(135deg, #1a1a3e 0%, #2d2d5f 100%);
        border-radius: 12px;
        border: 2px solid #00ff88;
        display: flex;
        flex-direction: column;
        height: 600px;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
    }
    
    .chat-header {
        padding: 16px;
        border-bottom: 2px solid #00ff88;
        font-weight: 700;
        color: #00ff88;
        font-family: 'Press Start 2P', monospace;
        font-size: 14px;
        text-shadow: 0 0 10px #00ff88;
    }
    
    .chat-messages {
        flex: 1;
        min-height: 0;
        max-height: 520px;
        overflow: hidden;
        padding: 16px;
    }
    .chat-messages:hover .log-track {
        animation-play-state: paused;
    }
    .log-track {
        animation: scrollLog linear infinite;
    }
    @keyframes scrollLog {
        0% { transform: translateY(0); }
        100% { transform: translateY(-50%); }
    }
    
    .chat-message {
        margin: 12px 0;
        animation: slideIn 0.4s ease;
    }
    
    .chat-message.user .msg {
        background: linear-gradient(135deg, #ff1493 0%, #ff69b4 100%);
        color: white;
        display: inline-block;
        max-width: 85%;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 13px;
        box-shadow: 0 0 10px rgba(255, 20, 147, 0.4);
    }
    
    .chat-message.assistant .msg {
        background: linear-gradient(135deg, #00ff88 0%, #00ffcc 100%);
        color: #0a0e27;
        display: inline-block;
        max-width: 85%;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.4);
    }
    
    .chat-message.user {
        text-align: right;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Achievement Badge */
    .achievement {
        display: inline-block;
        background: linear-gradient(135deg, #00d4ff 0%, #7b2ff7 100%);
        color: #ffffff;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin: 5px;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        border: 2px solid #00d4ff;
    }
    
    /* Data Table */
    .phase-card table { color: #e0e0e0; }
    .phase-card [data-testid="stDataFrame"] { background: rgba(0, 255, 136, 0.1) !important; }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #ff1493 0%, #00ff88 100%);
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    /* Quest Stage Buttons (clickable progress bar) */
    .stage-row-wrap {
        background: linear-gradient(135deg, #1a1a3e 0%, #2d2d5f 100%);
        border: 2px solid #00ff88;
        border-radius: 12px;
        padding: 12px 16px 4px 16px;
        margin: 0 0 24px 0;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.25);
    }
    .stage-row-wrap div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
    }
    .stage-row-wrap div[data-testid="stButton"] button:disabled {
        opacity: 0.35;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .arcade-title { font-size: 24px; }
        .phase-card h2 { font-size: 18px; }
    }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# LEFT SIDEBAR: QUEST STATS
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="quest-header"><h1>⚔️ QUEST</h1><p>Medallion Data Wars</p></div>', unsafe_allow_html=True)

    acc_col, logout_col = st.columns([2, 1])
    with acc_col:
        st.markdown(f"👤 **{st.session_state.username}**")
    with logout_col:
        if st.button("Logout", width='stretch'):
            persist_progress()
            st.session_state.username = None
            st.session_state.progress_loaded = False
            st.session_state.disclaimer_ack = False
            st.rerun()

    # Stats Panel — XP bar always shows progress WITHIN the current level (0-500)
    xp_into_level = st.session_state.xp % 500
    xp_to_next = 500 - xp_into_level
    st.markdown(f"""
    <div class="stats-panel">
        <div class="stat-row">
            <span>LEVEL:</span>
            <span style="color: #00ff88; text-shadow: 0 0 10px #00ff88;">{st.session_state.level}</span>
        </div>
        <div class="stat-row">
            <span>XP:</span>
            <span>{xp_into_level} / 500</span>
        </div>
        <div class="xp-bar">
            <div class="xp-fill" style="width: {xp_into_level / 5}%"></div>
        </div>
        <div class="stat-row" style="margin-top: 15px;">
            <span>ACHIEVEMENTS:</span>
            <span style="color: #ffd700;">{len(st.session_state.achievements)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"⚡ {xp_to_next} XP to Level {st.session_state.level + 1}. Levels have no cap — keep asking the Oracle (+25 XP each) after your quest completes!")
    
    if st.session_state.achievements:
        st.markdown("### 🏆 Unlocked Badges")
        for achievement in st.session_state.achievements:
            st.markdown(f'<div class="achievement">{achievement}</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # AI Status
    if is_llm_configured():
        st.markdown('🤖 **AI Ready** · Groq Engine Loaded')
    else:
        st.error('❌ AI Engine Offline')
    
    st.divider()
    
    # Progress
    if st.session_state.state:
        state = st.session_state.state
        st.markdown(f"📍 **Run ID:** `{state['run_id'][:8]}`")
        if st.button("🔄 New Adventure", width='stretch'):
            reset_quest()
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN QUEST AREA + CHAT
# ═════════════════════════════════════════════════════════════════════════════
col_main, col_chat = st.columns([3.5, 1.2], gap="small")

with col_main:
    st.markdown('<h1 class="arcade-title">🎮 MEDALLION DATA QUEST 🎮</h1>', unsafe_allow_html=True)
    render_quest_progress(st.session_state.state)

    if st.session_state.state and st.session_state.view_stage is not None:
        render_stage_preview(st.session_state.state, st.session_state.view_stage)

    if st.session_state.state is None:
        # QUEST START
        st.markdown('<div class="phase-card">', unsafe_allow_html=True)
        st.markdown('### 🗡️ START YOUR QUEST')
        st.markdown('Prepare your data scrolls and embark on an epic transformation journey!')
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('#### 📜 Upload Data Scrolls')
            uploaded = st.file_uploader(
                "Choose your data scrolls",
                type=["csv", "tsv", "txt", "xlsx", "xls", "json", "parquet"],
                accept_multiple_files=True,
                label_visibility="collapsed",
            )
            st.caption("Supported: CSV, TSV, TXT, Excel (.xlsx/.xls), JSON, Parquet")
            if uploaded:
                st.success(f'⚔️ {len(uploaded)} scrolls ready for battle!')
                for f in uploaded:
                    st.caption(f"📄 {f.name}")
        
        with col2:
            st.markdown('#### 🎯 Quest Objective')
            business_intent = st.text_area(
                "What is your mission?",
                value="Transform raw retail data into actionable business intelligence",
                height=150,
                label_visibility="collapsed",
            )
        
        st.markdown('---')
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown('#### 🚀 BEGIN QUEST')
        with col2:
            if st.button("⚡ START EPIC ADVENTURE ⚡", width='stretch', disabled=not uploaded):
                if uploaded:
                    with st.spinner("⏳ Loading quest... Summoning data spirits..."):
                        run_id, file_paths = _save_uploads(uploaded)
                        state = start_pipeline(file_paths, business_intent, run_id)
                    st.session_state.state = state
                    add_xp(100)
                    add_achievement("Data Collector")
                    if state.get("status") == "awaiting_bronze_approval":
                        st.success("✅ PHASE 1: Bronze Layer Awaits Your Approval!")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        state = st.session_state.state
        
        if state["status"] == "failed":
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)
            st.error(f'💀 QUEST FAILED: {", ".join(state.get("errors", ["Unknown"]))}')
            st.markdown('</div>', unsafe_allow_html=True)
        
        # PHASE 1: BRONZE BOSS
        if state["status"] in ("awaiting_bronze_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter">', unsafe_allow_html=True)
            st.markdown('### 🥉 BOSS: BRONZE GUARDIAN')
            st.markdown('*Defeat this boss by reviewing and approving the Bronze transformation rules!*')
            
            # Boss Health
            st.markdown("""
            <div class="boss-health">
                <div class="boss-health-fill" style="width: 100%"></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("📊 Analyze Data Profile", expanded=False):
                try:
                    profile = json.loads(Path(state["profile_path"]).read_text(encoding="utf-8"))
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown('**Files Scanned:**')
                        for fname, info in profile.get("files", {}).items():
                            st.caption(f"📄 {fname}: {info['row_count']:,} rows")
                    with col2:
                        st.markdown('**Discovered Keys:**')
                        if profile.get("join_keys"):
                            for jk in profile.get("join_keys", []):
                                st.caption(f"`{jk['column']}`")
                except: pass
            
            st.markdown('### ⚔️ Review Transformation Spells')
            try:
                sttm_df = pd.read_csv(state["sttm_bronze_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="bronze", hide_index=False)
            except Exception as e:
                st.error(f"Error loading spells: {e}")
                edited = None
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Defeat this boss to level up and proceed!")
            with col2:
                if st.button("⚡ DEFEAT BOSS ⚡", key="bronze_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_bronze_path"], index=False)
                    with st.spinner("🔥 Crushing the Bronze Guardian..."):
                        st.session_state.state = approve_bronze(state)
                    add_xp(250)
                    add_achievement("Bronze Slayer")
                    st.success("🎉 VICTORY! You've defeated the Bronze Guardian!")
                    st.rerun()
            with col3:
                if st.button("💀 FLEE QUEST", key="bronze_reject", width='stretch'):
                    st.session_state.state = None
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # PHASE 2: SILVER BOSS
        if state["status"] in ("awaiting_silver_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter">', unsafe_allow_html=True)
            st.markdown('### 🥈 BOSS: SILVER SENTINEL')
            st.markdown('*The Silver Sentinel guards the cleansing layer. Prove your worth!*')
            st.markdown("""
            <div class="boss-health">
                <div class="boss-health-fill" style="width: 75%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("📦 Preview Bronze Achievements", expanded=False):
                for p in state.get("bronze_output_paths", []):
                    try:
                        df = pd.read_parquet(p)
                        st.markdown(f"**{Path(p).name}** ({len(df):,} rows)")
                        st.dataframe(df.head(3), width='stretch', hide_index=True)
                    except: pass
            
            st.markdown('### ⚔️ Review Cleansing Spells')
            try:
                sttm_df = pd.read_csv(state["sttm_silver_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="silver", hide_index=False)
            except: edited = None
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Defeat this boss to advance your quest!")
            with col2:
                if st.button("⚡ DEFEAT BOSS ⚡", key="silver_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_silver_path"], index=False)
                    with st.spinner("💨 Vanquishing the Silver Sentinel..."):
                        st.session_state.state = approve_silver(state)
                    add_xp(250)
                    add_achievement("Silver Master")
                    st.success("🎉 VICTORY! The Silver Sentinel falls!")
                    st.rerun()
            with col3:
                if st.button("💀 FLEE QUEST", key="silver_reject", width='stretch'):
                    st.session_state.state = None
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # PHASE 3: GOLD BOSS
        if state["status"] in ("awaiting_gold_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter">', unsafe_allow_html=True)
            st.markdown('### 🥇 BOSS: GOLD DRAGON')
            st.markdown('*The final boss! Defeat the Gold Dragon to unlock the treasure!*')
            st.markdown("""
            <div class="boss-health">
                <div class="boss-health-fill" style="width: 50%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("📦 Preview Silver Achievements", expanded=False):
                for p in state.get("silver_output_paths", []):
                    try:
                        df = pd.read_parquet(p)
                        st.markdown(f"**{Path(p).name}** ({len(df):,} rows)")
                        st.dataframe(df.head(3), width='stretch', hide_index=True)
                    except: pass
            
            st.markdown('### ⚔️ Review Analytics Spells')
            try:
                sttm_df = pd.read_csv(state["sttm_gold_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="gold", hide_index=False)
            except: edited = None
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Defeat the Gold Dragon to claim victory!")
            with col2:
                if st.button("⚡ DEFEAT FINAL BOSS ⚡", key="gold_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_gold_path"], index=False)
                    with st.spinner("🔥🐉💥 Epic final battle... The Gold Dragon falls!"):
                        st.session_state.state = approve_gold(state)
                    add_xp(500)
                    add_achievement("Dragon Slayer")
                    add_achievement("Quest Master")
                    st.success("🎉🎉🎉 VICTORY! You've conquered the Medallion Realm!")
                    st.rerun()
            with col3:
                if st.button("💀 FLEE QUEST", key="gold_reject", width='stretch'):
                    st.session_state.state = None
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # PHASE 4: TREASURE & REWARDS
        if state["status"] == "complete":
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)

            # Surprise reward reveal — shown once per run, right when the quest is completed
            if st.session_state.get("celebrated_run") != state["run_id"]:
                st.session_state.celebrated_run = state["run_id"]
                st.balloons()
                st.markdown(f"""
                <div class="boss-encounter" style="animation: none; border-style: solid;">
                    <h3>🎁 SURPRISE! TREASURE CHEST UNLOCKED 🎁</h3>
                    <p style="color: white; font-size: 16px; margin: 10px 0;">
                        You earned <b>{st.session_state.xp} XP</b> and unlocked
                        <b>{len(st.session_state.achievements)} badges</b> this quest!
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('# 🏆 QUEST COMPLETE! 🏆')
            st.markdown('### 💎 You have successfully claimed the treasure!')
            
            report = state.get("report", {})
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown('#### 📊 THE TREASURE (Your Answer)')
                st.markdown(f'**Quest Objective:** {state["business_intent"]}')
                st.success(safe_md(report.get("answer", "Treasure loading...")))
            
            with col2:
                if report.get("chart"):
                    st.plotly_chart(report["chart"], width='stretch')
            
            st.divider()
            
            st.markdown('#### 📈 Analytics Chambers')
            for p in state.get("gold_output_paths", []):
                try:
                    df = pd.read_parquet(p)
                    with st.expander(f"🏺 {Path(p).stem}"):
                        st.dataframe(df, width='stretch', hide_index=True)
                except: pass
            
            st.divider()
            
            st.markdown('#### 🔧 Forge Logs')
            tab1, tab2, tab3 = st.tabs(["SQL Spell", "Traces", "Audit"])
            with tab1:
                if report.get("sql"):
                    st.code(report["sql"], language="sql")
            with tab2:
                trace_dir = BASE_DIR / "data" / "traces"
                if trace_dir.exists():
                    for tf in sorted(trace_dir.glob(f"trace_*_{state['run_id'][:8]}.json")):
                        with st.expander(f"🔍 {tf.name}"):
                            try:
                                st.json(json.loads(tf.read_text()))
                            except: pass
            with tab3:
                audit_path = BASE_DIR / "audit_logs" / f"{state['run_id']}.jsonl"
                if audit_path.exists():
                    try:
                        entries = [json.loads(l) for l in audit_path.read_text().splitlines()]
                        st.dataframe(pd.DataFrame(entries), width='stretch', hide_index=True)
                    except: pass
            
            st.divider()
            st.download_button(
                "💾 Download Quest Report",
                data=json.dumps(state, indent=2, default=str),
                file_name=f"quest_{state['run_id']}.json",
                mime="application/json",
                width='stretch',
            )
            
            st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL: LIVE MISSION LOG + ASK THE ORACLE
# ═════════════════════════════════════════════════════════════════════════════
with col_chat:
    state = st.session_state.state
    status = state["status"] if state else None
    icon, tip = PHASE_TIPS.get(status, PHASE_TIPS[None])

    # Build the whole log as one HTML string — avoids Streamlit's markdown-call
    # nesting quirks that made this panel render blank before.
    log_items = [f'<div class="chat-message assistant"><div class="msg">{icon} {tip}</div></div>']

    if state:
        audit_path = BASE_DIR / "audit_logs" / f"{state['run_id']}.jsonl"
        if audit_path.exists():
            try:
                entries = [json.loads(l) for l in audit_path.read_text(encoding="utf-8").splitlines() if l.strip()]
            except Exception:
                entries = []
            for entry in reversed(entries[-8:]):
                action = entry.get("action", "")
                ok = "failed" not in action
                badge = "✅" if ok else "💥"
                ts = entry.get("timestamp", "")[11:19]
                label = action.replace("_", " ").title()
                log_items.append(
                    f'<div class="chat-message assistant"><div class="msg">{badge} {label}'
                    f'<br><small style="opacity:0.6">{ts} UTC</small></div></div>'
                )
        else:
            log_items.append('<div class="chat-message assistant"><div class="msg">⏳ No events logged yet for this run.</div></div>')

    st.markdown(
        '<div class="chat-container"><div class="chat-header">📜 MISSION LOG</div>'
        f'<div class="chat-messages"><div class="log-track" style="animation-duration: {max(10, len(log_items) * 4)}s">'
        f'{"".join(log_items)}{"".join(log_items)}'
        '</div></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 🔮 Ask the Data Oracle")
    gold_paths = state.get("gold_output_paths") if state else None

    if not gold_paths:
        st.caption("🔒 Unlocks after you defeat the Gold Dragon. Uses exactly 1 AI call per question — no token waste.")
    elif st.session_state.show_restart_prompt:
        st.warning("🧭 You've asked 5 questions! Start a fresh adventure, or keep exploring this one?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("🔄 Yes, New Adventure", width='stretch'):
                reset_quest()
                st.rerun()
        with col_no:
            if st.button("🙅 No, Keep Exploring", width='stretch'):
                st.session_state.show_restart_prompt = False
                st.session_state.oracle_prompted = False  # allows the nudge to re-trigger after 5 more questions
                st.rerun()
    else:
        oracle_q = st.text_input(
            "Ask a question about your treasure...", placeholder="e.g. Which region has the highest revenue?",
            key="oracle_input", label_visibility="collapsed",
        )
        if st.button("🔮 Consult the Oracle", width='stretch', disabled=not oracle_q):
            with st.spinner("🔮 The Oracle is reading the runes (1 AI call)..."):
                try:
                    st.session_state.oracle_answer = ask_question(gold_paths, oracle_q, state["run_id"])
                    add_xp(25)
                    st.session_state.oracle_query_count += 1
                except Exception as exc:
                    st.session_state.oracle_answer = {"answer": f"⚠️ The Oracle is silent: {exc}", "sql": None, "rows": [], "chart": None}
            if st.session_state.oracle_query_count > 0 and st.session_state.oracle_query_count % 5 == 0 and not st.session_state.oracle_prompted:
                st.session_state.show_restart_prompt = True
                st.session_state.oracle_prompted = True
            st.rerun()

        if st.session_state.oracle_answer:
            ans = st.session_state.oracle_answer
            st.info(safe_md(ans["answer"]))
            if ans.get("sql"):
                with st.expander("View SQL"):
                    st.code(ans["sql"], language="sql")
            if ans.get("chart"):
                st.plotly_chart(ans["chart"], width='stretch')
            elif ans.get("rows"):
                st.dataframe(pd.DataFrame(ans["rows"]), width='stretch', hide_index=True)

# Save this account's progress on every rerun so it survives logout/browser close.
persist_progress()
