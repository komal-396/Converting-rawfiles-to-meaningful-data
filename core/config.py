"""Central configuration for the Medallion agentic pipeline."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # medallion-pipeline/
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))

# --- Data lake layout ---
DATA_DIR = BASE_DIR / "data"
LANDING_DIR = DATA_DIR / "landing"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
PROFILES_DIR = DATA_DIR / "profiles"
STTM_DIR = DATA_DIR / "sttm"
TRACES_DIR = DATA_DIR / "traces"

# --- Output layout ---
REPORTS_DIR = DATA_DIR / "reports"
AUDIT_DIR = BASE_DIR / "audit_logs"
CHROMA_DIR = BASE_DIR / ".chroma"

# --- User accounts (per-account login + saved quest progress) ---
USERS_DIR = DATA_DIR / "users"
USERS_FILE = USERS_DIR / "users.json"

for _d in (
    LANDING_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR,
    PROFILES_DIR, STTM_DIR, TRACES_DIR, REPORTS_DIR, AUDIT_DIR, CHROMA_DIR, USERS_DIR,
):
    _d.mkdir(parents=True, exist_ok=True)

# --- Data quality thresholds ---
MAX_NULL_RATIO_DROP_COLUMN = float(os.getenv("MAX_NULL_RATIO_DROP_COLUMN", "0.6"))
OUTLIER_ZSCORE_THRESHOLD = float(os.getenv("OUTLIER_ZSCORE_THRESHOLD", "3.0"))
