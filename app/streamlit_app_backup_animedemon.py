"""
⚔️ DEMON HUNTER: DATA BREATHING CORPS ⚔️
A Demon-Slayer-inspired gamified Streamlit pipeline for epic data transformations.
"""
import json
import sys
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
    page_title="⚔️ Demon Hunter: Data Corps",
    page_icon="⚡",
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
if "fx_trigger" not in st.session_state:
    st.session_state.fx_trigger = None
if "username" not in st.session_state:
    st.session_state.username = None
if "progress_loaded" not in st.session_state:
    st.session_state.progress_loaded = False
if "disclaimer_ack" not in st.session_state:
    st.session_state.disclaimer_ack = False


# ═════════════════════════════════════════════════════════════════════════════
# ACCOUNT LOGIN — a Mortal-Kombat-style "choose your fighter" character select
# (Original CSS/SVG silhouettes only — no copyrighted character art is used.)
# ═════════════════════════════════════════════════════════════════════════════
def render_login_page():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Yuji+Mai&family=Cinzel:wght@600;800&display=swap');
        .main {
            background:
                radial-gradient(circle at 50% 40%, transparent 0%, rgba(0,0,0,0.6) 100%),
                radial-gradient(circle at 10% 20%, rgba(20,100,50,0.18) 0%, transparent 40%),
                radial-gradient(circle at 90% 20%, rgba(255,20,110,0.16) 0%, transparent 40%),
                linear-gradient(135deg, #050305 0%, #0e070d 45%, #06040a 100%);
        }
        .select-title {
            font-family: 'Yuji Mai', serif;
            font-size: 42px;
            text-align: center;
            color: #ff5722;
            letter-spacing: 4px;
            text-shadow: 0 0 14px #ff3d00, 0 0 30px rgba(255,61,0,0.6);
            animation: selGlow 3s ease-in-out infinite;
            margin-bottom: 0;
        }
        @keyframes selGlow {
            0%, 100% { text-shadow: 0 0 14px #ff3d00, 0 0 30px rgba(255,61,0,0.6); color: #ff5722; }
            50% { text-shadow: 0 0 18px #29b6f6, 0 0 34px rgba(41,182,246,0.6); color: #4fc3f7; }
        }
        .select-sub {
            text-align: center; color: #e8dcc8; letter-spacing: 2px; font-size: 13px;
            margin-bottom: 18px; text-transform: uppercase;
        }

        /* Fighter pedestal */
        .fighter-pedestal { text-align: center; padding: 10px 6px 0 6px; position: relative; }
        .fighter-name {
            font-family: 'Yuji Mai', serif; font-size: 20px; margin-top: 10px;
            letter-spacing: 1px;
        }
        .fighter-tag { font-size: 11px; color: #cfc3ab; letter-spacing: 1px; text-transform: uppercase; }

        .silhouette { width: 130px; height: 210px; margin: 0 auto; position: relative; }
        .sil-head { width: 52px; height: 52px; border-radius: 50%; margin: 0 auto;
            background: radial-gradient(circle at 35% 30%, #3a3a3a, #0a0a0a 70%); }
        .sil-body { width: 96px; height: 140px; margin: -6px auto 0; border-radius: 46% 46% 18% 18%; }

        .tanjiro-body {
            background: repeating-linear-gradient(45deg, #0d3d20 0 12px, #0a0a0a 12px 24px);
            box-shadow: 0 0 26px rgba(20, 160, 70, 0.55), inset 0 0 20px rgba(0,0,0,0.5);
            animation: tanjiroAura 2.4s ease-in-out infinite;
        }
        @keyframes tanjiroAura {
            0%, 100% { box-shadow: 0 0 20px rgba(20,160,70,0.45); }
            50% { box-shadow: 0 0 36px rgba(20,160,70,0.85), 0 0 16px rgba(255,80,20,0.4); }
        }
        .nezuko-body {
            background: linear-gradient(160deg, #ff8fb3 0%, #ff1e6e 55%, #7a0d33 100%);
            box-shadow: 0 0 26px rgba(255, 30, 110, 0.55), inset 0 0 20px rgba(0,0,0,0.35);
            animation: nezukoAura 2.4s ease-in-out infinite;
        }
        @keyframes nezukoAura {
            0%, 100% { box-shadow: 0 0 20px rgba(255,30,110,0.45); }
            50% { box-shadow: 0 0 36px rgba(255,30,110,0.85), 0 0 16px rgba(255,255,255,0.35); }
        }
        .sil-obi { position: absolute; left: 50%; top: 128px; transform: translateX(-50%);
            width: 96px; height: 14px; background: rgba(0,0,0,0.35); border-radius: 3px; }

        .pedestal-base {
            width: 150px; height: 14px; margin: 6px auto 0; border-radius: 50%;
            filter: blur(1px); opacity: 0.8;
        }
        .tanjiro-base { background: radial-gradient(ellipse, rgba(20,160,70,0.7), transparent 70%); }
        .nezuko-base { background: radial-gradient(ellipse, rgba(255,30,110,0.7), transparent 70%); }

        /* Floating particles per side */
        .particle-col { position: relative; height: 0; }
        .p-ember { position: absolute; font-size: 13px; opacity: 0.7; animation: pRise 4s ease-in-out infinite; }
        .p-petal { position: absolute; font-size: 13px; opacity: 0.7; animation: pDrift 5s ease-in-out infinite; }
        @keyframes pRise { 0% { transform: translateY(0); opacity: 0; } 20% { opacity: 0.8; } 100% { transform: translateY(-160px); opacity: 0; } }
        @keyframes pDrift { 0% { transform: translateY(0) translateX(0) rotate(0deg); opacity: 0; } 20% { opacity: 0.8; } 100% { transform: translateY(-160px) translateX(18px) rotate(120deg); opacity: 0; } }

        /* Center console */
        .console-panel {
            background: linear-gradient(135deg, #140a12 0%, #1c1220 100%);
            border: 2px solid #d4af37;
            border-radius: 14px;
            padding: 22px 26px 10px 26px;
            box-shadow: 0 0 28px rgba(212, 175, 55, 0.3);
        }
        .vs-badge {
            text-align: center; font-family: 'Yuji Mai', serif; font-size: 26px;
            color: #d4af37; text-shadow: 0 0 12px rgba(212,175,55,0.8);
            margin: 6px 0 2px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="select-title">⚔️ DEMON HUNTER: DATA CORPS ⚔️</div>', unsafe_allow_html=True)
    st.markdown('<div class="select-sub">Choose your path \u2014 the Corps awaits</div>', unsafe_allow_html=True)

    left, mid, right = st.columns([1, 1.5, 1])

    with left:
        st.markdown("""
        <div class="fighter-pedestal">
            <div class="particle-col">
                <span class="p-ember" style="left:20%; animation-delay:0s;">🔥</span>
                <span class="p-ember" style="left:60%; animation-delay:1.3s;">🔥</span>
                <span class="p-ember" style="left:40%; animation-delay:2.6s;">🔥</span>
            </div>
            <div class="silhouette">
                <div class="sil-head"></div>
                <div class="sil-body tanjiro-body"><div class="sil-obi"></div></div>
            </div>
            <div class="pedestal-base tanjiro-base"></div>
            <div class="fighter-name" style="color:#4caf50;">🌊 TANJIRO</div>
            <div class="fighter-tag">Water Breathing User</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="fighter-pedestal">
            <div class="particle-col">
                <span class="p-petal" style="left:20%; animation-delay:0.5s;">🌸</span>
                <span class="p-petal" style="left:55%; animation-delay:1.8s;">🌸</span>
                <span class="p-petal" style="left:38%; animation-delay:3.1s;">🌸</span>
            </div>
            <div class="silhouette">
                <div class="sil-head"></div>
                <div class="sil-body nezuko-body"><div class="sil-obi"></div></div>
            </div>
            <div class="pedestal-base nezuko-base"></div>
            <div class="fighter-name" style="color:#ff5c93;">🌸 NEZUKO</div>
            <div class="fighter-tag">Blood Demon Art</div>
        </div>
        """, unsafe_allow_html=True)

    with mid:
        st.markdown('<div class="console-panel">', unsafe_allow_html=True)
        st.markdown('<div class="vs-badge">— ENTER THE CORPS —</div>', unsafe_allow_html=True)
        tab_login, tab_signup = st.tabs(["🔑 Login", "🛡️ Enlist"])
        with tab_login:
            u = st.text_input("Username", key="login_user")
            p = st.text_input("Password", type="password", key="login_pass")
            if st.button("⚔️ Enter the Corps", width='stretch', type="primary"):
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
            if st.button("🛡️ Enlist Now", width='stretch', type="primary"):
                err = register_user(nu, np_)
                if err:
                    st.error(err)
                else:
                    st.success("Enlisted! Switch to the Login tab to enter.")
        st.markdown('</div>', unsafe_allow_html=True)


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
                '<span style="left:30%; animation-delay:0.6s;">�</span>'
                '<span style="left:52%; animation-delay:1.2s;">💧</span>'
                '<span style="left:74%; animation-delay:0.3s;">☀️</span>'
                '<span style="left:90%; animation-delay:0.9s;">🐦</span>'
                '</div>', unsafe_allow_html=True)
    st.markdown('<div class="briefing-title">⛩️ CORPS BRIEFING ⛩️</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#e8dcc8;'>Read your orders, demon hunter, before you begin training.</p>", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
        st.markdown("""
        <div class="briefing-card">
            <h4>⚔️ YOUR MISSION</h4>
            <p>Demon Hunter: Data Corps turns a real Bronze/Silver/Gold data pipeline into a training arc.
            Upload raw data files and progress through 4 breathing trials:</p>
            <div class="quest-obj">💧 <b>Water Breathing (Bronze)</b> — profile your data and propose rename/cast rules</div>
            <div class="quest-obj">🔥 <b>Flame Breathing (Silver)</b> — cleanse nulls, dedupe, and cast types (you approve every rule)</div>
            <div class="quest-obj">☀️ <b>Sun Breathing (Gold)</b> — join and aggregate into analytics-ready tables</div>
            <div class="quest-obj">🐦 <b>The Kasugai Crow</b> — ask questions in plain English, answered with real SQL over your own data</div>
            <div class="briefing-note">
                ⚡ Your XP, rank, and progress are saved to your account.<br>
                🔒 Files stay local on this machine \u2014 only the question/SQL text is sent to the LLM.<br>
                🛠️ Demo-grade auth: fine for local use, not hardened for production.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("✅ OK, BEGIN TRAINING!", width='stretch', type="primary"):
            st.session_state.disclaimer_ack = True
            st.rerun()


if not st.session_state.disclaimer_ack:
    render_disclaimer_page()
    st.stop()

QUEST_STAGES = [
    ("⚔️", "Recruit"),
    ("💧", "Water"),
    ("🔥", "Flame"),
    ("☀️", "Sun"),
    ("🐦", "Verdict"),
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
        st.markdown(f"**Mission Objective:** {state.get('business_intent', '')}")
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
    None: ("⚔️", "Upload your training scrolls (data files) and state your mission to begin."),
    "awaiting_bronze_approval": ("💧", "Review the rename/cast rules below, then master Water Breathing to advance."),
    "awaiting_silver_approval": ("🔥", "Check the null-handling & dedup rules, then master Flame Breathing to advance."),
    "awaiting_gold_approval": ("☀️", "Confirm the join/aggregate rules, then master Sun Breathing — the final technique."),
    "complete": ("🐦", "Training complete! Consult the Kasugai Crow below to ask follow-up questions about your data."),
    "failed": ("💀", "Your training was interrupted. Check the error above, then begin a new mission."),
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
    @import url('https://fonts.googleapis.com/css2?family=Yuji+Mai&family=Cinzel:wght@600;800&display=swap');

    * {
        font-family: 'Cinzel', 'Arial', sans-serif;
    }

    .main {
        background:
            radial-gradient(circle at 50% 45%, transparent 0%, rgba(0, 0, 0, 0.5) 100%),
            radial-gradient(circle at 12% 10%, rgba(255, 90, 0, 0.18) 0%, transparent 40%),
            radial-gradient(circle at 88% 15%, rgba(233, 30, 140, 0.16) 0%, transparent 42%),
            radial-gradient(circle at 90% 88%, rgba(0, 217, 255, 0.16) 0%, transparent 40%),
            radial-gradient(circle at 10% 90%, rgba(255, 204, 0, 0.10) 0%, transparent 45%),
            repeating-conic-gradient(from 0deg at 50% 50%, rgba(255,255,255,0.015) 0deg 2deg, transparent 2deg 8deg),
            linear-gradient(135deg, #0a0316 0%, #150a1e 45%, #060412 100%);
    }

    /* Twinkling starlight */
    .star { position: fixed; border-radius: 50%; background: #ffffff; z-index: 0;
        animation: starTwinkle ease-in-out infinite; pointer-events: none; }
    @keyframes starTwinkle {
        0%, 100% { opacity: 0.15; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.3); }
    }

    /* Ember particles drifting up in the background */
    .ember { position: fixed; bottom: -10px; font-size: 14px; opacity: 0.5; z-index: 0;
        animation: emberRise linear infinite; pointer-events: none; }
    @keyframes emberRise {
        0% { transform: translateY(0) translateX(0) scale(0.8); opacity: 0; }
        10% { opacity: 0.7; }
        50% { transform: translateY(-55vh) translateX(-10px) scale(1.1); }
        100% { transform: translateY(-110vh) translateX(20px) scale(0.7); opacity: 0; }
    }

    /* Energy-charge divider — the "katana slash" under the title */
    .slash-divider {
        position: relative;
        height: 4px;
        margin: 0 auto 26px auto;
        width: 55%;
        max-width: 520px;
        background: linear-gradient(90deg, transparent, #ff3d00 20%, #d4af37 50%, #29b6f6 80%, transparent);
        background-size: 200% 100%;
        animation: slashSweep 3s ease-in-out infinite;
        border-radius: 4px;
        box-shadow: 0 0 20px rgba(255, 61, 0, 0.7), 0 0 24px rgba(41, 182, 246, 0.5);
    }
    @keyframes slashSweep {
        0% { background-position: 200% 0; opacity: 0.3; }
        50% { background-position: 0% 0; opacity: 1; }
        100% { background-position: -200% 0; opacity: 0.3; }
    }

    /* Demon Hunter Title — elemental power-surge cycling fire/water/gold */
    .arcade-title {
        font-family: 'Yuji Mai', serif;
        font-size: 46px;
        color: #ff5722;
        text-shadow: 0 0 12px #ff3d00, 0 0 24px rgba(255, 61, 0, 0.6), 0 0 6px #000;
        text-align: center;
        margin: 20px 0 4px 0;
        animation: glow 3.6s ease-in-out infinite;
        letter-spacing: 3px;
    }

    @keyframes glow {
        0%, 100% { text-shadow: 0 0 14px #ff3d00, 0 0 30px rgba(255, 61, 0, 0.7); color: #ff5722; }
        33% { text-shadow: 0 0 18px #29b6f6, 0 0 34px rgba(41, 182, 246, 0.7); color: #4fc3f7; }
        66% { text-shadow: 0 0 20px #d4af37, 0 0 36px rgba(212, 175, 55, 0.7); color: #f0d060; }
    }

    /* Sidebar: Corps HQ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #120a10 0%, #1c1018 100%);
        border-right: 3px solid #d4af37;
        box-shadow: -5px 0 20px rgba(212, 175, 55, 0.2);
    }
    [data-testid="stSidebar"] * { color: #f0d9a8 !important; }

    /* Header */
    .quest-header {
        background: linear-gradient(135deg, #1a0a0a 0%, #3d0f0f 45%, #0a1a2a 100%);
        padding: 30px;
        border-radius: 12px;
        border: 2px solid #d4af37;
        box-shadow: 0 0 30px rgba(212, 175, 55, 0.35);
        margin: -16px -16px 24px -16px;
        text-align: center;
    }

    .quest-header h1 {
        font-family: 'Yuji Mai', serif;
        color: #d4af37;
        margin: 0;
        font-size: 32px;
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.6);
    }

    .quest-header p {
        color: #f0d9a8;
        font-weight: bold;
        margin: 0;
    }

    /* Stats Panel */
    .stats-panel {
        background: linear-gradient(135deg, #2a0e0e 0%, #431414 100%);
        padding: 20px;
        border-radius: 8px;
        border: 2px solid #d4af37;
        box-shadow: 0 0 20px rgba(255, 61, 0, 0.25);
        margin: 15px 0;
    }

    .stat-row {
        display: flex;
        justify-content: space-between;
        margin: 10px 0;
        font-weight: bold;
        color: #f0d9a8;
    }

    .xp-bar {
        background: rgba(41, 182, 246, 0.15);
        border-radius: 4px;
        overflow: hidden;
        height: 20px;
        border: 2px solid #29b6f6;
    }

    .xp-fill {
        height: 100%;
        background: linear-gradient(90deg, #0288d1 0%, #29b6f6 100%);
        animation: glow-bar 1s ease-in-out infinite;
    }

    @keyframes glow-bar {
        0%, 100% { box-shadow: 0 0 10px #29b6f6 inset; }
        50% { box-shadow: 0 0 20px #80d8ff inset; }
    }

    /* Demon Encounter / Approval Gate — with a contained lightning-flash overlay */
    .boss-encounter {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #1a0505 0%, #4a0e0e 55%, #250505 100%);
        padding: 25px;
        border-radius: 12px;
        border: 3px dashed #ff3d00;
        box-shadow: 0 0 30px rgba(255, 61, 0, 0.45);
        text-align: center;
        margin: 20px 0;
        animation: shake 4s ease-in-out infinite;
    }

    .boss-encounter::before {
        content: '';
        position: absolute;
        inset: 0;
        background: rgba(255, 255, 255, 0.9);
        opacity: 0;
        animation: thunderFlash 5s ease-in-out infinite;
        pointer-events: none;
        z-index: 1;
    }
    @keyframes thunderFlash {
        0%, 90%, 100% { opacity: 0; }
        91% { opacity: 0.45; }
        92% { opacity: 0; }
        93.5% { opacity: 0.25; }
        94% { opacity: 0; }
    }

    .kanji-watermark {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-6deg);
        font-family: 'Yuji Mai', serif;
        font-size: 150px;
        line-height: 1;
        color: rgba(255, 255, 255, 0.07);
        pointer-events: none;
        z-index: 0;
        user-select: none;
    }
    .boss-encounter > *:not(.kanji-watermark) { position: relative; z-index: 2; }

    @keyframes shake {
        0%, 88%, 100% { transform: translateX(0) rotate(0deg); }
        90% { transform: translateX(-4px) rotate(-0.3deg); }
        92% { transform: translateX(4px) rotate(0.3deg); }
        94% { transform: translateX(-3px) rotate(0deg); }
        96% { transform: translateX(0); }
    }

    .boss-encounter h3 {
        color: #ff5722;
        font-family: 'Yuji Mai', serif;
        margin: 0 0 15px 0;
        font-size: 22px;
        text-shadow: 0 0 10px #ff3d00;
    }

    .boss-health {
        background: rgba(0, 0, 0, 0.6);
        border: 2px solid #ff3d00;
        border-radius: 6px;
        height: 30px;
        margin: 15px 0;
        overflow: hidden;
    }

    .boss-health-fill {
        height: 100%;
        background: linear-gradient(90deg, #d4af37 0%, #ff5722 100%);
        transition: width 0.5s ease;
        animation: pulse 1s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Content Card — ink-brush reveal with a soft blur-in */
    .phase-card {
        background: linear-gradient(135deg, #140a12 0%, #1c1220 100%);
        padding: 30px;
        border-radius: 12px;
        border: 2px solid #d4af37;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.2);
        animation: fadeInUp 0.7s ease;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px) scale(0.98); filter: blur(4px); }
        to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }

    .phase-card h2 {
        color: #ff5722;
        font-family: 'Yuji Mai', serif;
        font-size: 24px;
        margin: 0 0 15px 0;
        text-shadow: 0 0 10px rgba(255, 87, 34, 0.5);
    }

    .phase-card h3 {
        color: #29b6f6;
        margin: 15px 0 10px 0;
    }

    .phase-card p, .phase-card label, .phase-card small {
        color: #e8dcc8;
    }

    /* Buttons */
    .approve-btn {
        background: linear-gradient(135deg, #29b6f6 0%, #0288d1 100%);
        color: #0a0508;
        border: 2px solid #29b6f6;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 700;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 0 15px rgba(41, 182, 246, 0.5);
    }

    .approve-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 0 25px rgba(41, 182, 246, 0.8);
    }

    .reject-btn {
        background: linear-gradient(135deg, #4a0e0e 0%, #ff3d00 100%);
        color: white;
        border: 2px solid #ff3d00;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 700;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.3s ease;
        box-shadow: 0 0 15px rgba(255, 61, 0, 0.5);
    }

    .reject-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 0 25px rgba(255, 61, 0, 0.8);
    }

    /* Kasugai Crow Messenger Panel */
    .chat-container {
        background: linear-gradient(135deg, #140a12 0%, #1e1420 100%);
        border-radius: 12px;
        border: 2px solid #d4af37;
        display: flex;
        flex-direction: column;
        height: 600px;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.25);
    }

    .chat-header {
        padding: 16px;
        border-bottom: 2px solid #d4af37;
        font-weight: 700;
        color: #d4af37;
        font-family: 'Yuji Mai', serif;
        font-size: 15px;
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
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
        background: linear-gradient(135deg, #4a0e0e 0%, #ff3d00 100%);
        color: white;
        display: inline-block;
        max-width: 85%;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 13px;
        box-shadow: 0 0 10px rgba(255, 61, 0, 0.4);
    }

    .chat-message.assistant .msg {
        background: linear-gradient(135deg, #0288d1 0%, #29b6f6 100%);
        color: #0a0508;
        display: inline-block;
        max-width: 85%;
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        box-shadow: 0 0 10px rgba(41, 182, 246, 0.4);
    }

    .chat-message.user {
        text-align: right;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Rank Badge — glowing aura pulse */
    .achievement {
        display: inline-block;
        background: linear-gradient(135deg, #d4af37 0%, #f0d060 100%);
        color: #1a0a0a;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin: 5px;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.6);
        border: 2px solid #f0d060;
        animation: badgeGlow 2.2s ease-in-out infinite;
    }
    @keyframes badgeGlow {
        0%, 100% { box-shadow: 0 0 10px rgba(212, 175, 55, 0.6); }
        50% { box-shadow: 0 0 22px rgba(212, 175, 55, 1), 0 0 12px rgba(255, 87, 34, 0.6); }
    }

    /* Charging Aura — every primary button pulses like a technique about to fire */
    div[data-testid="stButton"] button[kind="primary"] {
        border: 2px solid #ff5722 !important;
        animation: chargingAura 1.6s ease-in-out infinite;
        font-weight: 700 !important;
    }
    @keyframes chargingAura {
        0%, 100% { box-shadow: 0 0 10px rgba(255, 87, 34, 0.5), 0 0 18px rgba(41, 182, 246, 0.25); }
        50% { box-shadow: 0 0 26px rgba(255, 87, 34, 0.9), 0 0 40px rgba(41, 182, 246, 0.55); }
    }

    /* Data Table */
    .phase-card table { color: #e8dcc8; }
    .phase-card [data-testid="stDataFrame"] { background: rgba(212, 175, 55, 0.08) !important; }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }

    ::-webkit-scrollbar-track {
        background: transparent;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #ff3d00 0%, #d4af37 100%);
        border-radius: 6px;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
    }

    /* Breathing Technique Stage Buttons (clickable progress bar) */
    .stage-row-wrap {
        background: linear-gradient(135deg, #140a12 0%, #1e1420 100%);
        border: 2px solid #d4af37;
        border-radius: 12px;
        padding: 12px 16px 4px 16px;
        margin: 0 0 24px 0;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.2);
    }
    .stage-row-wrap div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
    }
    .stage-row-wrap div[data-testid="stButton"] button:disabled {
        opacity: 0.35;
    }

    /* Technique Activation Flash \u2014 plays once right after an approval click */
    .fx-flash {
        position: fixed; inset: 0; z-index: 9999; pointer-events: none;
        animation: fxFlashFade 0.7s ease-out forwards;
    }
    @keyframes fxFlashFade {
        0% { opacity: 1; }
        100% { opacity: 0; }
    }
    .fx-burst {
        position: fixed; top: 50%; left: 50%; z-index: 9999; pointer-events: none;
        width: 0; height: 0;
    }
    .fx-burst span {
        position: absolute; top: 0; left: 0; font-size: 30px;
        animation: fxParticleOut 0.9s ease-out forwards;
        opacity: 0;
    }
    @keyframes fxParticleOut {
        0% { transform: translate(-50%, -50%) scale(0.3); opacity: 1; }
        100% { transform: translate(var(--tx), var(--ty)) scale(1.4); opacity: 0; }
    }
    .fx-slash {
        position: fixed; top: 50%; left: -10%; width: 120%; height: 6px; z-index: 9999;
        pointer-events: none; transform: translateY(-50%) rotate(-8deg);
        animation: fxSlashWipe 0.6s ease-in forwards;
    }
    @keyframes fxSlashWipe {
        0% { transform: translateY(-50%) rotate(-8deg) scaleX(0); opacity: 1; }
        70% { opacity: 1; }
        100% { transform: translateY(-50%) rotate(-8deg) scaleX(1); opacity: 0; }
    }
    .fx-lightning {
        position: fixed; inset: 0; z-index: 9998; pointer-events: none;
        opacity: 0; animation: fxLightningFlicker 0.5s steps(1, end) forwards;
    }
    @keyframes fxLightningFlicker {
        0% { opacity: 0; }
        10% { opacity: 1; }
        18% { opacity: 0; }
        26% { opacity: 0.9; }
        34% { opacity: 0.1; }
        45% { opacity: 0.7; }
        100% { opacity: 0; }
    }

    /* Responsive */
    @media (max-width: 768px) {
        .arcade-title { font-size: 24px; }
        .phase-card h2 { font-size: 18px; }
    }
</style>
<span class="star" style="left:10%; top:8%; width:2px; height:2px; animation-duration:2.2s;"></span>
<span class="star" style="left:25%; top:18%; width:3px; height:3px; animation-duration:3.1s; animation-delay:0.5s;"></span>
<span class="star" style="left:40%; top:6%; width:2px; height:2px; animation-duration:2.6s; animation-delay:1.1s;"></span>
<span class="star" style="left:60%; top:14%; width:3px; height:3px; animation-duration:2.9s; animation-delay:0.3s;"></span>
<span class="star" style="left:75%; top:9%; width:2px; height:2px; animation-duration:2.3s; animation-delay:1.6s;"></span>
<span class="star" style="left:85%; top:22%; width:3px; height:3px; animation-duration:3.4s; animation-delay:0.8s;"></span>
<span class="star" style="left:15%; top:30%; width:2px; height:2px; animation-duration:2.7s; animation-delay:1.9s;"></span>
<span class="star" style="left:55%; top:28%; width:2px; height:2px; animation-duration:2.4s; animation-delay:0.2s;"></span>
<span class="ember" style="left:6%; animation-duration:9s; animation-delay:0s;">🔥</span>
<span class="ember" style="left:22%; animation-duration:12s; animation-delay:2s;">🔥</span>
<span class="ember" style="left:48%; animation-duration:10s; animation-delay:4s;">🔥</span>
<span class="ember" style="left:68%; animation-duration:14s; animation-delay:1s;">🔥</span>
<span class="ember" style="left:88%; animation-duration:11s; animation-delay:3s;">🔥</span>
""", unsafe_allow_html=True)

FX_THEMES = {
    "water": {
        "flash": "rgba(0, 217, 255, 0.6)",
        "slash": "linear-gradient(90deg, transparent, #00d9ff, #ffffff, #0099ff, transparent)",
        "particles": "💧💧💧💧💧💧",
        "freq": 440,
    },
    "flame": {
        "flash": "rgba(255, 87, 0, 0.6)",
        "slash": "linear-gradient(90deg, transparent, #ff3300, #ffcc00, #d90000, transparent)",
        "particles": "🔥🔥🔥🔥🔥🔥",
        "freq": 220,
    },
    "sun": {
        "flash": "rgba(255, 200, 60, 0.65)",
        "slash": "linear-gradient(90deg, transparent, #ffcc00, #ffffff, #ff2fb3, transparent)",
        "particles": "☀️✨✨☀️✨✨",
        "freq": 660,
    },
}


def trigger_fx(theme: str):
    st.session_state.fx_trigger = theme


def render_technique_flash():
    """Render a one-shot full-screen flash + lightning + particle burst + slash-wipe + synthesized sound."""
    theme = st.session_state.get("fx_trigger")
    if not theme:
        return
    cfg = FX_THEMES.get(theme, FX_THEMES["water"])
    st.session_state.fx_trigger = None

    particle_spans = []
    for i, p in enumerate(cfg["particles"]):
        angle = (360 / len(cfg["particles"])) * i
        import math
        tx = round(220 * math.cos(math.radians(angle)))
        ty = round(220 * math.sin(math.radians(angle)))
        particle_spans.append(
            f'<span style="--tx:{tx}px; --ty:{ty}px; animation-delay:{i * 0.03}s;">{p}</span>'
        )

    bolt_color = cfg["flash"].replace("0.6", "0.9").replace("0.65", "0.9")
    lightning_svg = (
        '<svg class="fx-lightning" viewBox="0 0 400 400" preserveAspectRatio="none">'
        f'<polyline points="60,0 160,150 100,150 260,400 200,220 260,220" '
        f'fill="none" stroke="{bolt_color}" stroke-width="6" />'
        '</svg>'
    )

    st.markdown(
        f'<div class="fx-flash" style="background:{cfg["flash"]};"></div>'
        f'{lightning_svg}'
        f'<div class="fx-slash" style="background:{cfg["slash"]};"></div>'
        f'<div class="fx-burst">{"".join(particle_spans)}</div>',
        unsafe_allow_html=True,
    )

    # Synthesized "technique activation" sound \u2014 generated live via Web Audio API,
    # no external/copyrighted audio files involved.
    components.html(
        f"""
        <script>
        try {{
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime({cfg['freq']}, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime({cfg['freq'] * 2}, ctx.currentTime + 0.15);
            gain.gain.setValueAtTime(0.25, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
            osc.connect(gain).connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.5);
        }} catch (e) {{}}
        </script>
        """,
        height=0,
    )

render_technique_flash()

# LEFT SIDEBAR: QUEST STATS
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="quest-header"><h1>⚔️ CORPS</h1><p>Demon Hunter Data Division</p></div>', unsafe_allow_html=True)

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
            <span>RANK:</span>
            <span style="color: #ff5722; text-shadow: 0 0 10px #ff5722;">{st.session_state.level}</span>
        </div>
        <div class="stat-row">
            <span>XP:</span>
            <span>{xp_into_level} / 500</span>
        </div>
        <div class="xp-bar">
            <div class="xp-fill" style="width: {xp_into_level / 5}%"></div>
        </div>
        <div class="stat-row" style="margin-top: 15px;">
            <span>BADGES:</span>
            <span style="color: #d4af37;">{len(st.session_state.achievements)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"⚡ {xp_to_next} XP to Rank {st.session_state.level + 1}. Ranks have no cap — keep consulting the Crow (+25 XP each) after training completes!")
    
    if st.session_state.achievements:
        st.markdown("### 🏅 Earned Ranks")
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
        if st.button("🔄 New Mission", width='stretch'):
            reset_quest()
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN QUEST AREA + CHAT
# ═════════════════════════════════════════════════════════════════════════════
col_main, col_chat = st.columns([3.5, 1.2], gap="small")

with col_main:
    st.markdown('<h1 class="arcade-title">⚔️ DEMON HUNTER: DATA CORPS ⚔️</h1>', unsafe_allow_html=True)
    st.markdown('<div class="slash-divider"></div>', unsafe_allow_html=True)
    render_quest_progress(st.session_state.state)

    if st.session_state.state and st.session_state.view_stage is not None:
        render_stage_preview(st.session_state.state, st.session_state.view_stage)

    if st.session_state.state is None:
        # MISSION START
        st.markdown('<div class="phase-card">', unsafe_allow_html=True)
        st.markdown('### ⚔️ BEGIN YOUR TRAINING')
        st.markdown('Prepare your data scrolls and undergo the breathing trials!')
        
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
                st.success(f'⚔️ {len(uploaded)} scrolls ready for training!')
                for f in uploaded:
                    st.caption(f"📄 {f.name}")
        
        with col2:
            st.markdown('#### 🎯 Mission Objective')
            business_intent = st.text_area(
                "What is your mission?",
                value="Transform raw retail data into actionable business intelligence",
                height=150,
                label_visibility="collapsed",
            )
        
        st.markdown('---')
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown('#### 🚀 BEGIN TRAINING')
        with col2:
            if st.button("⚡ START BREATHING TRIALS ⚡", width='stretch', disabled=not uploaded):
                if uploaded:
                    with st.spinner("⏳ Beginning training... Summoning the data spirits..."):
                        run_id, file_paths = _save_uploads(uploaded)
                        state = start_pipeline(file_paths, business_intent, run_id)
                    st.session_state.state = state
                    add_xp(100)
                    add_achievement("New Recruit")
                    if state.get("status") == "awaiting_bronze_approval":
                        st.success("✅ TRIAL 1: Water Breathing Awaits Your Approval!")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        state = st.session_state.state
        
        if state["status"] == "failed":
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)
            st.error(f'💀 TRAINING FAILED: {", ".join(state.get("errors", ["Unknown"]))}')
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TRIAL 1: WATER BREATHING
        if state["status"] in ("awaiting_bronze_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter"><span class="kanji-watermark">水</span>', unsafe_allow_html=True)
            st.markdown('### 💧 TRIAL: WATER BREATHING')
            st.markdown('*Master this technique by reviewing and approving the Bronze transformation rules!*')
            
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
            
            st.markdown('### ⚔️ Review Water Breathing Forms')
            try:
                sttm_df = pd.read_csv(state["sttm_bronze_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="bronze", hide_index=False)
            except Exception as e:
                st.error(f"Error loading forms: {e}")
                edited = None
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Master this technique to advance!")
            with col2:
                if st.button("⚡ MASTER TECHNIQUE ⚡", key="bronze_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_bronze_path"], index=False)
                    with st.spinner("💧 Channeling Water Breathing..."):
                        st.session_state.state = approve_bronze(state)
                    add_xp(250)
                    add_achievement("Water Breathing User")
                    trigger_fx("water")
                    st.success("🎉 MASTERED! Water Breathing complete!")
                    st.rerun()
            with col3:
                if st.button("💀 ABANDON MISSION", key="bronze_reject", width='stretch'):
                    st.session_state.state = None
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TRIAL 2: FLAME BREATHING
        if state["status"] in ("awaiting_silver_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter"><span class="kanji-watermark">炎</span>', unsafe_allow_html=True)
            st.markdown('### 🔥 TRIAL: FLAME BREATHING')
            st.markdown('*Flame Breathing purifies your data — cleanse nulls and duplicates to prove your resolve!*')
            st.markdown("""
            <div class="boss-health">
                <div class="boss-health-fill" style="width: 75%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("📦 Preview Water Breathing Results", expanded=False):
                for p in state.get("bronze_output_paths", []):
                    try:
                        df = pd.read_parquet(p)
                        st.markdown(f"**{Path(p).name}** ({len(df):,} rows)")
                        st.dataframe(df.head(3), width='stretch', hide_index=True)
                    except: pass
            
            st.markdown('### ⚔️ Review Flame Breathing Forms')
            try:
                sttm_df = pd.read_csv(state["sttm_silver_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="silver", hide_index=False)
            except: edited = None
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Master this technique to advance!")
            with col2:
                if st.button("⚡ MASTER TECHNIQUE ⚡", key="silver_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_silver_path"], index=False)
                    with st.spinner("🔥 Channeling Flame Breathing..."):
                        st.session_state.state = approve_silver(state)
                    add_xp(250)
                    add_achievement("Flame Hashira")
                    trigger_fx("flame")
                    st.success("🎉 MASTERED! Flame Breathing complete!")
                    st.rerun()
            with col3:
                if st.button("💀 ABANDON MISSION", key="silver_reject", width='stretch'):
                    st.session_state.state = None
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # TRIAL 3: SUN BREATHING
        if state["status"] in ("awaiting_gold_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter"><span class="kanji-watermark">日</span>', unsafe_allow_html=True)
            st.markdown('### ☀️ FINAL TRIAL: SUN BREATHING')
            st.markdown('*The legendary technique! Master Sun Breathing to complete your training!*')
            st.markdown("""
            <div class="boss-health">
                <div class="boss-health-fill" style="width: 50%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("📦 Preview Flame Breathing Results", expanded=False):
                for p in state.get("silver_output_paths", []):
                    try:
                        df = pd.read_parquet(p)
                        st.markdown(f"**{Path(p).name}** ({len(df):,} rows)")
                        st.dataframe(df.head(3), width='stretch', hide_index=True)
                    except: pass
            
            st.markdown('### ⚔️ Review Sun Breathing Forms')
            try:
                sttm_df = pd.read_csv(state["sttm_gold_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="gold", hide_index=False)
            except: edited = None
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Master the final technique to complete your training!")
            with col2:
                if st.button("⚡ MASTER FINAL TECHNIQUE ⚡", key="gold_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_gold_path"], index=False)
                    with st.spinner("☀️🗡️ The ultimate technique... Sun Breathing achieved!"):
                        st.session_state.state = approve_gold(state)
                    add_xp(500)
                    add_achievement("Sun Breathing Master")
                    add_achievement("Demon Slayer Corps Legend")
                    trigger_fx("sun")
                    st.success("🎉🎉🎉 MASTERED! You've completed all breathing trials!")
                    st.rerun()
            with col3:
                if st.button("💀 ABANDON MISSION", key="gold_reject", width='stretch'):
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
                <div class="boss-encounter" style="animation: none; border-style: solid;"><span class="kanji-watermark">鬼</span>
                    <h3>🎉 SURPRISE! SCROLL OF ACHIEVEMENT UNSEALED 🎉</h3>
                    <p style="color: white; font-size: 16px; margin: 10px 0;">
                        You earned <b>{st.session_state.xp} XP</b> and unlocked
                        <b>{len(st.session_state.achievements)} ranks</b> this mission!
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('# 🏆 TRAINING COMPLETE! 🏆')
            st.markdown('### ⛩️ You have mastered all breathing techniques!')
            
            report = state.get("report", {})
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown('#### 📊 THE VERDICT (Your Answer)')
                st.markdown(f'**Mission Objective:** {state["business_intent"]}')
                st.success(safe_md(report.get("answer", "Verdict loading...")))
            
            with col2:
                if report.get("chart"):
                    st.plotly_chart(report["chart"], width='stretch')
            
            st.divider()
            
            st.markdown('#### 📈 Analytics Dojo')
            for p in state.get("gold_output_paths", []):
                try:
                    df = pd.read_parquet(p)
                    with st.expander(f"⚩️ {Path(p).stem}"):
                        st.dataframe(df, width='stretch', hide_index=True)
                except: pass
            
            st.divider()
            
            st.markdown('#### 🔧 Training Records')
            tab1, tab2, tab3 = st.tabs(["SQL Technique", "Traces", "Audit"])
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
                "💾 Download Training Report",
                data=json.dumps(state, indent=2, default=str),
                file_name=f"mission_{state['run_id']}.json",
                mime="application/json",
                width='stretch',
            )
            
            st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL: LIVE MISSION LOG + CONSULT THE KASUGAI CROW
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
            log_items.append('<div class="chat-message assistant"><div class="msg">⏳ No events logged yet for this mission.</div></div>')

    st.markdown(
        '<div class="chat-container"><div class="chat-header">⚩️ TRAINING LOG</div>'
        f'<div class="chat-messages"><div class="log-track" style="animation-duration: {max(10, len(log_items) * 4)}s">'
        f'{"".join(log_items)}{"".join(log_items)}'
        '</div></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 🐦 Consult the Kasugai Crow")
    gold_paths = state.get("gold_output_paths") if state else None

    if not gold_paths:
        st.caption("🔒 Unlocks after you master Sun Breathing. Uses exactly 1 AI call per question — no token waste.")
    elif st.session_state.show_restart_prompt:
        st.warning("🧭 You've asked 5 questions! Begin a fresh mission, or keep training here?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("🔄 Yes, New Mission", width='stretch'):
                reset_quest()
                st.rerun()
        with col_no:
            if st.button("🙅 No, Keep Training", width='stretch'):
                st.session_state.show_restart_prompt = False
                st.session_state.oracle_prompted = False  # allows the nudge to re-trigger after 5 more questions
                st.rerun()
    else:
        oracle_q = st.text_input(
            "Ask a question about your data...", placeholder="e.g. Which region has the highest revenue?",
            key="oracle_input", label_visibility="collapsed",
        )
        if st.button("🐦 Send the Crow", width='stretch', disabled=not oracle_q):
            with st.spinner("🐦 The crow flies with your question (1 AI call)..."):
                try:
                    st.session_state.oracle_answer = ask_question(gold_paths, oracle_q, state["run_id"])
                    add_xp(25)
                    st.session_state.oracle_query_count += 1
                except Exception as exc:
                    st.session_state.oracle_answer = {"answer": f"⚠️ The crow returned empty-clawed: {exc}", "sql": None, "rows": [], "chart": None}
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
