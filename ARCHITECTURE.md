================================================================================
RETAIL MEDALLION PIPELINE — CODE STRUCTURE & ARCHITECTURE
================================================================================

📦 PROJECT LAYOUT
─────────────────────────────────────────────────────────────────────────────

medallion-pipeline/
│
├── app/
│   └── streamlit_app.py              ← USER-FACING: Tab-based web UI (5 tabs)
│
├── agents/                           ← AGENT LAYER: 6 ReAct agents + Supervisor
│   ├── orchestrator.py               ← Supervisor: coordinates 4 phases
│   ├── profiler.py                   ← Agent 1: analyzes raw CSV structure & quality
│   ├── sttm_generator.py             ← Agent 2: designs Bronze/Silver/Gold rules
│   ├── bronze_agent.py               ← Agent 3: ingests raw CSV → Parquet
│   ├── silver_agent.py               ← Agent 4: cleanses & dedupes
│   ├── gold_agent.py                 ← Agent 5: materializes analytics tables
│   └── reporter.py                   ← Agent 6: answers business questions via SQL
│
├── core/                             ← INFRASTRUCTURE LAYER
│   ├── config.py                     ← Paths, API keys, constants
│   ├── llm.py                        ← Groq LLM initialization
│   ├── state.py                      ← PipelineState TypedDict (inter-phase data)
│   ├── memory.py                     ← ChromaDB semantic memory store
│   ├── audit.py                      ← AuditLogger: logs every action
│   ├── observability.py              ← AgentTrace: captures agent reasoning
│   ├── retry.py                      ← Groq rate-limit retry handler
│   └── storage.py                    ← Parquet file I/O helpers
│
├── data/                             ← DATA LAKE
│   ├── landing/                      ← Raw CSV uploads (per run_id)
│   ├── bronze/                       ← Renamed & type-cast Parquet
│   ├── silver/                       ← Deduplicated & cleaned Parquet
│   ├── gold/                         ← Joined & aggregated Parquet (analytics-ready)
│   ├── profiles/                     ← Profiler JSON (structure, nulls, join keys)
│   ├── sttm/                         ← Generated transformation rules (CSV)
│   ├── traces/                       ← Agent reasoning traces (JSON)
│   └── reports/                      ← HTML reports (future)
│
├── tests/
│   └── test_agents_helpers.py        ← Unit tests for pure helper functions
│
├── .env                              ← Local secrets (GROQ_API_KEY)
├── .env.example                      ← Template for .env
└── requirements.txt                  ← Python dependencies

================================================================================
CORE CONCEPTS
─────────────────────────────────────────────────────────────────────────────

1️⃣  MEDALLION ARCHITECTURE (Data Transformation)
   ───────────────────────────────────────────────
   BRONZE (Layer 1):  Raw CSV → Parquet (rename, type-cast only)
   SILVER (Layer 2):  Bronze → Cleaned Parquet (nulls handled, deduped)
   GOLD (Layer 3):    Silver → Analytics-ready (joined, aggregated tables)
   
   Each layer is INDEPENDENT — a human approves the transformation rules
   before the next layer executes.

2️⃣  4-PHASE WORKFLOW (Human-in-the-Loop)
   ────────────────────────────────────
   Phase 1:  Profiler → Bronze STTM (user approves before Phase 2)
   Phase 2:  Bronze Agent → Silver STTM (user approves before Phase 3)
   Phase 3:  Silver Agent → Gold STTM (user approves before Phase 4)
   Phase 4:  Gold Agent → Reporter (final report with SQL query & chart)

3️⃣  PIPELINESTATE (Per-Run Dictionary)
   ───────────────────────────────────
   Survives across Streamlit reruns (stored in session_state) and contains:
   - run_id, uploaded_files, business_intent
   - Phase 1: profile_path, sttm_bronze_path
   - Phase 2: bronze_output_paths, sttm_silver_path
   - Phase 3: silver_output_paths, sttm_gold_path
   - Phase 4: gold_output_paths, report
   - status: "idle" → "awaiting_bronze_approval" → ... → "complete"

