"""Agent 1: Profiler — understands raw data structure/quality. Deterministic (no LLM).

Rule-based statistics only; there is no natural-language reasoning required here,
so an LLM tool-calling loop would just burn tokens/rate-limit budget for nothing.
"""
import json
from pathlib import Path
from typing import List

import pandas as pd

from core.config import PROFILES_DIR
from core.io_utils import read_any
from core.observability import AgentTrace


def _infer_semantic_meaning(col: str) -> str:
    c = col.lower()
    if c.endswith("_id") or c == "id":
        return "identifier"
    if "date" in c or "time" in c:
        return "date/time"
    if any(k in c for k in ("price", "amount", "cost", "revenue", "total")):
        return "monetary value"
    if any(k in c for k in ("qty", "quantity", "units")):
        return "count/quantity"
    if any(k in c for k in ("region", "city", "state", "country", "address")):
        return "geography"
    if "name" in c or "segment" in c or "method" in c or "category" in c:
        return "categorical / descriptive text"
    return "unclassified"


def run_profiler_agent(file_paths: List[str], business_intent: str, run_id: str, scratchpad: dict) -> str:
    """Compute full column statistics for all files and save profile_combined_{run_id}.json."""
    trace = AgentTrace("profiler_agent", run_id).set_input(file_paths=file_paths, business_intent=business_intent)
    try:
        file_column_sets = {}
        columns_report = {}

        for path in file_paths:
            df = read_any(path)
            fname = Path(path).name
            file_column_sets[fname] = set(df.columns)
            col_stats = {}
            for col in df.columns:
                series = df[col]
                stats = {
                    "dtype": str(series.dtype),
                    "null_count": int(series.isna().sum()),
                    "null_pct": round(float(series.isna().mean() * 100), 2),
                    "unique_count": int(series.nunique()),
                    "semantic_meaning": _infer_semantic_meaning(col),
                    "sample_values": series.dropna().astype(str).head(3).tolist(),
                }
                if pd.api.types.is_numeric_dtype(series):
                    stats.update(
                        min=float(series.min()) if series.notna().any() else None,
                        max=float(series.max()) if series.notna().any() else None,
                        mean=round(float(series.mean()), 2) if series.notna().any() else None,
                    )
                col_stats[col] = stats
            columns_report[fname] = {"row_count": len(df), "columns": col_stats}

        all_files = list(file_column_sets.keys())
        join_keys = []
        for i in range(len(all_files)):
            for j in range(i + 1, len(all_files)):
                shared = file_column_sets[all_files[i]] & file_column_sets[all_files[j]]
                for col in shared:
                    join_keys.append({"column": col, "between": [all_files[i], all_files[j]]})

        quality_notes = []
        for fname, report in columns_report.items():
            for col, stats in report["columns"].items():
                if stats["null_pct"] > 10:
                    quality_notes.append(f"{fname}.{col}: {stats['null_pct']}% nulls")
                if stats["unique_count"] == 1:
                    quality_notes.append(f"{fname}.{col}: constant column (low cardinality)")

        profile = {
            "run_id": run_id,
            "files": columns_report,
            "join_keys": join_keys,
            "quality_notes": quality_notes,
        }

        out_dir = PROFILES_DIR / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"profile_combined_{run_id}.json"
        path.write_text(json.dumps(profile, indent=2, default=str), encoding="utf-8")
        scratchpad["profile_path"] = str(path)

        trace.set_output(profile_path=str(path), join_keys=join_keys, quality_notes=quality_notes).complete()
        print(f"✅ [PROFILER] {len(file_paths)} files profiled, {len(join_keys)} join keys found")
    except Exception as exc:  # noqa: BLE001
        trace.fail(exc)
        raise

    return scratchpad["profile_path"]
