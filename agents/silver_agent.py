"""Agent 4: Silver Agent — cleanses Bronze Parquet using the approved Silver STTM.

Deterministic execution: rules (null strategy, dedup) come from the human-approved STTM.
"""
import json
from pathlib import Path
from typing import List

import pandas as pd

from core.config import SILVER_DIR
from core.observability import AgentTrace


def run_silver_agent(bronze_paths: List[str], sttm_silver_path: str, run_id: str, scratchpad: dict, business_intent: str = "") -> List[str]:
    """Cleanse Bronze data per the approved STTM: impute nulls, dedupe, inject a surrogate key."""
    trace = AgentTrace("silver_agent", run_id).set_input(bronze_paths=bronze_paths, sttm_silver_path=sttm_silver_path)
    try:
        sttm_df = pd.read_csv(sttm_silver_path)
        out_dir = SILVER_DIR / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        output_paths = []

        for path in bronze_paths:
            bronze_name = Path(path).name
            rules = sttm_df[sttm_df["source_file"] == bronze_name]
            df = pd.read_parquet(path)

            for _, rule in rules.iterrows():
                col = rule["target_col"]
                if col not in df.columns:
                    continue
                if rule["null_strategy"] == "impute_median" and pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
                elif rule["null_strategy"] == "impute_unknown":
                    if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
                        df[col] = df[col].fillna("unknown")

            if rules["dedup"].any():
                df = df.drop_duplicates()

            stem = bronze_name.replace("_bronze.parquet", "")
            df.insert(0, f"pk_{stem}_silver_id", range(1, len(df) + 1))

            out_path = out_dir / f"{stem}_silver.parquet"
            df.to_parquet(out_path, index=False)
            output_paths.append(str(out_path))

        scratchpad["silver_output_paths"] = output_paths
        trace.set_output(silver_output_paths=output_paths).complete()
        print(f"✅ [SILVER] {len(output_paths)} files cleansed")
    except Exception as exc:  # noqa: BLE001
        trace.fail(exc)
        raise

    return scratchpad["silver_output_paths"]