4️⃣  SCRATCHPAD (Ephemeral, Within-Phase Dictionary)
   ─────────────────────────────────────────────
   Thrown away after each phase; shared by tools in the same agent via closure.
   Example:
      Phase 1 scratchpad = {
        "profile_path": "data/profiles/run123.json",
        "sttm_bronze_path": "data/sttm/run123/sttm_bronze_run123.csv"
      }
   These are copied into PipelineState, scratchpad is garbage-collected.

5️⃣  @tool DECORATOR & TOOL FACTORY PATTERN
   ────────────────────────────────────────
   Each agent's tools are created by a _make_*_tools(...) function that:
   - Accepts runtime parameters (file paths, run_id, etc.)
   - Defines @tool-decorated functions inside (visible to LLM)
   - Captures the scratchpad dict via closure (shared state)
   - Returns a list of tools
   
   Example (from profiler.py):
      def _make_profiler_tools(file_paths, run_id, scratchpad):
          @tool
          def inspect_files_tool() -> str:
              """Preview CSVs without full stats."""
              ...
          
          @tool
          def profiler_tool() -> str:
              """Compute full stats and save profile JSON."""
              scratchpad["profile_path"] = str(path)  # ← closure writes to scratchpad
              ...
          
          return [inspect_files_tool, profiler_tool]

================================================================================
AGENT LAYER DEEP DIVE
─────────────────────────────────────────────────────────────────────────────

AGENT = ReAct Loop (Think → Act → Observe → Verify)
Each agent is built with: create_react_agent(llm, tools, system_prompt)

PROFILER AGENT (agents/profiler.py)
───────────────────────────────────
  INPUT:   file_paths, business_intent, run_id, scratchpad
  TOOLS:   inspect_files_tool(), profiler_tool()
  PROCESS: 1. Read raw CSV shapes & columns (inspect_files_tool)
           2. Compute column statistics, nulls, join keys (profiler_tool)
           3. Write profile_combined_run_id.json
  OUTPUT:  scratchpad["profile_path"]
  RUNTIME: ~3-5 seconds (one LLM call, two tool calls)

STTM GENERATOR AGENT (agents/sttm_generator.py) — UNIFIED, 3 TOOLS
──────────────────────────────────────────────────
  Called THREE times (once per layer: bronze, silver, gold)
  
  INPUT:   layer ("bronze"|"silver"|"gold"), run_id, scratchpad, 
           business_intent, profile/bronze_schemas/silver_schemas
  TOOLS:   inspect_context_tool(), generate_bronze_sttm_tool(), 
           generate_silver_sttm_tool(), generate_gold_sttm_tool()
  PROCESS: 1. Read source context (raw/bronze/silver schemas)
           2. Design transformation rules (LLM-assisted)
           3. Write sttm_{layer}_{run_id}.csv
  OUTPUT:  scratchpad["sttm_{layer}_path"]
  RUNTIME: ~10-30 seconds per layer

  Rules CSV format (example for Bronze):
  ┌──────────────────┬────────────┬──────────┬──────────────────────────┐
  │ source_file      │ source_col │ target_col       │ dtype_cast        │
  ├──────────────────┼────────────┼──────────┼──────────────────────────┤
  │ sales_data.csv   │ txn_date   │ transaction_date │ datetime          │
  │ sales_data.csv   │ amount     │ total_amount     │ numeric           │
  │ sales_data.csv   │ product    │ product_name     │ string            │
  └──────────────────┴────────────┴──────────┴──────────────────────────┘

BRONZE AGENT (agents/bronze_agent.py)
──────────────────────────────
  INPUT:   file_paths, sttm_bronze_path, run_id, scratchpad, business_intent
  TOOLS:   inspect_task_tool(), bronze_ingestion_tool()
  PROCESS: 1. Read raw CSVs + approved STTM rules
           2. Rename columns & cast dtypes
           3. Write {stem}_bronze.parquet per input CSV
  OUTPUT:  scratchpad["bronze_output_paths"] = [paths/to/bronze/files]
  RUNTIME: ~20-30 seconds

SILVER AGENT (agents/silver_agent.py)
──────────────────────────
  INPUT:   bronze_paths, sttm_silver_path, run_id, scratchpad, business_intent
  TOOLS:   inspect_task_tool(), silver_ingestion_tool()
  PROCESS: 1. Read Bronze Parquet + approved STTM rules
           2. Handle nulls (impute median/mode), drop duplicates
           3. Inject surrogate key (pk_{stem}_silver_id)
           4. Write {stem}_silver.parquet
  OUTPUT:  scratchpad["silver_output_paths"]
  RUNTIME: ~40-60 seconds (depends on data size)

