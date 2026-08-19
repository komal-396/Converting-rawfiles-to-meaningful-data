"""Retry helper for Groq's free-tier rate limits (429 tokens-per-minute)."""
import re
import time


def invoke_with_retry(agent, payload: dict, max_retries: int = 3):
    """Invoke a LangGraph agent, retrying on Groq 429 rate-limit errors."""
    for attempt in range(max_retries + 1):
        try:
            return agent.invoke(payload)
        except Exception as exc:  # noqa: BLE001 - inspect any exception for a 429 rate-limit
            message = str(exc)
            print(f"[RETRY ATTEMPT {attempt + 1}/{max_retries + 1}] {type(exc).__name__}")
            if "rate_limit" not in message and "429" not in message:
                print(f"[RETRY] Non-rate-limit error, re-raising: {message[:200]}")
                raise
            if attempt == max_retries:
                print(f"[RETRY] Max retries exhausted, re-raising rate-limit error")
                raise
            match = re.search(r"try again in ([\d.]+)s", message)
            wait_s = float(match.group(1)) + 1 if match else 5.0
            print(f"[RETRY] Rate limited, waiting {wait_s}s...")
            time.sleep(wait_s)
    raise RuntimeError("unreachable")
