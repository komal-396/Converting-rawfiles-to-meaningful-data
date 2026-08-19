"""
🌌 GALACTIC DATA COMMAND 🌌
An original space/cosmic-themed gamified Streamlit pipeline for data transformations.
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
    page_title="🌌 Galactic Data Command",
    page_icon="🚀",
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
# ACCOUNT LOGIN — original "Space Station Access" character-select screen
# (Fully original silhouette designs. No copyrighted characters/logos used.)
# ═════════════════════════════════════════════════════════════════════════════
def render_login_page():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Rajdhani:wght@500;700&display=swap');
        .main {
            background:
                radial-gradient(circle at 50% 30%, rgba(120, 60, 220, 0.15) 0%, transparent 45%),
                radial-gradient(circle at 15% 80%, rgba(0, 200, 255, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 85% 75%, rgba(255, 0, 150, 0.12) 0%, transparent 40%),
                linear-gradient(180deg, #04030a 0%, #0a0620 50%, #04030a 100%);
        }
        * { font-family: 'Rajdhani', sans-serif; }
        .select-title {
            font-family: 'Orbitron', sans-serif; font-weight: 800;
            font-size: 40px; text-align: center; letter-spacing: 4px;
            color: #7c4dff; text-shadow: 0 0 16px #7c4dff, 0 0 30px rgba(0,200,255,0.5);
            animation: cosmicGlow 3s ease-in-out infinite;
        }
        @keyframes cosmicGlow {
            0%, 100% { text-shadow: 0 0 16px #7c4dff, 0 0 30px rgba(0,200,255,0.5); color: #7c4dff; }
            50% { text-shadow: 0 0 20px #00c8ff, 0 0 34px rgba(255,0,150,0.5); color: #00c8ff; }
        }
        .select-sub { text-align: center; color: #cfd8ff; letter-spacing: 2px; font-size: 13px;
            text-transform: uppercase; margin-bottom: 18px; }

        .pilot-pedestal { text-align: center; padding: 10px 6px 0 6px; position: relative; }
        .console-panel {
            background: linear-gradient(135deg, #0d0a1e 0%, #150c28 100%);
            border: 2px solid #7c4dff; border-radius: 14px; padding: 22px 26px 10px 26px;
            box-shadow: 0 0 28px rgba(124, 77, 255, 0.35);
        }
        .vs-badge { text-align: center; font-family: 'Orbitron', sans-serif; font-size: 20px;
            color: #00e5ff; text-shadow: 0 0 12px rgba(0,229,255,0.8); margin: 6px 0 2px 0; }

        /* Original CSS-only rotating planet (no external image assets) */
        .planet-stage { position: relative; height: 340px; display: flex; align-items: center; justify-content: center; }
        .planet-glow {
            position: absolute; width: 320px; height: 320px; border-radius: 50%;
            background: radial-gradient(circle, rgba(20,40,120,0.45) 0%, rgba(0,0,0,0.2) 60%, transparent 78%);
            animation: planetGlowPulse 4s ease-in-out infinite;
        }
        @keyframes planetGlowPulse {
            0%, 100% { transform: scale(1); opacity: 0.75; }
            50% { transform: scale(1.1); opacity: 1; }
        }
        /* Minimal single-tone "event horizon" orb — no surface texture, just depth */
        .planet-sphere {
            position: relative; width: 250px; height: 250px; border-radius: 50%;
            background: radial-gradient(circle at 38% 35%, #16224a 0%, #0a1130 45%, #020208 80%, #000000 100%);
            box-shadow:
                0 0 60px rgba(20,60,160,0.5), 0 0 120px rgba(10,20,60,0.4),
                inset -18px -12px 50px rgba(0,0,0,0.9), inset 14px 10px 30px rgba(60,90,200,0.15);
            animation: planetBob 6s ease-in-out infinite;
        }
        .planet-accretion {
            position: absolute; width: 340px; height: 340px; border-radius: 50%;
            background: conic-gradient(from 0deg, transparent 0deg, rgba(60,110,255,0.55) 60deg, transparent 140deg,
                rgba(120,80,255,0.35) 220deg, transparent 300deg, transparent 360deg);
            filter: blur(3px); animation: accretionSpin 9s linear infinite;
            mask: radial-gradient(circle, transparent 62%, black 64%, black 78%, transparent 80%);
            -webkit-mask: radial-gradient(circle, transparent 62%, black 64%, black 78%, transparent 80%);
        }
        @keyframes accretionSpin { to { transform: rotate(360deg); } }
        @keyframes planetBob {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        .login-star { position: fixed; border-radius: 50%; background: #ffffff; z-index: 0;
            animation: loginTwinkle ease-in-out infinite; pointer-events: none; }
        @keyframes loginTwinkle {
            0%, 100% { opacity: 0.15; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.3); }
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<span class="login-star" style="left:8%; top:10%; width:2px; height:2px; animation-duration:2.3s;"></span>'
        '<span class="login-star" style="left:20%; top:20%; width:3px; height:3px; animation-duration:3.0s; animation-delay:0.4s;"></span>'
        '<span class="login-star" style="left:35%; top:8%; width:2px; height:2px; animation-duration:2.6s; animation-delay:1.0s;"></span>'
        '<span class="login-star" style="left:65%; top:15%; width:3px; height:3px; animation-duration:2.8s; animation-delay:0.2s;"></span>'
        '<span class="login-star" style="left:78%; top:9%; width:2px; height:2px; animation-duration:2.4s; animation-delay:1.4s;"></span>'
        '<span class="login-star" style="left:90%; top:22%; width:3px; height:3px; animation-duration:3.2s; animation-delay:0.7s;"></span>'
        '<span class="login-star" style="left:12%; top:35%; width:2px; height:2px; animation-duration:2.7s; animation-delay:1.8s;"></span>'
        '<span class="login-star" style="left:50%; top:32%; width:2px; height:2px; animation-duration:2.5s; animation-delay:0.3s;"></span>'
        '<span class="login-star" style="left:85%; top:38%; width:2px; height:2px; animation-duration:2.9s; animation-delay:1.1s;"></span>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="select-title">🌌 GALACTIC DATA COMMAND 🌌</div>', unsafe_allow_html=True)
    st.markdown('<div class="select-sub">Access the station — the fleet awaits your command</div>', unsafe_allow_html=True)

    left, right = st.columns([1, 1])

    with left:
        st.markdown('<div class="planet-stage"><div class="planet-glow"></div><div class="planet-accretion"></div><div class="planet-sphere"></div></div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="console-panel">', unsafe_allow_html=True)
        st.markdown('<div class="vs-badge">— STATION ACCESS —</div>', unsafe_allow_html=True)
        tab_login, tab_signup = st.tabs(["🔑 Login", "🛰️ Enlist"])
        with tab_login:
            u = st.text_input("Callsign", key="login_user")
            p = st.text_input("Access Code", type="password", key="login_pass")
            if st.button("🚀 Board the Station", width='stretch', type="primary"):
                if verify_user(u, p):
                    st.session_state.username = u.strip().lower()
                    st.session_state.progress_loaded = False
                    st.session_state.disclaimer_ack = False
                    st.rerun()
                else:
                    st.error("Invalid callsign or access code.")
        with tab_signup:
            nu = st.text_input("Choose a callsign", key="signup_user")
            np_ = st.text_input("Choose an access code", type="password", key="signup_pass")
            if st.button("🛰️ Enlist Now", width='stretch', type="primary"):
                err = register_user(nu, np_)
                if err:
                    st.error(err)
                else:
                    st.success("Enlisted! Switch to the Login tab to board the station.")
        st.markdown('</div>', unsafe_allow_html=True)


def scroll_to_top():
    """Force the page back to the top — Streamlit otherwise keeps the previous scroll offset on rerun."""
    components.html(
        "<script>window.parent.document.querySelector('section.main').scrollTo(0, 0);</script>",
        height=0,
    )


if not st.session_state.username:
    render_login_page()
    scroll_to_top()
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
# WELCOME BRIEFING — shown once per login, before the app is usable
# ═════════════════════════════════════════════════════════════════════════════
def render_disclaimer_page():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Rajdhani:wght@500;700&display=swap');
        .main { background: radial-gradient(circle at 50% 30%, rgba(120,60,220,0.15) 0%, transparent 45%),
            linear-gradient(180deg, #04030a 0%, #0a0620 50%, #04030a 100%); }
        * { font-family: 'Rajdhani', sans-serif; }
        .brief-star { position: fixed; border-radius: 50%; background: #ffffff; z-index: 0;
            animation: briefTwinkle ease-in-out infinite; pointer-events: none; }
        @keyframes briefTwinkle {
            0%, 100% { opacity: 0.15; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.3); }
        }

        /* ── KORA's arrival scene ─────────────────────────────────────── */
        .ufo-scene { position: relative; height: 260px; margin-bottom: 4px; }

        /* The UFO group only ever carries position/scale — never the caption text,
           so captions don't inherit its scale and blow up (that was the earlier bug). */
        .ufo-rig {
            position: absolute; top: 20px; left: 50%; transform-origin: center;
            animation: koraFlight 6.4s cubic-bezier(0.4, 0.1, 0.25, 1) forwards;
        }
        @keyframes koraFlight {
            0%   { transform: translate(-50%, -110px) scale(0.3) rotate(0deg); opacity: 0; }
            17%  { transform: translate(-50%, 20px) scale(1.35) rotate(0deg); opacity: 1; }
            24%  { transform: translate(-50%, 20px) scale(1.35) rotate(-7deg); }
            30%  { transform: translate(-50%, 20px) scale(1.35) rotate(7deg); }
            36%  { transform: translate(-50%, 20px) scale(1.35) rotate(0deg); }
            64%  { transform: translate(-50%, 20px) scale(1.35) rotate(0deg); opacity: 1; }
            82%  { transform: translate(calc(-50% - 250px), 10px) scale(1.05) rotate(0deg); opacity: 1; }
            100% { transform: translate(calc(-50% - 250px), 10px) scale(1.05) rotate(0deg); opacity: 1; }
        }
        .ufo-dome {
            width: 44px; height: 30px; margin: 0 auto; border-radius: 50% 50% 0 0; position: relative;
            background: radial-gradient(circle at 35% 25%, #e8fbff, #7fe3ff 45%, #0a8fb8 100%);
            box-shadow: 0 0 16px rgba(79,212,255,0.9); overflow: hidden; z-index: 2;
        }
        /* A little robot riding inside the dome */
        .kora-bot { position: absolute; bottom: -2px; left: 50%; transform: translateX(-50%); }
        .kora-bot-head { width: 14px; height: 12px; border-radius: 50%; background: #eaf7ff; margin: 0 auto; position: relative; }
        .kora-bot-eye { position: absolute; top: 4px; width: 2.5px; height: 2.5px; border-radius: 50%; background: #133; }
        .kora-bot-eye.l { left: 3px; } .kora-bot-eye.r { right: 3px; }
        .kora-bot-arm {
            position: absolute; top: 2px; right: -3px; width: 2px; height: 8px; background: #eaf7ff;
            border-radius: 2px; transform-origin: top center; animation: koraWave 6.4s ease forwards;
        }
        @keyframes koraWave {
            0%, 22% { transform: rotate(0deg); }
            25% { transform: rotate(-35deg); } 28% { transform: rotate(10deg); }
            31% { transform: rotate(-30deg); } 34%, 100% { transform: rotate(0deg); }
        }
        /* Classic wide flying-saucer disc with glowing rim lights */
        .ufo-body {
            width: 150px; height: 26px; margin: -6px auto 0; border-radius: 50%; position: relative; z-index: 1;
            background: linear-gradient(180deg, #cfd4e6 0%, #8a8fa3 35%, #4a4e5c 70%, #23252e 100%);
            box-shadow: 0 6px 24px rgba(124,77,255,0.55), inset 0 -6px 10px rgba(0,0,0,0.45), inset 0 4px 6px rgba(255,255,255,0.3);
        }
        .ufo-body::before {
            content: ''; position: absolute; left: 8%; right: 8%; bottom: 2px; height: 8px; border-radius: 50%;
            background: repeating-linear-gradient(90deg, #ffea8a 0 6px, transparent 6px 14px);
            box-shadow: 0 0 10px rgba(255, 220, 120, 0.8);
            animation: rimLightsPulse 1.4s ease-in-out infinite;
        }
        @keyframes rimLightsPulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }
        .ufo-beam {
            width: 60px; height: 70px; margin: 0 auto; clip-path: polygon(20% 0, 80% 0, 100% 100%, 0 100%);
            background: linear-gradient(180deg, rgba(0,229,255,0.45), rgba(0,229,255,0));
            animation: beamPulse 2s ease-in-out infinite;
        }
        @keyframes beamPulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }

        /* Speech captions — independent elements, positioned by themselves, never scaled */
        .kora-caption {
            position: absolute; top: 130px; left: 50%; transform: translateX(-50%);
            white-space: nowrap; background: linear-gradient(135deg, #0d0a1e 0%, #1a0f3d 100%);
            border: 1px solid #4fd4ff; border-radius: 12px; padding: 10px 20px; font-size: 19px; font-weight: 700;
            color: #f2fbff; box-shadow: 0 0 16px rgba(79,212,255,0.55); opacity: 0;
        }
        @keyframes captionInOut { 0%, 100% { opacity: 0; } 15%, 85% { opacity: 1; } }
        .kora-caption.c1 { animation: captionInOut 0.9s ease 1.75s both; }
        .kora-caption.c2 { animation: captionInOut 0.9s ease 2.65s both; }
        .kora-caption.c3 { animation: captionInOut 1.1s ease 3.55s both; font-size: 16px; }

        .scroll-drop {
            position: absolute; top: 40px; left: calc(50% - 250px); font-size: 24px;
            opacity: 0; animation: scrollFall 0.9s ease-in 5.5s forwards;
        }
        @keyframes scrollFall {
            0% { transform: translate(-50%, -10px) rotate(0deg); opacity: 0; }
            25% { opacity: 1; }
            100% { transform: translate(-50%, 150px) rotate(-20deg); opacity: 1; }
        }

        /* ── Full-width paper scroll, unrolling left-to-right across the screen ── */
        .left-banner {
            position: relative;
            background: linear-gradient(90deg, #150c28 0%, #0d0a1e 100%);
            border: 2px solid #00c8ff; border-radius: 10px;
            padding: 22px 30px; box-shadow: 0 0 25px rgba(0, 200, 255, 0.3);
            clip-path: inset(0 100% 0 0);
            animation: paperUnroll 1.1s cubic-bezier(0.65, 0, 0.35, 1) 6.2s forwards;
        }
        @keyframes paperUnroll { to { clip-path: inset(0 0% 0 0); } }
        /* the unrolling "leading edge" glow that sweeps across as the paper opens */
        .left-banner::after {
            content: ''; position: absolute; top: 0; bottom: 0; width: 8px;
            background: linear-gradient(180deg, #00c8ff, #ff4fd8); box-shadow: 0 0 20px rgba(0,200,255,0.9);
            animation: unrollEdge 1.1s cubic-bezier(0.65, 0, 0.35, 1) 6.2s forwards;
        }
        @keyframes unrollEdge { 0% { left: 0; opacity: 1; } 100% { left: 100%; opacity: 0; } }
        .left-banner h4 { color: #ff4fd8; text-shadow: 0 0 8px #ff4fd8; margin: 0 0 10px 0; }
        .left-banner p, .left-banner li { color: #cfd8ff; }
        .quest-obj {
            margin: 10px 0; padding: 10px 14px; border-left: 3px solid #7c4dff;
            background: rgba(124,77,255,0.08); border-radius: 0 8px 8px 0;
        }
        .briefing-note { margin-top: 16px; padding: 12px 14px; border-radius: 8px;
            background: rgba(0,200,255,0.08); border: 1px dashed #00c8ff; font-size: 13px; color: #b8e8ff; }
        div[data-testid="stButton"] button[kind="primary"] {
            animation: briefBtnPulse 1.4s ease-in-out infinite; font-weight: 700;
        }
        @keyframes briefBtnPulse {
            0%, 100% { box-shadow: 0 0 10px rgba(0,200,255,0.4); }
            50% { box-shadow: 0 0 25px rgba(124,77,255,0.8); }
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<span class="brief-star" style="left:10%; top:8%; width:2px; height:2px; animation-duration:2.2s;"></span>'
        '<span class="brief-star" style="left:25%; top:16%; width:3px; height:3px; animation-duration:3.1s; animation-delay:0.5s;"></span>'
        '<span class="brief-star" style="left:60%; top:12%; width:2px; height:2px; animation-duration:2.6s; animation-delay:1.1s;"></span>'
        '<span class="brief-star" style="left:80%; top:20%; width:3px; height:3px; animation-duration:2.9s; animation-delay:0.3s;"></span>'
        '<span class="brief-star" style="left:15%; top:28%; width:2px; height:2px; animation-duration:2.7s; animation-delay:1.6s;"></span>',
        unsafe_allow_html=True,
    )

    st.markdown(f"""
    <div class="ufo-scene">
        <div class="ufo-rig">
            <div class="ufo-dome">
                <div class="kora-bot">
                    <div class="kora-bot-head"><span class="kora-bot-eye l"></span><span class="kora-bot-eye r"></span></div>
                </div>
                <div class="kora-bot-arm"></div>
            </div>
            <div class="ufo-body"></div>
            <div class="ufo-beam"></div>
        </div>
        <div class="kora-caption c1">👋 Hello!</div>
        <div class="kora-caption c2">I'm KORA — nice to meet you, {st.session_state.username}!</div>
        <div class="kora-caption c3">Here's something you should know before your journey begins...</div>
        <div class="scroll-drop">📜</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="left-banner">
        <h4>🚀 YOUR MISSION</h4>
        <p>Galactic Data Command turns a real Bronze/Silver/Gold data pipeline into a space voyage.
        Upload raw data files and navigate 4 legs of the journey:</p>
        <div class="quest-obj">☄️ <b>Asteroid Field (Bronze)</b> — profile your data and propose rename/cast rules</div>
        <div class="quest-obj">🌌 <b>Nebula Storm (Silver)</b> — cleanse nulls, dedupe, and cast types (you approve every rule)</div>
        <div class="quest-obj">🪐 <b>Wormhole Core (Gold)</b> — join and aggregate into analytics-ready tables</div>
        <div class="quest-obj">📡 <b>Deep Space Comms</b> — ask questions in plain English, answered with real SQL over your own data</div>
        <div class="briefing-note">
            ⚡ Your XP, rank, and progress are saved to your account.<br>
            🔒 Files stay local on this machine — only the question/SQL text is sent to the LLM.<br>
            🛠️ Demo-grade auth: fine for local use, not hardened for production.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    _, btn_col, _ = st.columns([1, 1, 1])
    with btn_col:
        if st.button("✅ OK, LAUNCH!", width='stretch', type="primary"):
            st.session_state.disclaimer_ack = True
            st.rerun()