GOLD AGENT (agents/gold_agent.py)
──────────────────────
  INPUT:   silver_paths, sttm_gold_path, run_id, scratchpad, business_intent
  TOOLS:   inspect_task_tool(), gold_ingestion_tool()
  PROCESS: 1. Read Silver Parquet + approved STTM rules
           2. Outer-join all Silver tables on shared *_id columns
           3. Execute groupby().agg() rules from STTM
           4. Inject pk_gold_id surrogate key
           5. Write one Parquet per target table
  OUTPUT:  scratchpad["gold_output_paths"]
  RUNTIME: ~20-30 seconds

REPORTER AGENT (agents/reporter.py)
──────────────────────────
  INPUT:   gold_paths, business_intent, run_id
  TOOLS:   inspect_gold_tables_tool(), load_gold_data_tool(), 
           execute_query_tool(sql)
  PROCESS: 1. Preview Gold tables (row counts, column names)
           2. Register Gold Parquet files as DuckDB in-memory SQL tables
           3. LLM writes ANSI SQL query to answer business_intent
           4. Execute SQL, get result rows
           5. Build Plotly chart (best-effort: first col = category, second = value)
           6. Call store_document() to persist intent + answer in ChromaDB
  OUTPUT:  {"answer": str, "sql": str, "rows": list, "chart": Plotly}
  RUNTIME: ~120-180 seconds (Groq free tier hit 429 rate limits, retry waits)

ORCHESTRATOR (agents/orchestrator.py)
──────────────────────────────
  4 PUBLIC FUNCTIONS:
  1. start_pipeline(files, business_intent, run_id) → PipelineState
     Runs Phases 1 & 2, returns awaiting_bronze_approval
  
  2. approve_bronze(state) → PipelineState
     Runs Phase 2b (STTM) & Phase 3a (Bronze), returns awaiting_silver_approval
  
  3. approve_silver(state) → PipelineState
     Runs Phase 3b (STTM) & Phase 4a (Silver), returns awaiting_gold_approval
  
  4. approve_gold(state) → PipelineState
     Runs Phase 4b (STTM) & Phase 5a (Gold) & Phase 5b (Reporter), 
     returns complete

================================================================================
INFRASTRUCTURE LAYER
─────────────────────────────────────────────────────────────────────────────

config.py
──────────
  - Paths: DATA_DIR, LANDING_DIR, BRONZE_DIR, SILVER_DIR, GOLD_DIR, etc.
  - LLM: GROQ_API_KEY, GROQ_MODEL (="openai/gpt-oss-20b"), GROQ_TEMPERATURE
  - Thresholds: MAX_NULL_RATIO_DROP_COLUMN, OUTLIER_ZSCORE_THRESHOLD

llm.py
───────
  - get_llm() → ChatGroq instance
  - is_llm_configured() → bool

state.py
─────────
  - PipelineState: TypedDict with all fields required between phases
  - Tells Streamlit what state to preserve across reruns

memory.py (ChromaDB)
──────────
  - store_document(text, metadata, doc_id) → doc_id
    Embeds & persists "business_intent + answer" for future retrieval
  - retrieve_context(query, n_results) → List[{"document": ..., "metadata": ...}]
    Semantic search for similar past runs (not used yet, ready for RAG)

audit.py (AuditLogger)
─────────
  - audit.log(agent_name, action, **kwargs)
    Appends JSON-line to audit_logs/{run_id}.jsonl
  - Example: audit.log("orchestrator", "phase1_complete", sttm_bronze_path="...")

