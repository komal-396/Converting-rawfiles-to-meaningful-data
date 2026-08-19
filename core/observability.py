"""Detailed per-agent execution traces: input, plan, tool calls, reasoning, output."""
import json
import time
from datetime import datetime, timezone
from typing import Any, List

from core.config import TRACES_DIR


class AgentTrace:
    """Captures what one agent thought and did during a single pipeline run."""

    def __init__(self, agent_name: str, run_id: str):
        self.agent_name = agent_name
        self.run_id = run_id
        self._start_time = time.time()
        self.trace: dict = {
            "agent": agent_name,
            "run_id": run_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "input": {},
            "plan": None,
            "tool_calls": [],
            "reasoning_steps": [],
            "output": {},
            "duration_seconds": None,
            "status": None,
        }

    def set_input(self, **kwargs: Any) -> "AgentTrace":
        self.trace["input"] = kwargs
        return self

    def set_plan(self, plan_str: str) -> "AgentTrace":
        self.trace["plan"] = plan_str
        return self

    def set_output(self, **kwargs: Any) -> "AgentTrace":
        self.trace["output"] = kwargs
        return self

    def extract_from_messages(self, messages: List[Any]) -> "AgentTrace":
        """Walk a LangGraph message history and populate plan/tool_calls/reasoning_steps."""
        for message in messages:
            msg_type = type(message).__name__

            if msg_type == "HumanMessage":
                self.trace["reasoning_steps"].append({"type": "task_input", "content": message.content})

            elif msg_type == "AIMessage":
                tool_calls = getattr(message, "tool_calls", None) or []
                if tool_calls:
                    self.trace["tool_calls"].extend(tool_calls)
                content = getattr(message, "content", "")
                if content:
                    self.trace["reasoning_steps"].append({"type": "ai_reasoning", "content": content})
                    if self.trace["plan"] is None:
                        self.trace["plan"] = content

            elif msg_type == "ToolMessage":
                self.trace["reasoning_steps"].append(
                    {"type": "tool_result", "tool_call_id": getattr(message, "tool_call_id", None), "content": message.content}
                )

        return self

    def complete(self, status: str = "success") -> "AgentTrace":
        self.trace["duration_seconds"] = round(time.time() - self._start_time, 3)
        self.trace["status"] = status

        path = TRACES_DIR / f"trace_{self.agent_name}_{self.run_id[:8]}.json"
        path.write_text(json.dumps(self.trace, indent=2, default=str), encoding="utf-8")

        print(f"[trace] {self.agent_name} ({self.run_id[:8]}) · {status} · {self.trace['duration_seconds']}s")
        return self

    def fail(self, error: Exception | str) -> "AgentTrace":
        self.trace["output"]["error"] = str(error)
        return self.complete(status="failed")
