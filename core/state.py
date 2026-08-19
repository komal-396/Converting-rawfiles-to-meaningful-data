"""PipelineState — the dict handed BETWEEN phases (across Streamlit reruns).

Per-phase, ephemeral tool outputs live in a plain `scratchpad` dict instead
(see agents/orchestrator.py) and are copied into PipelineState once a phase
completes; the scratchpad itself is discarded after that.
"""
from typing import Any, Dict, List, TypedDict


class PipelineState(TypedDict, total=False):
    # --- run context ---
    run_id: str
    uploaded_files: List[str]  # landing-zone CSV paths
    business_intent: str

    # --- Phase 1: Profiler + Bronze STTM ---
    profile_path: str
    sttm_bronze_path: str

    # --- Phase 2: Bronze ingestion + Silver STTM ---
    bronze_output_paths: List[str]
    sttm_silver_path: str

    # --- Phase 3: Silver cleansing + Gold STTM ---
    silver_output_paths: List[str]
    sttm_gold_path: str

    # --- Phase 4: Gold materialization + report ---
    gold_output_paths: List[str]
    report: Dict[str, Any]

    # --- control flow ---
    # idle | awaiting_bronze_approval | awaiting_silver_approval |
    # awaiting_gold_approval | complete | failed
    status: str
    errors: List[str]
