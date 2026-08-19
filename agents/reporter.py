"""Agent 6: Reporter — answers the business question over Gold tables.

LLM usage is limited to TWO plain chat completions: one to write SQL from the
business question, one to summarize the actual result rows in plain English.
No tool-calling / ReAct loop -> no risk of corrupted tool-call tokens, and far fewer
tokens burned per run (2 calls instead of a multi-turn agent loop).
"""
import json
import re
from pathlib import Path
from typing import List

import duckdb
import pandas as pd
import plotly.express as px

from core.llm import get_llm, is_llm_configured
from core.memory import store_document
from core.observability import AgentTrace
from core.retry import invoke_with_retry

SYSTEM_PROMPT = (
    "You are a SQL analyst. Given table schemas and a business question, write ONE "
    "ANSI SQL query (DuckDB dialect) that answers it. Only reference the tables/columns "
    "given — never invent columns or use outside knowledge. Reply with ONLY the SQL query, "
    "no explanation, no markdown fences, no commentary."
)


def _load_gold_tables(gold_paths: List[str]) -> dict:
    return {Path(p).stem: pd.read_parquet(p) for p in gold_paths}


def _schema_context(tables: dict) -> str:
    lines = []
    for name, df in tables.items():
        cols = ", ".join(f"{c} ({t})" for c, t in df.dtypes.astype(str).items())
        lines.append(f"TABLE {name} [{len(df)} rows]: {cols}")
    return "\n".join(lines)


def _extract_sql(text: str) -> str:
    """Strip markdown fences/commentary the LLM might add despite instructions."""
    text = re.sub(r"```sql|```", "", text, flags=re.IGNORECASE).strip()
    # If the model added a leading sentence, keep from the first SELECT/WITH onward.
    match = re.search(r"(select|with)\s", text, flags=re.IGNORECASE)
    return text[match.start():].strip() if match else text


def _default_query(tables: dict) -> str:
    """Deterministic fallback when the LLM is unavailable or fails twice."""
    name = next(iter(tables))
    return f"SELECT * FROM {name} LIMIT 20"


def _build_chart(rows: list[dict]):
    """Best-effort bar chart from the query result: first col = category, second = value."""
    if not rows:
        return None
    df = pd.DataFrame(rows)
    if df.shape[1] < 2:
        return None
    x_col, y_col = df.columns[0], df.columns[1]
    if not pd.api.types.is_numeric_dtype(df[y_col]):
        return None
    return px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")


def _generate_sql(question: str, schema_context: str, error_hint: str = "") -> str:
    """One plain chat completion -> SQL text. No tools, no function calling."""
    llm = get_llm()
    user_msg = f"Table schemas:\n{schema_context}\n\nQuestion: {question}"
    if error_hint:
        user_msg += f"\n\nThe previous query failed with: {error_hint}\nFix it."
    messages = [("system", SYSTEM_PROMPT), ("user", user_msg)]
    result = invoke_with_retry(llm, messages)
    return _extract_sql(result.content)


SUMMARY_PROMPT = (
    "You are a data analyst. Given a business question, the SQL query used, and the "
    "resulting rows, write a short (1-3 sentence) plain-English answer to the question "
    "using ONLY the actual values from the rows provided — never use outside/general "
    "knowledge. Be direct and specific (name the numbers). Format every monetary amount "
    "with a '$' sign, thousands separators, and exactly 2 decimal places (e.g. $52,083.35, "
    "never 52083.350000000006 or 52083). Non-monetary counts/quantities can stay as plain "
    "numbers. Plain text only: no markdown, no SQL, no commentary about the process."
)


def _round_floats(rows: list[dict]) -> list[dict]:
    """Round floats to 2dp before showing the LLM raw query results — avoids float noise
    like 52083.350000000006 leaking into the summarized answer regardless of prompting."""
    cleaned = []
    for row in rows:
        cleaned.append({k: (round(v, 2) if isinstance(v, float) else v) for k, v in row.items()})
    return cleaned


def _summarize_answer(question: str, sql: str, rows: list[dict]) -> str:
    """One plain chat completion -> natural-language answer grounded in the query result."""
    llm = get_llm()
    preview = json.dumps(_round_floats(rows[:20]), default=str)
    user_msg = f"Question: {question}\n\nSQL used: {sql}\n\nResult rows: {preview}"
    messages = [("system", SUMMARY_PROMPT), ("user", user_msg)]
    result = invoke_with_retry(llm, messages)
    return result.content.strip()


def _fallback_answer(rows: list[dict]) -> str:
    """Deterministic fallback if the LLM is unavailable or the summary call fails."""
    if not rows:
        return "No rows matched this question."
    rows = _round_floats(rows)
    if len(rows) == 1 and len(rows[0]) <= 2:
        return " ".join(f"{k}: {v}" for k, v in rows[0].items())
    return f"Found {len(rows)} matching row(s) — see the table/chart below."


def run_reporter_agent(gold_paths: List[str], business_intent: str, run_id: str) -> dict:
    """Answer the business question over Gold tables; returns {'answer', 'sql', 'rows', 'chart'}."""
    trace = AgentTrace("reporter_agent", run_id).set_input(gold_paths=gold_paths, business_intent=business_intent)
    try:
        tables = _load_gold_tables(gold_paths)
        con = duckdb.connect(database=":memory:")
        for name, df in tables.items():
            con.register(name, df)
        schema_context = _schema_context(tables)

        sql, result_df = None, None
        if is_llm_configured():
            for attempt in range(2):
                try:
                    sql = _generate_sql(business_intent, schema_context, error_hint="" if attempt == 0 else str(last_error))
                    result_df = con.execute(sql).fetchdf()
                    break
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    sql, result_df = None, None
        if result_df is None:
            sql = _default_query(tables)
            result_df = con.execute(sql).fetchdf()

        rows = result_df.head(50).to_dict(orient="records")
        rows = _round_floats(rows)
        chart = _build_chart(rows)

        if is_llm_configured():
            try:
                answer = _summarize_answer(business_intent, sql, rows)
            except Exception:  # noqa: BLE001
                answer = _fallback_answer(rows)
        else:
            answer = _fallback_answer(rows)

        report = {"answer": answer, "sql": sql, "rows": rows}
        store_document(
            text=f"business_intent: {business_intent}\nanswer: {answer}",
            metadata={"run_id": run_id, "sql": sql or ""},
        )
        trace.set_output(answer=answer, sql=sql).complete()
        print(f"✅ [REPORTER] Answered via SQL: {sql[:80] if sql else 'n/a'}...")
        return {**report, "chart": chart}
    except Exception as exc:  # noqa: BLE001
        trace.fail(exc)
        raise


def ask_question(gold_paths: List[str], question: str, run_id: str) -> dict:
    """On-demand ad hoc Q&A over Gold tables (used by the UI's 'Ask the Oracle' panel)."""
    return run_reporter_agent(gold_paths, question, run_id)