observability.py (AgentTrace)
──────────────────
  - AgentTrace(agent_name, run_id)
    Captures every LLM call's reasoning chain
  
  Methods:
  - set_input(**kwargs) → self (chainable)
  - set_output(**kwargs) → self
  - extract_from_messages(messages) → self
    Parses result["messages"] from create_react_agent:
    • Extracts plan (first AIMessage reasoning)
    • Extracts tool_calls (names & args)
    • Extracts reasoning_steps (full HumanMessage → AIMessage → ToolMessage chain)
  - complete() / fail(exc)
    Writes to data/traces/trace_{agent}_{run_id[:8]}.json
  
  Output JSON example:
    {
      "agent": "profiler_agent",
      "run_id": "a1b2c3d4",
      "started_at": "2026-08-17T20:09:00+00:00",
      "input": {"files": ["sales_data.csv", ...], "business_intent": "..."},
      "plan": "First I'll preview all files...",
      "tool_calls": [
        {"name": "inspect_files_tool", "args": {}, "id": "xyz", "type": "tool_call"},
        {"name": "profiler_tool", "args": {}, "id": "abc", "type": "tool_call"}
      ],
      "reasoning_steps": [
        {"type": "task_input", "content": "..."},
        {"type": "tool_result", "tool_call_id": "xyz", "content": "..."},
        ...
      ],
      "output": {"profile_path": "..."},
      "duration_seconds": 3.62,
      "status": "success"
    }

retry.py (Groq Rate Limit Handler)
──────────────────────────
  - invoke_with_retry(agent, payload, max_retries=3)
    Catches Groq 429 "rate_limit_exceeded" errors
    Parses "try again in Xs" from error message
    Sleeps & retries up to 3 times
    Used in every agent's agent.invoke() call

================================================================================
STREAMLIT UI (app/streamlit_app.py)
────────────────────────────────────────────────────────────────────────────

TAB 1: "📤 Upload & Profile"
  - File uploader (accepts multiple CSV)
  - Text area for business_intent
  - "Start → Phase 1" button
  - Calls start_pipeline(...) → updates st.session_state.state

TAB 2: "🥉 Bronze STTM"
  - Shows Profiler output (join keys, quality alerts)
  - Editable data_editor for Bronze STTM rules
  - "✅ Approve & proceed" → calls approve_bronze(...) → Phase 2
  - "❌ Reject & reset" → clears state

TAB 3: "🥈 Silver STTM"
  - Shows Bronze output Parquet previews
  - Editable Silver STTM rules
  - Approve/Reject for Phase 3

TAB 4: "🥇 Gold STTM"
  - Shows Silver output Parquet previews
  - Editable Gold STTM rules
  - Approve → runs Phases 4 & 5 (Gold + Reporter)

TAB 5: "📋 Report"
  - Gold tables (materialized analytics tables)
  - Reporter's answer + Plotly chart
  - Sub-tabs: SQL query, Query result, Agent traces, Audit log
  - Download button for full run JSON

STATE MANAGEMENT:
  - st.session_state.state = PipelineState (survives Streamlit reruns)
  - st.session_state.state = None (reset on user click)

================================================================================
DATA FLOW EXAMPLE (sales_data.csv + products.csv + stores.csv)
─────────────────────────────────────────────────────────────────────────────

USER UPLOADS & STARTS PHASE 1:
  Upload: sales_data.csv, products.csv, stores.csv
  Intent: "What is total revenue by product category?"
  ↓
PROFILER (Phase 1a):
  Reads all 3 CSVs, discovers:
  - 1,500 sales records (sales_data.csv)
  - 50 product records (products.csv)
  - 12 store records (stores.csv)
  - Join key: "product_id" links sales ↔ products
  - Join key: "store_id" links sales ↔ stores
  - Quality: 2% nulls in sales.product_id, 0.5% in stores.state
  ↓
STTM GENERATOR (Phase 1b → Bronze):
  LLM proposes rename rules:
  - sales_data.csv: "txn_date" → "transaction_date" (datetime)
  - sales_data.csv: "amount" → "total_amount" (numeric)
  - products.csv: "prod_id" → "product_id" (string)
  - stores.csv: "store_location_state" → "state" (string)
  ↓
USER APPROVES BRONZE STTM:
  ✅ Approve button clicked
  ↓
BRONZE AGENT (Phase 2):
  Ingests all 3 CSVs:
  - sales_data_bronze.parquet (1,500 rows, renamed/typed)
  - products_bronze.parquet (50 rows, renamed/typed)
  - stores_bronze.parquet (12 rows, renamed/typed)
  ↓
