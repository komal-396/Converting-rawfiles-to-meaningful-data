"""
STTM Generator - Deterministic transformation rule generation.
Removed LLM to avoid tool hallucination/corruption issues.
"""
import json
from pathlib import Path
from typing import Dict

import pandas as pd

from core.config import STTM_DIR
from core.observability import AgentTrace

REVENUE_HINTS = ("total_amount", "revenue", "sales", "amount")
CATEGORY_HINTS = ("category", "region", "store", "segment")


def _standardize_name(col: str) -> str:
    """Normalize column name to snake_case."""
    return "".join(ch if ch.isalnum() else "_" for ch in col.strip().lower()).strip("_")


def run_sttm_agent(
    layer: str,
    run_id: str,
    scratchpad: dict,
    business_intent: str = "",
    profile: dict | None = None,
    bronze_schemas: dict | None = None,
    silver_schemas: dict | None = None,
) -> str:
    """Generate STTM for a layer (bronze/silver/gold) - Deterministic, no LLM."""
    trace = AgentTrace("sttm_generator", run_id).set_input(layer=layer)
    
    try:
        if layer == "bronze":
            path = _generate_bronze_sttm(run_id, scratchpad, profile or {})
        elif layer == "silver":
            path = _generate_silver_sttm(run_id, scratchpad, bronze_schemas or {})
        elif layer == "gold":
            path = _generate_gold_sttm(run_id, scratchpad, silver_schemas or {})
        else:
            raise ValueError(f"Unknown layer: {layer}")
        
        trace.set_output(**{f"sttm_{layer}_path": path}).complete()
        return path
    except Exception as exc:
        print(f"[STTM ERROR] {layer}: {exc}")
        trace.fail(exc)
        raise


def _generate_bronze_sttm(run_id: str, scratchpad: dict, profile: dict) -> str:
    """Generate Bronze STTM: rename and cast dtypes."""
    rows = []
    for fname, info in profile.get("files", {}).items():
        for col, stats in info["columns"].items():
            target = _standardize_name(col)
            cast = "datetime" if stats["semantic_meaning"] == "date/time" else (
                "numeric" if stats["dtype"].startswith(("int", "float")) else "string"
            )
            rows.append({
                "source_file": fname,
                "source_col": col,
                "target_col": target,
                "dtype_cast": cast,
                "transformation_logic": f"rename → {target}; cast → {cast}",
            })
    
    df = pd.DataFrame(rows)
    out_dir = STTM_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"sttm_bronze_{run_id}.csv"
    df.to_csv(path, index=False)
    scratchpad["sttm_bronze_path"] = str(path)
    print(f"✅ [BRONZE] {len(df)} transformation rules")
    return str(path)


def _generate_silver_sttm(run_id: str, scratchpad: dict, bronze_schemas: dict) -> str:
    """Generate Silver STTM: null handling, dedup, type casting."""
    rows = []
    for fname, cols in bronze_schemas.items():
        for col, dtype in cols.items():
            is_numeric = str(dtype).startswith(("int", "float"))
            null_strategy = "impute_median" if is_numeric else "impute_unknown"
            rows.append({
                "source_file": fname,
                "target_col": col,
                "null_strategy": null_strategy,
                "dedup": "True",
                "transformation_logic": f"{null_strategy} → drop_duplicates",
            })
    
    df = pd.DataFrame(rows)
    out_dir = STTM_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"sttm_silver_{run_id}.csv"
    df.to_csv(path, index=False)
    scratchpad["sttm_silver_path"] = str(path)
    print(f"✅ [SILVER] {len(df)} transformation rules")
    return str(path)


def _generate_gold_sttm(run_id: str, scratchpad: dict, silver_schemas: dict) -> str:
    """Generate Gold STTM: join rules + aggregations."""
    rows = []
    all_cols: set = set()
    for cols in silver_schemas.values():
        all_cols |= set(cols.keys())
    
    # Exclude surrogate keys to avoid false positives
    candidate_cols = {c for c in all_cols if not c.startswith("pk_") and not c.endswith("_id")}
    
    revenue_col = next((c for c in candidate_cols if any(h in c for h in REVENUE_HINTS)), None)
    group_cols = [c for c in candidate_cols if any(h in c for h in CATEGORY_HINTS)]
    
    if revenue_col:
        for group_col in group_cols or ["category"]:
            rows.append({
                "target_table": f"gold_revenue_by_{group_col}",
                "rule_type": "aggregate",
                "group_by": group_col,
                "agg_col": revenue_col,
                "agg_func": "sum",
                "transformation_logic": f"GROUP BY {group_col} → SUM({revenue_col})",
            })
    
    rows.append({
        "target_table": "gold_transactions",
        "rule_type": "join",
        "group_by": "all_ids",
        "agg_col": "n/a",
        "agg_func": "n/a",
        "transformation_logic": "OUTER JOIN on *_id columns",
    })
    
    df = pd.DataFrame(rows)
    out_dir = STTM_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"sttm_gold_{run_id}.csv"
    df.to_csv(path, index=False)
    scratchpad["sttm_gold_path"] = str(path)
    print(f"✅ [GOLD] {len(df)} transformation rules")
    return str(path)
