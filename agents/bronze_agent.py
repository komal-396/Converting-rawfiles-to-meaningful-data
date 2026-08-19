"""Agent 3: Bronze Agent — ingests raw CSV -> Parquet using the approved Bronze STTM.

Deterministic execution: the STTM CSV (human-approved) fully specifies the rename/cast
rules, so there is nothing for an LLM to decide here.
"""
import json
from pathlib import Path
from typing import List

import pandas as pd

from core.config import BRONZE_DIR
from core.io_utils import read_any
from core.observability import AgentTrace


def run_bronze_agent(file_paths: List[str], sttm_bronze_path: str, run_id: str, scratchpad: dict, business_intent: str = "") -> List[str]:
    """Apply the approved Bronze STTM rename/cast rules; write *_bronze.parquet."""
    trace = AgentTrace("bronze_agent", run_id).set_input(file_paths=file_paths, sttm_bronze_path=sttm_bronze_path)
    try:
        sttm_df = pd.read_csv(sttm_bronze_path)
        out_dir = BRONZE_DIR / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        output_paths = []

        for path in file_paths:
            fname = Path(path).name
            rules = sttm_df[sttm_df["source_file"] == fname]
            df = read_any(path)

            rename_map = dict(zip(rules["source_col"], rules["target_col"]))
            df = df.rename(columns=rename_map)

            for _, rule in rules.iterrows():
                target = rule["target_col"]
                if target not in df.columns:
                    continue
                if rule["dtype_cast"] == "numeric":
                    df[target] = pd.to_numeric(df[target], errors="coerce")
                elif rule["dtype_cast"] == "datetime":
                    df[target] = pd.to_datetime(df[target], errors="coerce", format="mixed")

            stem = Path(fname).stem
            out_path = out_dir / f"{stem}_bronze.parquet"
            df.to_parquet(out_path, index=False)
            output_paths.append(str(out_path))

        scratchpad["bronze_output_paths"] = output_paths
        trace.set_output(bronze_output_paths=output_paths).complete()
        print(f"✅ [BRONZE] {len(output_paths)} files ingested")
    except Exception as exc:  # noqa: BLE001
        trace.fail(exc)
        raise

    return scratchpad["bronze_output_paths"]