STTM GENERATOR (Phase 2b → Silver):
  LLM proposes cleansing rules:
  - sales_data_bronze: fillna(total_amount with median), drop_duplicates
  - products_bronze: fillna(product_name with "unknown")
  - stores_bronze: drop_duplicates on store_id
  ↓
USER APPROVES SILVER STTM:
  ↓
SILVER AGENT (Phase 3):
  Cleans all 3 Bronze tables:
  - sales_data_silver.parquet (1,470 rows after dedup, 2 nulls imputed)
  - products_silver.parquet (50 rows, no dupes)
  - stores_silver.parquet (12 rows, no dupes)
  Each gets a surrogate key: pk_sales_data_silver_id, etc.
  ↓
STTM GENERATOR (Phase 3b → Gold):
  LLM proposes analytics rules:
  - Join all 3 Silver tables on product_id & store_id (outer)
  - Aggregate: groupby(category).sum(total_amount)
  - Aggregate: groupby(region).sum(total_amount)
  - Aggregate: groupby(store_name).sum(total_amount)
  ↓
USER APPROVES GOLD STTM:
  ↓
GOLD AGENT (Phase 4):
  Materializes analytics tables:
  - gold_transactions.parquet (outer-joined fact table)
  - gold_revenue_by_category.parquet (9 categories × 1 revenue col)
  - gold_revenue_by_region.parquet (5 regions × 1 revenue col)
  - gold_revenue_by_store_name.parquet (12 stores × 1 revenue col)
  ↓
REPORTER AGENT (Phase 5):
  LLM writes SQL:
    SELECT category, SUM(total_amount) AS total_revenue
    FROM gold_revenue_by_category
    GROUP BY category
    ORDER BY total_revenue DESC
  Executes in DuckDB → 9 rows
  Builds Plotly bar chart (category vs revenue)
  Answers: "Electronics $106,675 | Beauty $25,537 | ..."
  ↓
STREAMLIT TAB 5 (Report):
  Shows gold tables, answer text, bar chart, SQL query,
  agent traces, audit log, download button

================================================================================
KEY DESIGN PATTERNS
─────────────────────────────────────────────────────────────────────────────

1. TOOL FACTORY + CLOSURE
   ─────────────────────
   Why: LLMs hallucinate file paths
   How: _make_*_tools(files, sttm_path, run_id) captures them
        Tools use closure to access paths without arguments
   Example (bronze_agent.py):
     def _make_bronze_tools(file_paths, sttm_path, run_id, scratchpad):
         @tool
         def bronze_ingestion_tool() -> str:
             for path in file_paths:  # ← closure
                 df = pd.read_csv(path)
                 ...

2. SCRATCHPAD + CLOSURE
   ────────────────────
   Why: Tools in the same phase need to share outputs
   How: scratchpad dict is passed to tool factory, both tools capture it
   Example:
     scratchpad = {}
     profiler_tool() writes scratchpad["profile_path"]
     sttm_generator_tool() reads scratchpad["profile_path"]
   No LLM copy-paste required.

3. PIPELINESTATE + SESSION STATE
   ────────────────────────────
   Why: Streamlit reruns the entire script on every interaction
   How: st.session_state.state persists PipelineState across reruns
   Result: User can navigate tabs freely, state survives

4. HUMAN-IN-THE-LOOP STTM APPROVAL
   ────────────────────────────
   Why: Transformation rules are critical; bad rules = bad downstream data
   How: After each STTM generation, pause for user approval
        User can edit st.data_editor(sttm_df) before approval
        st.button("Approve") copies edited CSV back to disk & continues
   Result: Trust in AI outputs; matching real data engineering processes

5. AUDIT + OBSERVABILITY
   ──────────────────
   Why: Debugging multi-agent pipelines is hard
   How: AuditLogger logs every orchestrator step
        AgentTrace logs every LLM call's reasoning + tool calls
        Both write to JSON files (persisted after run completes)
   Result: Full audit trail; see exactly what each agent decided & why

================================================================================
DEPENDENCIES & VERSIONS
─────────────────────────────────────────────────────────────────────────────

Core LLM/Agents:
  langchain >= 0.2
  langchain-core
  langchain-groq (Groq chat model)
  langgraph (ReAct agent graphs)

Data Processing:
  pandas >= 2.0
  pyarrow (Parquet backend)
  duckdb (SQL analytics)