if not st.session_state.disclaimer_ack:
    render_disclaimer_page()
    scroll_to_top()
    st.stop()

QUEST_STAGES = [
    ("🚀", "Launch"),
    ("☄️", "Asteroid"),
    ("🌌", "Nebula"),
    ("🪐", "Wormhole"),
    ("📡", "Verdict"),
]
STATUS_TO_STAGE = {
    None: 0,
    "awaiting_bronze_approval": 1,
    "awaiting_silver_approval": 2,
    "awaiting_gold_approval": 3,
    "complete": 4,
}


def render_quest_progress(state: dict | None) -> None:
    """Spaceship flight-path tracker: the ship's position along the track shows mission progress."""
    status = state["status"] if state else None
    failed = status == "failed"
    current = STATUS_TO_STAGE.get(status, 4 if failed else 0)
    pct = (min(current, 4) / 4) * 100

    nodes_html = []
    for i, (icon, label) in enumerate(QUEST_STAGES):
        if failed and i == current:
            cls = "failed"
        elif status == "complete" or i < current:
            cls = "done"
        elif i == current:
            cls = "active"
        else:
            cls = ""
        nodes_html.append(f'<div class="flight-node {cls}"><span class="flight-node-icon">{icon}</span><span class="flight-node-label">{label}</span></div>')

    st.markdown(f"""
    <div class="flight-path-wrap">
        <div class="flight-track"><div class="flight-track-fill" style="width:{pct}%"></div></div>
        <div class="flight-ship" style="left: calc({pct}% - 14px);">🚀</div>
        <div class="flight-nodes">{''.join(nodes_html)}</div>
    </div>
    """, unsafe_allow_html=True)


