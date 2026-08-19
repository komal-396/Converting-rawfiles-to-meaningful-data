"""Utility to inspect audit logs and execution traces for a given pipeline run."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import AUDIT_DIR, TRACES_DIR  # noqa: E402


def show_run(run_id: str) -> None:
    audit_path = AUDIT_DIR / f"{run_id}.jsonl"

    print(f"=== Audit log: {audit_path} ===")
    if audit_path.exists():
        for line in audit_path.read_text(encoding="utf-8").splitlines():
            print(line)
    else:
        print("(no audit log found)")

    trace_files = sorted(TRACES_DIR.glob(f"trace_*_{run_id[:8]}.json"))
    print(f"\n=== Agent traces for {run_id[:8]} ===")
    if not trace_files:
        print("(no traces found)")
    for tf in trace_files:
        print(f"--- {tf.name} ---")
        print(json.dumps(json.loads(tf.read_text(encoding="utf-8")), indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tools/inspect_run.py <run_id>")
        sys.exit(1)
    show_run(sys.argv[1])
