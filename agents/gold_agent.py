"""Agent 5: Gold Agent — materializes analytics tables using the approved Gold STTM.

Deterministic execution: joins + groupby/agg rules come from the human-approved STTM.
"""
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

from core.config import GOLD_DIR
from core.observability import AgentTrace


def _load_silver_tables(silver_paths: List[str]) -> Dict[str, pd.DataFrame]:
    return {Path(p).name.replace("_silver.parquet", ""): pd.read_parquet(p) for p in silver_paths}


def _build_gold_transactions(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Outer-join all Silver tables on whichever *_id columns they share with the fact table."""
    id_cols = {name: [c for c in df.columns if c.endswith("_id") and not c.startswith("pk_")] for name, df in tables.items()}
    fact_name = max(id_cols, key=lambda n: len(id_cols[n])) if id_cols else next(iter(tables))
    joined = tables[fact_name].copy()

    for name, df in tables.items():
        if name == fact_name:
            continue
        shared = [c for c in id_cols[name] if c in joined.columns]
        if shared:
            joined = joined.merge(df, how="outer", on=shared, suffixes=("", f"_{name}"))
    return joined


def run_gold_agent(silver_paths: List[str], sttm_gold_path: str, run_id: str, scratchpad: dict, business_intent: str = "") -> List[str]:
    """Join Silver tables, then apply groupby().agg() rules; write one Parquet per target table."""
    trace = AgentTrace("gold_agent", run_id).set_input(silver_paths=silver_paths, sttm_gold_path=sttm_gold_path)
    try:
        tables = _load_silver_tables(silver_paths)
        sttm_df = pd.read_csv(sttm_gold_path)
        out_dir = GOLD_DIR / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        output_paths = []

        joined = _build_gold_transactions(tables)
        joined.insert(0, "pk_gold_id", range(1, len(joined) + 1))

        join_path = out_dir / "gold_transactions.parquet"
        joined.to_parquet(join_path, index=False)
        output_paths.append(str(join_path))

        for _, rule in sttm_df[sttm_df["rule_type"] == "aggregate"].iterrows():
            group_col, agg_col, agg_func = rule["group_by"], rule["agg_col"], rule["agg_func"]
            if group_col not in joined.columns or agg_col not in joined.columns:
                continue
            agg_df = joined.groupby(group_col)[agg_col].agg(agg_func).reset_index()
            agg_df.insert(0, "pk_gold_id", range(1, len(agg_df) + 1))
            path = out_dir / f"{rule['target_table']}.parquet"
            agg_df.to_parquet(path, index=False)
            output_paths.append(str(path))

        scratchpad["gold_output_paths"] = output_paths
        trace.set_output(gold_output_paths=output_paths).complete()
        print(f"✅ [GOLD] {len(output_paths)} tables materialized")
    except Exception as exc:  # noqa: BLE001
        trace.fail(exc)
        raise

    return scratchpad["gold_output_paths"]
