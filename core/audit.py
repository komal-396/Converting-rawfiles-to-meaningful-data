"""Append-only audit trail of what each agent did, per pipeline run."""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from core.config import AUDIT_DIR


class AuditLogger:
    """Per-run JSONL audit trail: one line per agent action."""

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or uuid.uuid4().hex
        self.path = AUDIT_DIR / f"{self.run_id}.jsonl"

    def log(self, agent: str, action: str, **kwargs: Any) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "agent": agent,
            "action": action,
            **kwargs,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def get_logs(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


def log_action(run_id: str, agent: str, action: str, details: dict | None = None) -> None:
    """Backward-compatible helper used by pipeline agents; wraps AuditLogger."""
    AuditLogger(run_id).log(agent, action, **(details or {}))