Vector Search & Memory:
  chromadb (semantic memory store)

UI:
  streamlit >= 1.32

Other:
  groq (Groq SDK, for model listing & direct API)
  plotly (charts in reports)
  python-dotenv (load .env)
  uuid, json, pathlib, datetime, traceback (stdlib)

================================================================================
RUNNING THE SYSTEM
─────────────────────────────────────────────────────────────────────────────

1. SET UP:
   $ python -m venv .venv
   $ .venv/Scripts/activate
   $ pip install -r medallion-pipeline/requirements.txt

2. CONFIGURE:
   $ cp medallion-pipeline/.env.example medallion-pipeline/.env
   $ # Edit .env: set GROQ_API_KEY

3. RUN STREAMLIT:
   $ streamlit run medallion-pipeline/app/streamlit_app.py
   Opens http://localhost:8501

4. USAGE:
   - Tab 1: Upload CSVs, define intent, click "Start → Phase 1"
   - Tab 2: Review Bronze STTM, edit if needed, click "Approve & proceed"
   - Tab 3: Review Silver STTM, edit if needed, click "Approve & proceed"
   - Tab 4: Review Gold STTM, edit if needed, click "Approve & proceed"
   - Tab 5: View final report, SQL, chart, traces

5. TEST (PROGRAMMATICALLY):
   $ pytest medallion-pipeline/tests/
   
   Or full end-to-end:
   $ python -c "
     from agents.orchestrator import start_pipeline, approve_*
     state = start_pipeline(['file1.csv', 'file2.csv', ...], 'question', 'run_id')
     state = approve_bronze(state)
     state = approve_silver(state)
     state = approve_gold(state)
     print(state['report']['answer'])
   "

================================================================================
COMMON QUESTIONS
─────────────────────────────────────────────────────────────────────────────

Q: Why 4 phases instead of just running end-to-end?
A: STTM (transformation rules) are the critical artifact. Humans review them
   before execution to prevent bad rules from cascading downstream. This
   matches real data engineering & builds trust in AI decisions.

Q: Why Medallion architecture (Bronze/Silver/Gold)?
A: Standard in data lakes. Bronze = raw ingestion, Silver = clean & trusted,
   Gold = analytics-ready. Each layer has a clear purpose & approval gate.

Q: Can I use a different LLM?
A: Yes. Edit core/llm.py to use OpenAI, Anthropic, etc. The ReAct pattern
   works with any LLM that supports create_react_agent from LangChain.

Q: What if the Reporter Agent writes bad SQL?
A: It retries once (execute_query_tool catches SQL errors). If it fails twice,
   the trace JSON captures the failed SQL so you can debug. Consider it a
   limitation of free-tier LLMs; fine-tuned models would do better.

Q: Can I run this without Streamlit?
A: Yes. Call orchestrator functions directly:
   from agents.orchestrator import start_pipeline, approve_bronze, ...
   state = start_pipeline([...], intent, run_id)
   state = approve_bronze(state)  # etc.
   # or programmatically edit CSVs and skip approval
   state['sttm_bronze_path'] = ...  # manually
   state = approve_bronze(state)

Q: How does ChromaDB memory work?
A: store_document() embeds & persists (intent + answer) after every run.
   retrieve_context(query) does semantic search over past runs.
   Currently not used (ready for RAG / prompting future runs with similar
   historical context). See core/memory.py.

================================================================================
FUTURE ENHANCEMENTS
─────────────────────────────────────────────────────────────────────────────

1. Use ChromaDB memory in Reporter Agent: "Based on similar past questions..."
2. Add file diff viewer: show before/after for STTM edits before approval
3. Parallel agent execution: run all 3 STTM agents (for different gold tables)
   concurrently instead of sequentially
4. Smarter null imputation: use ML (KNN, etc.) instead of mean/median
5. Export approved STTM rules for reuse in next pipeline run
6. Interactive SQL editor in Tab 5: user writes custom SQL, reporter agent
   tries to execute
7. Cost tracking: log token usage per agent, display dashboard
8. Model switching: dropdown to switch between openai/gpt-oss-20b, 
   openai/gpt-oss-120b, qwen/qwen3.6-27b, etc. (per Groq availability)

================================================================================
