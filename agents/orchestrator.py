"""The Supervisor — coordinates the 4 human-in-the-loop phases of the pipeline.

WITHIN a phase, agents share a throwaway `scratchpad` dict (closures write into it).
BETWEEN phases, only PipelineState survives (Streamlit reruns lose local variables).
"""
import json
from pathlib import Path
from typing import List

import pandas as pd

from agents.bronze_agent import run_bronze_agent
from agents.gold_agent import run_gold_agent
from agents.profiler import run_profiler_agent
from agents.reporter import run_reporter_agent
from agents.silver_agent import run_silver_agent
from agents.sttm_generator import run_sttm_agent
from core.audit import AuditLogger
from core.state import PipelineState


def _parquet_schemas(paths: List[str]) -> dict:
    return {Path(p).name: {c: str(t) for c, t in pd.read_parquet(p).dtypes.items()} for p in paths}


def start_pipeline(file_paths: List[str], business_intent: str, run_id: str) -> PipelineState:
    """Phase 1: Profiler profiles raw files -> STTM Agent generates Bronze STTM -> pause for approval."""
    audit = AuditLogger(run_id)
    audit.log("orchestrator", "phase1_start", files=[Path(p).name for p in file_paths])
    scratchpad: dict = {}
    try:
        profile_path = run_profiler_agent(file_paths, business_intent, run_id, scratchpad)
        profile = json.loads(Path(profile_path).read_text(encoding="utf-8"))
        sttm_bronze_path = run_sttm_agent("bronze", run_id, scratchpad, business_intent, profile=profile)
    except Exception as exc:  # noqa: BLE001
        audit.log("orchestrator", "phase1_failed", error=str(exc))
        return {"run_id": run_id, "uploaded_files": file_paths, "business_intent": business_intent, "status": "failed", "errors": [str(exc)]}

    audit.log("orchestrator", "phase1_complete", sttm_bronze_path=sttm_bronze_path)
    return {
        "run_id": run_id, "uploaded_files": file_paths, "business_intent": business_intent,
        "profile_path": profile_path, "sttm_bronze_path": sttm_bronze_path,
        "status": "awaiting_bronze_approval", "errors": [],
    }


def approve_bronze(state: PipelineState) -> PipelineState:
    """Phase 2: Bronze Agent ingests -> STTM Agent generates Silver STTM -> pause for approval."""
    audit = AuditLogger(state["run_id"])
    audit.log("orchestrator", "phase2_start")
    scratchpad: dict = {}
    try:
        bronze_paths = run_bronze_agent(
            state["uploaded_files"], state["sttm_bronze_path"], state["run_id"], scratchpad, state["business_intent"]
        )
        bronze_schemas = _parquet_schemas(bronze_paths)
        sttm_silver_path = run_sttm_agent(
            "silver", state["run_id"], scratchpad, state["business_intent"], bronze_schemas=bronze_schemas
        )
    except Exception as exc:  # noqa: BLE001
        audit.log("orchestrator", "phase2_failed", error=str(exc))
        return {**state, "status": "failed", "errors": state.get("errors", []) + [str(exc)]}

    audit.log("orchestrator", "phase2_complete", sttm_silver_path=sttm_silver_path)
    return {
        **state, "bronze_output_paths": bronze_paths, "sttm_silver_path": sttm_silver_path,
        "status": "awaiting_silver_approval",
    }


def approve_silver(state: PipelineState) -> PipelineState:
    """Phase 3: Silver Agent cleanses -> STTM Agent generates Gold STTM -> pause for approval."""
    audit = AuditLogger(state["run_id"])
    audit.log("orchestrator", "phase3_start")
    scratchpad: dict = {}
    try:
        silver_paths = run_silver_agent(
            state["bronze_output_paths"], state["sttm_silver_path"], state["run_id"], scratchpad, state["business_intent"]
        )
        silver_schemas = _parquet_schemas(silver_paths)
        sttm_gold_path = run_sttm_agent(
            "gold", state["run_id"], scratchpad, state["business_intent"], silver_schemas=silver_schemas
        )
    except Exception as exc:  # noqa: BLE001
        audit.log("orchestrator", "phase3_failed", error=str(exc))
        return {**state, "status": "failed", "errors": state.get("errors", []) + [str(exc)]}

    audit.log("orchestrator", "phase3_complete", sttm_gold_path=sttm_gold_path)
    return {
        **state, "silver_output_paths": silver_paths, "sttm_gold_path": sttm_gold_path,
        "status": "awaiting_gold_approval",
    }


def approve_gold(state: PipelineState) -> PipelineState:
    """Phase 4: Gold Agent materializes -> Reporter Agent answers the business question -> complete."""
    audit = AuditLogger(state["run_id"])
    audit.log("orchestrator", "phase4_start")
    scratchpad: dict = {}
    try:
        gold_paths = run_gold_agent(
            state["silver_output_paths"], state["sttm_gold_path"], state["run_id"], scratchpad, state["business_intent"]
        )
        report = run_reporter_agent(gold_paths, state["business_intent"], state["run_id"])
    except Exception as exc:  # noqa: BLE001
        audit.log("orchestrator", "phase4_failed", error=str(exc))
        return {**state, "status": "failed", "errors": state.get("errors", []) + [str(exc)]}

    audit.log("orchestrator", "phase4_complete", gold_output_paths=gold_paths)
    return {**state, "gold_output_paths": gold_paths, "report": report, "status": "complete"}