def _render_stage_body(state: dict, stage_idx: int) -> None:
    """The read-only content for a single stage — used inside each tab."""
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
                with st.expander(f"🪐 {Path(p).stem} ({len(df):,} rows)"):
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


def render_stage_tabs(state: dict) -> None:
    """Real tabs — one per mission leg — for browsing read-only history of the voyage so far."""
    reached_keys = [
        True,
        bool(state.get("sttm_bronze_path")),
        bool(state.get("sttm_silver_path")),
        bool(state.get("sttm_gold_path")),
        bool(state.get("report")),
    ]
    with st.container(border=True):
        tabs = st.tabs([f"{icon} {label}" for icon, label in QUEST_STAGES])
        for i, tab in enumerate(tabs):
            with tab:
                st.markdown('<div class="tab-shatter-in">', unsafe_allow_html=True)
                if not reached_keys[i]:
                    st.caption("🔒 Not reached yet — clear the earlier legs first.")
                else:
                    _render_stage_body(state, i)
                st.markdown('</div>', unsafe_allow_html=True)


    st.markdown('</div>', unsafe_allow_html=True)

PHASE_TIPS = {
    None: ("🚀", "Upload your data cargo and log your mission objective to begin launch."),
    "awaiting_bronze_approval": ("☄️", "Review the rename/cast rules below, then clear the Asteroid Field to advance."),
    "awaiting_silver_approval": ("🌌", "Check the null-handling & dedup rules, then navigate the Nebula Storm."),
    "awaiting_gold_approval": ("🪐", "Confirm the join/aggregate rules, then punch through the Wormhole Core."),
    "complete": ("📡", "Mission complete! Ping Deep Space Comms below to ask follow-up questions about your data."),
    "failed": ("💥", "Mission control lost signal. Check the error above, then launch a new mission."),
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
    """Save this account's mission state to disk so it's there next time they log in."""
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
# COSMIC STYLES
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Rajdhani:wght@500;700&display=swap');

    * { font-family: 'Rajdhani', sans-serif; }

    .main {
        background:
            radial-gradient(circle at 50% 45%, transparent 0%, rgba(0,0,0,0.5) 100%),
            radial-gradient(circle at 12% 10%, rgba(124, 77, 255, 0.16) 0%, transparent 40%),
            radial-gradient(circle at 88% 15%, rgba(255, 79, 216, 0.14) 0%, transparent 42%),
            radial-gradient(circle at 90% 88%, rgba(0, 200, 255, 0.16) 0%, transparent 40%),
            radial-gradient(circle at 10% 90%, rgba(255, 204, 0, 0.08) 0%, transparent 45%),
            linear-gradient(180deg, #04030a 0%, #0a0620 50%, #04030a 100%);
    }

    .star { position: fixed; border-radius: 50%; background: #ffffff; z-index: 0;
        animation: starTwinkle ease-in-out infinite; pointer-events: none; }
    @keyframes starTwinkle {
        0%, 100% { opacity: 0.15; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.3); }
    }

    .ember { position: fixed; bottom: -10px; font-size: 14px; opacity: 0.5; z-index: 0;
        animation: emberRise linear infinite; pointer-events: none; }
    @keyframes emberRise {
        0% { transform: translateY(0) translateX(0) scale(0.8); opacity: 0; }
        10% { opacity: 0.7; }
        50% { transform: translateY(-55vh) translateX(-10px) scale(1.1); }
        100% { transform: translateY(-110vh) translateX(20px) scale(0.7); opacity: 0; }
    }

    .slash-divider {
        position: relative; height: 4px; margin: 0 auto 26px auto; width: 55%; max-width: 520px;
        background: linear-gradient(90deg, transparent, #7c4dff 20%, #00c8ff 50%, #ff4fd8 80%, transparent);
        background-size: 200% 100%; animation: slashSweep 3s ease-in-out infinite;
        border-radius: 4px; box-shadow: 0 0 20px rgba(124,77,255,0.7), 0 0 24px rgba(0,200,255,0.5);
    }
    @keyframes slashSweep {
        0% { background-position: 200% 0; opacity: 0.3; }
        50% { background-position: 0% 0; opacity: 1; }
        100% { background-position: -200% 0; opacity: 0.3; }
    }

    .arcade-title {
        font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 42px; color: #7c4dff;
        text-shadow: 0 0 14px #7c4dff, 0 0 28px rgba(124,77,255,0.6); text-align: center;
        margin: 20px 0 4px 0; animation: glow 3.6s ease-in-out infinite; letter-spacing: 3px;
    }
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 14px #7c4dff, 0 0 30px rgba(124,77,255,0.7); color: #7c4dff; }
        33% { text-shadow: 0 0 18px #00c8ff, 0 0 34px rgba(0,200,255,0.7); color: #00c8ff; }
        66% { text-shadow: 0 0 20px #ff4fd8, 0 0 36px rgba(255,79,216,0.7); color: #ff4fd8; }
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0620 0%, #150c28 100%);
        border-right: 3px solid #00c8ff; box-shadow: -5px 0 20px rgba(0,200,255,0.2);
    }
    [data-testid="stSidebar"] * { color: #cfd8ff !important; }

    .quest-header {
        background: linear-gradient(135deg, #150a2a 0%, #1a0f3d 45%, #0a1a2a 100%);
        padding: 30px; border-radius: 12px; border: 2px solid #00c8ff;
        box-shadow: 0 0 30px rgba(0,200,255,0.35); margin: -16px -16px 24px -16px; text-align: center;
    }
    .quest-header h1 { font-family: 'Orbitron', sans-serif; color: #00c8ff; margin: 0; font-size: 28px;
        text-shadow: 0 0 10px rgba(0,200,255,0.6); }
    .quest-header p { color: #cfd8ff; font-weight: bold; margin: 0; }

    .stats-panel {
        background: linear-gradient(135deg, #1a0f3d 0%, #2a1a55 100%); padding: 20px; border-radius: 8px;
        border: 2px solid #00c8ff; box-shadow: 0 0 20px rgba(124,77,255,0.25); margin: 15px 0;
    }
    .stat-row { display: flex; justify-content: space-between; margin: 10px 0; font-weight: bold; color: #cfd8ff; }
    .xp-bar { background: rgba(124,77,255,0.15); border-radius: 4px; overflow: hidden; height: 20px; border: 2px solid #7c4dff; }
    .xp-fill { height: 100%; background: linear-gradient(90deg, #7c4dff 0%, #00c8ff 100%); animation: glow-bar 1s ease-in-out infinite; }
    @keyframes glow-bar {
        0%, 100% { box-shadow: 0 0 10px #7c4dff inset; }
        50% { box-shadow: 0 0 20px #00c8ff inset; }
    }

    .boss-encounter {
        position: relative; overflow: hidden;
        background: linear-gradient(135deg, #0a0620 0%, #1a0f3d 55%, #05030f 100%);
        padding: 25px; border-radius: 12px; border: 2px solid #ff4fd8;
        box-shadow: 0 0 30px rgba(255,79,216,0.4); text-align: center; margin: 20px 0;
        animation: encounterGlow 3s ease-in-out infinite;
    }
    @keyframes encounterGlow {
        0%, 100% { box-shadow: 0 0 24px rgba(255,79,216,0.35); border-color: #ff4fd8; }
        50% { box-shadow: 0 0 40px rgba(0,200,255,0.5); border-color: #00c8ff; }
    }
    .boss-encounter::before {
        content: ''; position: absolute; top: 50%; left: 50%; width: 20px; height: 20px;
        border: 2px solid rgba(0,200,255,0.6); border-radius: 50%; transform: translate(-50%,-50%);
        animation: radarPing 3.5s ease-out infinite; pointer-events: none; z-index: 1;
    }
    @keyframes radarPing {
        0% { width: 20px; height: 20px; opacity: 0.9; }
        100% { width: 500px; height: 500px; opacity: 0; }
    }
    .cosmic-watermark {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-6deg);
        font-size: 130px; opacity: 0.12; pointer-events: none; z-index: 0; user-select: none;
    }
    .boss-encounter > *:not(.cosmic-watermark) { position: relative; z-index: 2; }
    .boss-encounter h3 { color: #ff4fd8; font-family: 'Orbitron', sans-serif; margin: 0 0 15px 0;
        font-size: 20px; text-shadow: 0 0 10px #ff4fd8; }

    .boss-health { background: rgba(0,0,0,0.6); border: 2px solid #ff4fd8; border-radius: 6px; height: 30px; margin: 15px 0; overflow: hidden; }
    .boss-health-fill { height: 100%; background: linear-gradient(90deg, #7c4dff 0%, #00c8ff 100%); transition: width 0.5s ease; animation: pulse 1s ease-in-out infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }

    .phase-card {
        background: linear-gradient(135deg, #0a0620 0%, #150c28 100%); padding: 30px; border-radius: 12px;
        border: 2px solid #00c8ff; box-shadow: 0 0 20px rgba(0,200,255,0.2); animation: fadeInUp 0.7s ease;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px) scale(0.98); filter: blur(4px); }
        to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }
    .phase-card h2 { color: #ff4fd8; font-family: 'Orbitron', sans-serif; font-size: 22px; margin: 0 0 15px 0;
        text-shadow: 0 0 10px rgba(255,79,216,0.5); }
    .phase-card h3 { color: #00c8ff; margin: 15px 0 10px 0; }
    .phase-card p, .phase-card label, .phase-card small { color: #cfd8ff; }

    .chat-container {
        background: linear-gradient(135deg, #0a0620 0%, #150c28 100%); border-radius: 12px; border: 2px solid #00c8ff;
        display: flex; flex-direction: column; height: 600px; box-shadow: 0 0 20px rgba(0,200,255,0.25);
    }
    .chat-header { padding: 16px; border-bottom: 2px solid #00c8ff; font-weight: 700; color: #00c8ff;
        font-family: 'Orbitron', sans-serif; font-size: 14px; text-shadow: 0 0 10px rgba(0,200,255,0.5); }
    .chat-messages { flex: 1; min-height: 0; max-height: 520px; overflow: hidden; padding: 16px; }
    .chat-messages:hover .log-track { animation-play-state: paused; }
    .log-track { animation: scrollLog linear infinite; }
    @keyframes scrollLog { 0% { transform: translateY(0); } 100% { transform: translateY(-50%); } }
    .chat-message { margin: 12px 0; animation: slideIn 0.4s ease; }
    .chat-message.user .msg {
        background: linear-gradient(135deg, #6a1b9a 0%, #ff4fd8 100%); color: white; display: inline-block;
        max-width: 85%; padding: 10px 14px; border-radius: 8px; font-size: 13px; box-shadow: 0 0 10px rgba(255,79,216,0.4);
    }
    .chat-message.assistant .msg {
        background: linear-gradient(135deg, #0077aa 0%, #00c8ff 100%); color: #04030a; display: inline-block;
        max-width: 85%; padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 600;
        box-shadow: 0 0 10px rgba(0,200,255,0.4);
    }
    .chat-message.user { text-align: right; }
    @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

    .achievement {
        display: inline-block; background: linear-gradient(135deg, #7c4dff 0%, #00c8ff 100%); color: #04030a;
        padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 700; margin: 5px;
        box-shadow: 0 0 10px rgba(124,77,255,0.6); border: 2px solid #00c8ff;
        animation: badgeGlow 2.2s ease-in-out infinite;
    }
    @keyframes badgeGlow {
        0%, 100% { box-shadow: 0 0 10px rgba(124,77,255,0.6); }
        50% { box-shadow: 0 0 22px rgba(0,200,255,1), 0 0 12px rgba(255,79,216,0.6); }
    }

    div[data-testid="stButton"] button[kind="primary"] {
        border: 2px solid #00c8ff !important; animation: chargingAura 1.6s ease-in-out infinite; font-weight: 700 !important;
    }
    @keyframes chargingAura {
        0%, 100% { box-shadow: 0 0 10px rgba(0,200,255,0.5), 0 0 18px rgba(124,77,255,0.25); }
        50% { box-shadow: 0 0 26px rgba(0,200,255,0.9), 0 0 40px rgba(255,79,216,0.5); }
    }

    .phase-card table { color: #cfd8ff; }
    .phase-card [data-testid="stDataFrame"] { background: rgba(0,200,255,0.08) !important; }

    ::-webkit-scrollbar { width: 12px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #7c4dff 0%, #00c8ff 100%); border-radius: 6px; box-shadow: 0 0 10px rgba(0,200,255,0.5);
    }

    /* Spaceship flight-path tracker */
    .flight-path-wrap {
        position: relative; background: linear-gradient(135deg, #0a0620 0%, #150c28 100%);
        border: 2px solid #00c8ff; border-radius: 12px; padding: 30px 20px 14px 20px;
        margin: 0 0 24px 0; box-shadow: 0 0 20px rgba(0,200,255,0.2);
    }
    .flight-track { position: relative; height: 4px; border-radius: 4px; background: rgba(124,77,255,0.2); margin: 0 10px; }
    .flight-track-fill {
        height: 100%; border-radius: 4px; background: linear-gradient(90deg, #7c4dff, #00c8ff);
        transition: width 1s ease;
    }
    .flight-ship {
        position: absolute; top: 12px; font-size: 22px; transition: left 1s ease;
        animation: shipThrust 1.4s ease-in-out infinite; filter: drop-shadow(0 0 6px #00c8ff);
    }
    @keyframes shipThrust { 0%, 100% { transform: translateY(0) rotate(90deg); } 50% { transform: translateY(-4px) rotate(90deg); } }
    .flight-nodes { display: flex; justify-content: space-between; margin-top: 14px; }
    .flight-node { flex: 1; text-align: center; font-size: 11px; color: #6a6f8a; font-weight: 700; }
    .flight-node-icon { font-size: 20px; display: block; margin-bottom: 2px; filter: grayscale(1); opacity: 0.4; }
    .flight-node.done .flight-node-icon, .flight-node.active .flight-node-icon { filter: grayscale(0); opacity: 1; }
    .flight-node.done { color: #00c8ff; }
    .flight-node.active { color: #ff4fd8; animation: activeNodePulse 1.4s ease-in-out infinite; }
    @keyframes activeNodePulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
    .flight-node.failed { color: #ff3b3b; }

    /* "Universe breaks apart" reveal each time a tab panel becomes visible */
    .tab-shatter-in { animation: tabShatterIn 0.5s cubic-bezier(0.2, 0.8, 0.3, 1); }
    @keyframes tabShatterIn {
        0% { opacity: 0; transform: scale(0.9) rotate(-2deg); filter: blur(6px) brightness(2); clip-path: inset(0 40% 0 40%); }
        60% { clip-path: inset(0 0 0 0); }
        100% { opacity: 1; transform: scale(1) rotate(0deg); filter: blur(0) brightness(1); clip-path: inset(0 0 0 0); }
    }

    .fx-flash { position: fixed; inset: 0; z-index: 9999; pointer-events: none; animation: fxFlashFade 0.7s ease-out forwards; }
    @keyframes fxFlashFade { 0% { opacity: 1; } 100% { opacity: 0; } }
    .fx-burst { position: fixed; top: 50%; left: 50%; z-index: 9999; pointer-events: none; width: 0; height: 0; }
    .fx-burst span { position: absolute; top: 0; left: 0; font-size: 30px; animation: fxParticleOut 0.9s ease-out forwards; opacity: 0; }
    @keyframes fxParticleOut {
        0% { transform: translate(-50%, -50%) scale(0.3); opacity: 1; }
        100% { transform: translate(var(--tx), var(--ty)) scale(1.4); opacity: 0; }
    }
    .fx-warp {
        position: fixed; inset: 0; z-index: 9999; pointer-events: none;
        background: radial-gradient(circle, transparent 0%, transparent 40%, var(--warp-color) 100%);
        animation: fxWarpJump 0.6s ease-in forwards;
    }
    @keyframes fxWarpJump {
        0% { opacity: 0; transform: scale(0.6); }
        40% { opacity: 0.85; }
        100% { opacity: 0; transform: scale(1.6); }
    }

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
<span class="ember" style="left:6%; animation-duration:9s; animation-delay:0s;">✨</span>
<span class="ember" style="left:22%; animation-duration:12s; animation-delay:2s;">✨</span>
<span class="ember" style="left:48%; animation-duration:10s; animation-delay:4s;">✨</span>
<span class="ember" style="left:68%; animation-duration:14s; animation-delay:1s;">✨</span>
<span class="ember" style="left:88%; animation-duration:11s; animation-delay:3s;">✨</span>
""", unsafe_allow_html=True)

FX_THEMES = {
    "water": {"flash": "rgba(0, 200, 255, 0.6)", "slash": "linear-gradient(90deg, transparent, #00c8ff, #ffffff, #0077aa, transparent)", "particles": "☄️☄️☄️☄️☄️☄️", "freq": 440},
    "flame": {"flash": "rgba(124, 77, 255, 0.6)", "slash": "linear-gradient(90deg, transparent, #7c4dff, #ff4fd8, #7c4dff, transparent)", "particles": "🌌🌌🌌🌌🌌🌌", "freq": 220},
    "sun": {"flash": "rgba(255, 79, 216, 0.65)", "slash": "linear-gradient(90deg, transparent, #ff4fd8, #ffffff, #00c8ff, transparent)", "particles": "🪐✨✨🪐✨✨", "freq": 660},
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
        particle_spans.append(f'<span style="--tx:{tx}px; --ty:{ty}px; animation-delay:{i * 0.03}s;">{p}</span>')

    warp_color = cfg["flash"].replace("0.6", "0.85").replace("0.65", "0.85")

    st.markdown(
        f'<div class="fx-flash" style="background:{cfg["flash"]};"></div>'
        f'<div class="fx-warp" style="--warp-color:{warp_color};"></div>'
        f'<div class="fx-burst">{"".join(particle_spans)}</div>',
        unsafe_allow_html=True,
    )

render_technique_flash()

# Shatter-and-reassemble transition on every tab switch — a grid of tiles flies apart
# (covering the screen) then flies back together, injected client-side so it always
# fires regardless of how Streamlit toggles the underlying tab panel visibility.
components.html(
    """
    <script>
    (function() {
        const doc = window.parent.document;
        if (doc.__cosmicShatterInit) return;
        doc.__cosmicShatterInit = true;

        const style = doc.createElement('style');
        style.textContent = `
            .cosmic-shatter-layer { position: fixed; inset: 0; z-index: 999999; pointer-events: none; }
            .cosmic-shard {
                position: absolute; background: linear-gradient(135deg, rgba(20,10,40,0.97), rgba(5,5,15,0.97));
                border: 1px solid rgba(0,200,255,0.25); box-shadow: 0 0 10px rgba(124,77,255,0.25);
                opacity: 0;
            }
        `;
        doc.head.appendChild(style);

        const ROWS = 5, COLS = 7;

        function burst(direction) {
            const layer = doc.createElement('div');
            layer.className = 'cosmic-shatter-layer';
            const w = window.parent.innerWidth, h = window.parent.innerHeight;
            const tw = w / COLS, th = h / ROWS;

            for (let r = 0; r < ROWS; r++) {
                for (let c = 0; c < COLS; c++) {
                    const shard = doc.createElement('div');
                    shard.className = 'cosmic-shard';
                    const x = c * tw, y = r * th;
                    shard.style.left = x + 'px';
                    shard.style.top = y + 'px';
                    shard.style.width = tw + 1 + 'px';
                    shard.style.height = th + 1 + 'px';

                    const cx = w / 2, cy = h / 2;
                    const dx = (x + tw / 2 - cx) / cx;
                    const dy = (y + th / 2 - cy) / cy;
                    const flyX = dx * 260 + (Math.random() * 60 - 30);
                    const flyY = dy * 260 + (Math.random() * 60 - 30);
                    const rot = (Math.random() * 70 - 35);
                    const delay = (Math.hypot(dx, dy) * 0.05) + (Math.random() * 0.04);

                    if (direction === 'out') {
                        shard.style.transform = 'translate(0,0) rotate(0deg) scale(1)';
                        shard.style.opacity = '1';
                        shard.style.transition = `transform 0.42s cubic-bezier(.55,0,1,.45) ${delay}s, opacity 0.42s ease ${delay + 0.18}s`;
                        requestAnimationFrame(() => requestAnimationFrame(() => {
                            shard.style.transform = `translate(${flyX}px, ${flyY}px) rotate(${rot}deg) scale(0.4)`;
                            shard.style.opacity = '0';
                        }));
                    } else {
                        shard.style.transform = `translate(${flyX}px, ${flyY}px) rotate(${rot}deg) scale(0.4)`;
                        shard.style.opacity = '0';
                        shard.style.transition = `transform 0.48s cubic-bezier(0,.6,.3,1) ${delay}s, opacity 0.3s ease ${delay}s`;
                        requestAnimationFrame(() => requestAnimationFrame(() => {
                            shard.style.transform = 'translate(0,0) rotate(0deg) scale(1)';
                            shard.style.opacity = '1';
                        }));
                    }
                    layer.appendChild(shard);
                }
            }
            doc.body.appendChild(layer);
            return layer;
        }

        doc.addEventListener('click', function(e) {
            const tabBtn = e.target.closest('button[role="tab"]');
            if (!tabBtn || tabBtn.getAttribute('aria-selected') === 'true') return;

            const outLayer = burst('out');
            setTimeout(function() {
                outLayer.remove();
                const inLayer = burst('in');
                setTimeout(function() { inLayer.remove(); }, 620);
            }, 560);
        }, true);
    })();
    </script>
    """,
    height=0,
)

# ═════════════════════════════════════════════════════════════════════════════
# LEFT SIDEBAR: FLEET STATS
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="quest-header"><h1>🚀 FLEET</h1><p>Galactic Data Command</p></div>', unsafe_allow_html=True)

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

    xp_into_level = st.session_state.xp % 500
    xp_to_next = 500 - xp_into_level
    st.markdown(f"""
    <div class="stats-panel">
        <div class="stat-row">
            <span>RANK:</span>
            <span style="color: #00c8ff; text-shadow: 0 0 10px #00c8ff;">{st.session_state.level}</span>
        </div>
        <div class="stat-row">
            <span>XP:</span>
            <span>{xp_into_level} / 500</span>
        </div>
        <div class="xp-bar">
            <div class="xp-fill" style="width: {xp_into_level / 5}%"></div>
        </div>
        <div class="stat-row" style="margin-top: 15px;">
            <span>MEDALS:</span>
            <span style="color: #ff4fd8;">{len(st.session_state.achievements)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"⚡ {xp_to_next} XP to Rank {st.session_state.level + 1}. Ranks have no cap — keep pinging Deep Space Comms (+25 XP each) after your mission completes!")

    if st.session_state.achievements:
        st.markdown("### 🎖️ Earned Medals")
        for achievement in st.session_state.achievements:
            st.markdown(f'<div class="achievement">{achievement}</div>', unsafe_allow_html=True)

    st.divider()

    if is_llm_configured():
        st.markdown('🤖 **AI Ready** · Groq Engine Online')
    else:
        st.error('❌ AI Engine Offline')

    st.divider()

    if st.session_state.state:
        state = st.session_state.state
        st.markdown(f"📍 **Mission ID:** `{state['run_id'][:8]}`")
        if st.button("🔄 New Mission", width='stretch'):
            reset_quest()
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN MISSION AREA + COMMS
# ═════════════════════════════════════════════════════════════════════════════
col_main, col_chat = st.columns([3.5, 1.2], gap="small")

with col_main:
    st.markdown('<h1 class="arcade-title">🌌 GALACTIC DATA COMMAND 🌌</h1>', unsafe_allow_html=True)
    st.markdown('<div class="slash-divider"></div>', unsafe_allow_html=True)
    render_quest_progress(st.session_state.state)

    if st.session_state.state:
        render_stage_tabs(st.session_state.state)

    if st.session_state.state is None:
        st.markdown('<div class="phase-card">', unsafe_allow_html=True)
        st.markdown('### 🚀 PREPARE FOR LAUNCH')
        st.markdown('Load your data cargo and chart your mission before departure!')

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('#### 📦 Upload Data Cargo')
            uploaded = st.file_uploader(
                "Choose your data cargo",
                type=["csv", "tsv", "txt", "xlsx", "xls", "json", "parquet"],
                accept_multiple_files=True,
                label_visibility="collapsed",
            )
            st.caption("Supported: CSV, TSV, TXT, Excel (.xlsx/.xls), JSON, Parquet")
            if uploaded:
                st.success(f'🚀 {len(uploaded)} cargo files loaded and ready!')
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
            st.markdown('#### 🛰️ BEGIN LAUNCH')
        with col2:
            if st.button("⚡ INITIATE LAUNCH SEQUENCE ⚡", width='stretch', disabled=not uploaded):
                if uploaded:
                    with st.spinner("⏳ Igniting thrusters... Calibrating navigation..."):
                        run_id, file_paths = _save_uploads(uploaded)
                        state = start_pipeline(file_paths, business_intent, run_id)
                    st.session_state.state = state
                    add_xp(100)
                    add_achievement("Cadet")
                    if state.get("status") == "awaiting_bronze_approval":
                        st.success("✅ LEG 1: Asteroid Field Awaits Your Clearance!")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        state = st.session_state.state

        if state["status"] == "failed":
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)
            st.error(f'💥 MISSION FAILED: {", ".join(state.get("errors", ["Unknown"]))}')
            st.markdown('</div>', unsafe_allow_html=True)

        # LEG 1: ASTEROID FIELD
        if state["status"] in ("awaiting_bronze_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter"><span class="cosmic-watermark">☄️</span>', unsafe_allow_html=True)
            st.markdown('### ☄️ LEG 1: ASTEROID FIELD')
            st.markdown('*Navigate the asteroid field by reviewing and clearing the Bronze transformation rules!*')

            st.markdown("""
            <div class="boss-health">
                <div class="boss-health-fill" style="width: 100%"></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("📊 Analyze Cargo Scan", expanded=False):
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

            st.markdown('### 🛰️ Review Navigation Rules')
            try:
                sttm_df = pd.read_csv(state["sttm_bronze_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="bronze", hide_index=False)
            except Exception as e:
                st.error(f"Error loading rules: {e}")
                edited = None

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Clear this leg to advance to the Nebula Storm!")
            with col2:
                if st.button("⚡ CLEAR ASTEROID FIELD ⚡", key="bronze_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_bronze_path"], index=False)
                    with st.spinner("☄️ Navigating the asteroid field..."):
                        st.session_state.state = approve_bronze(state)
                    add_xp(250)
                    add_achievement("Navigator")
                    trigger_fx("water")
                    st.success("🎉 CLEARED! Asteroid Field navigated!")
                    st.rerun()
            with col3:
                if st.button("💥 ABORT MISSION", key="bronze_reject", width='stretch'):
                    st.session_state.state = None
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # LEG 2: NEBULA STORM
        if state["status"] in ("awaiting_silver_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter"><span class="cosmic-watermark">🌌</span>', unsafe_allow_html=True)
            st.markdown('### 🌌 LEG 2: NEBULA STORM')
            st.markdown('*The nebula storm scrambles your data — cleanse nulls and duplicates to push through!*')
            st.markdown("""
            <div class="boss-health">
                <div class="boss-health-fill" style="width: 75%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("📦 Preview Asteroid Field Results", expanded=False):
                for p in state.get("bronze_output_paths", []):
                    try:
                        df = pd.read_parquet(p)
                        st.markdown(f"**{Path(p).name}** ({len(df):,} rows)")
                        st.dataframe(df.head(3), width='stretch', hide_index=True)
                    except: pass

            st.markdown('### 🛰️ Review Storm Navigation Rules')
            try:
                sttm_df = pd.read_csv(state["sttm_silver_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="silver", hide_index=False)
            except: edited = None

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Clear this leg to advance to the Wormhole Core!")
            with col2:
                if st.button("⚡ CLEAR NEBULA STORM ⚡", key="silver_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_silver_path"], index=False)
                    with st.spinner("🌌 Weathering the nebula storm..."):
                        st.session_state.state = approve_silver(state)
                    add_xp(250)
                    add_achievement("Fleet Commander")
                    trigger_fx("flame")
                    st.success("🎉 CLEARED! Nebula Storm survived!")
                    st.rerun()
            with col3:
                if st.button("💥 ABORT MISSION", key="silver_reject", width='stretch'):
                    st.session_state.state = None
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # LEG 3: WORMHOLE CORE
        if state["status"] in ("awaiting_gold_approval",):
            st.markdown('<div class="phase-card"><div class="boss-encounter"><span class="cosmic-watermark">🪐</span>', unsafe_allow_html=True)
            st.markdown('### 🪐 FINAL LEG: WORMHOLE CORE')
            st.markdown('*The final jump! Punch through the Wormhole Core to complete your voyage!*')
            st.markdown("""
            <div class="boss-health">
                <div class="boss-health-fill" style="width: 50%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("📦 Preview Nebula Storm Results", expanded=False):
                for p in state.get("silver_output_paths", []):
                    try:
                        df = pd.read_parquet(p)
                        st.markdown(f"**{Path(p).name}** ({len(df):,} rows)")
                        st.dataframe(df.head(3), width='stretch', hide_index=True)
                    except: pass

            st.markdown('### 🛰️ Review Wormhole Jump Rules')
            try:
                sttm_df = pd.read_csv(state["sttm_gold_path"])
                edited = st.data_editor(sttm_df, width='stretch', num_rows="dynamic", key="gold", hide_index=False)
            except: edited = None

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("⚡ Punch through the wormhole to complete your voyage!")
            with col2:
                if st.button("⚡ JUMP THE WORMHOLE ⚡", key="gold_approve", width='stretch'):
                    if edited is not None:
                        edited.to_csv(state["sttm_gold_path"], index=False)
                    with st.spinner("🪐🚀 Engaging the wormhole drive..."):
                        st.session_state.state = approve_gold(state)
                    add_xp(500)
                    add_achievement("Wormhole Master")
                    add_achievement("Galactic Legend")
                    trigger_fx("sun")
                    st.success("🎉🎉🎉 JUMPED! You've completed the voyage!")
                    st.rerun()
            with col3:
                if st.button("💥 ABORT MISSION", key="gold_reject", width='stretch'):
                    st.session_state.state = None
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # LEG 4: MISSION COMPLETE
        if state["status"] == "complete":
            st.markdown('<div class="phase-card">', unsafe_allow_html=True)

            if st.session_state.get("celebrated_run") != state["run_id"]:
                st.session_state.celebrated_run = state["run_id"]
                st.markdown(f"""
                <div class="boss-encounter" style="border-style: solid;"><span class="cosmic-watermark">🌟</span>
                    <h3>🎉 SURPRISE! MISSION LOG UNSEALED 🎉</h3>
                    <p style="color: white; font-size: 16px; margin: 10px 0;">
                        You earned <b>{st.session_state.xp} XP</b> and unlocked
                        <b>{len(st.session_state.achievements)} medals</b> this mission!
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('# 🏆 MISSION COMPLETE! 🏆')
            st.markdown('### 🛰️ You have charted the entire voyage!')

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

            st.markdown('#### 📈 Star Chart Data')
            for p in state.get("gold_output_paths", []):
                try:
                    df = pd.read_parquet(p)
                    with st.expander(f"🪐 {Path(p).stem}"):
                        st.dataframe(df, width='stretch', hide_index=True)
                except: pass

            st.divider()

            st.markdown('#### 🔧 Mission Records')
            tab1, tab2, tab3 = st.tabs(["SQL Log", "Traces", "Audit"])
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
                "💾 Download Mission Report",
                data=json.dumps(state, indent=2, default=str),
                file_name=f"mission_{state['run_id']}.json",
                mime="application/json",
                width='stretch',
            )

            st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL: MISSION LOG + DEEP SPACE COMMS
# ═════════════════════════════════════════════════════════════════════════════
with col_chat:
    state = st.session_state.state
    status = state["status"] if state else None
    icon, tip = PHASE_TIPS.get(status, PHASE_TIPS[None])

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
        '<div class="chat-container"><div class="chat-header">📡 MISSION LOG</div>'
        f'<div class="chat-messages"><div class="log-track" style="animation-duration: {max(10, len(log_items) * 4)}s">'
        f'{"".join(log_items)}{"".join(log_items)}'
        '</div></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 📡 Ping Deep Space Comms")
    gold_paths = state.get("gold_output_paths") if state else None

    if not gold_paths:
        st.caption("🔒 Unlocks after you jump the Wormhole Core. Uses exactly 1 AI call per question — no token waste.")
    elif st.session_state.show_restart_prompt:
        st.warning("🛰️ You've asked 5 questions! Launch a fresh mission, or keep exploring this one?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("🔄 Yes, New Mission", width='stretch'):
                reset_quest()
                st.rerun()
        with col_no:
            if st.button("🙅 No, Keep Exploring", width='stretch'):
                st.session_state.show_restart_prompt = False
                st.session_state.oracle_prompted = False  # allows the nudge to re-trigger after 5 more questions
                st.rerun()
    else:
        oracle_q = st.text_input(
            "Ask a question about your data...", placeholder="e.g. Which region has the highest revenue?",
            key="oracle_input", label_visibility="collapsed",
        )
        if st.button("📡 Send Transmission", width='stretch', disabled=not oracle_q):
            with st.spinner("📡 Transmitting to deep space comms (1 AI call)..."):
                try:
                    st.session_state.oracle_answer = ask_question(gold_paths, oracle_q, state["run_id"])
                    add_xp(25)
                    st.session_state.oracle_query_count += 1
                except Exception as exc:
                    st.session_state.oracle_answer = {"answer": f"⚠️ Signal lost: {exc}", "sql": None, "rows": [], "chart": None}
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
