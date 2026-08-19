"""Generic raw-file reader so the pipeline isn't locked to CSV only."""
from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = [".csv", ".tsv", ".txt", ".xlsx", ".xls", ".json", ".parquet"]


def read_any(path: str) -> pd.DataFrame:
    """Read a raw data file into a DataFrame, dispatching on file extension."""
    ext = Path(path).suffix.lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext == ".tsv":
        return pd.read_csv(path, sep="\t")
    if ext == ".txt":
        return pd.read_csv(path, sep=None, engine="python")
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if ext == ".json":
        return pd.read_json(path)
    if ext == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported file type: {ext}")
