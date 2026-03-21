# Local Business Quote Agent (Python CLI)

A small Python CLI assistant that answers common questions for a local service business (junk removal / hauling / dumpsters / gravel / demo / land clearing) using a **rules + tools** architecture, with **optional** OpenAI-assisted routing for truly unknown requests and an **optional** grounded rewrite of tool-based answers.

This project is intentionally designed to be demo/portfolio-ready: deterministic tools remain the source of truth, and any LLM usage is gated and logged.

---

## What it does

- **Intent routing**: maps user messages to a known “intent” (services, pricing, hours, etc.)
- **Tool calls**: each intent calls a Python function that returns structured business info
- **Resilient formatters**: user-facing answers are formatted safely even if tool data is missing
- **Session memory**: handles simple follow-ups (“How much?”, “What about pianos?”)
- **Quote intake flow**: collects required quote details across multiple turns
- **Logging**: JSONL log file with routing + tool + (optional) LLM decisions
- **Optional OpenAI support (gated)**:
  - unknown-intent routing fallback (only when rules return `unknown`)
  - grounded rewrite of tool answers (only after a tool call, no new facts allowed)

---

## Quickstart

### 1) Create and activate a venv

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Create a `.env` (optional but recommended)

Create a file named `.env` in the project root.

Minimal example (no LLM features):
```env
# Logging
QUOTE_AGENT_ENABLE_LOGGING=1
```

Example enabling OpenAI features:
```env
OPENAI_API_KEY=your_key_here

# Optional: unknown-intent routing (Day 10)
QUOTE_AGENT_ENABLE_LLM=1
QUOTE_AGENT_LLM_MODEL=gpt-4o-mini

# Optional: grounded rewrite of tool answers (Day 11)
QUOTE_AGENT_ENABLE_LLM_REWRITE=1
```

### 4) Run

```bash
python app.py
```

### 5) Run tests

```bash
python tests.py
```

---

## CLI commands (inside the app)

- `/help` — list commands
- `/logs` or `/log` — show the last 5 log entries (JSON)
- `/clearlogs` — delete the current log file
- `exit` — quit

> Note: `/logs` works **inside the running CLI app**, not your shell.

---

## Environment variables

### Required (only if OpenAI features are enabled)

- `OPENAI_API_KEY`  
  Required **only** when `QUOTE_AGENT_ENABLE_LLM=1` and/or `QUOTE_AGENT_ENABLE_LLM_REWRITE=1`.

### Optional OpenAI toggles

- `QUOTE_AGENT_ENABLE_LLM` (default: `0`)  
  Enables OpenAI-assisted routing **only** when rules return `unknown`.

- `QUOTE_AGENT_LLM_MODEL` (default: `gpt-4o-mini`)  
  Model name passed to the OpenAI Responses API.

- `QUOTE_AGENT_ENABLE_LLM_REWRITE` (default: `0`)  
  Enables a tool-grounded rewrite pass **only** for tool-based answers (no new facts allowed).

### Logging

- `QUOTE_AGENT_ENABLE_LOGGING` (default: `0`)  
  Enable JSONL logging.

- `QUOTE_AGENT_LOG_PATH` (default: `agent_logs.jsonl`)  
  Path to the JSONL log file.

---

## Example prompts to try

**Services / items**
- “What services do you offer?”
- “Do you remove pianos?”
- “Do you haul appliances?”

**Pricing**
- “How much does junk removal cost?”
- “What’s your minimum price?”

**Scheduling**
- “When are you available?”
- “Can I schedule service for Friday?”

**Policies**
- “Do you recycle anything?”
- “Can you donate usable items?”
- “Do you take paint or tires?”
- “Do I need to be home during the job?”

**Quote intake**
- “I need a quote”
- “I’d like an estimate for junk removal in Cedar Rapids”

---

## Logging

Logs are written in JSONL format (one JSON object per line). Fields include:

- `intent`, `matched_keywords`, `routing_reason`
- `tool_called`, `tool_ok`, `final_answer`
- `llm_used`, `llm_decision` (unknown-intent routing fallback)
- `llm_answer_used`, `llm_answer_note` (grounded rewrite)

---

## Project structure

- `app.py` — CLI entry point and command routing
- `agent.py` — intent routing, tool orchestration, memory, logging, optional OpenAI calls (urllib)
- `tools.py` — tool functions + resilient answer formatters (must never raise)
- `business_data.py` — source-of-truth business facts used by tools
- `tests.py` — regression + follow-up + logging harness tests

---

## Known limitations

- Business data is static (no database / CRM integration).
- The “quote intake” flow validates only basic formats (e.g., phone digits).
- Optional OpenAI usage is best-effort: network or API errors simply fall back to the deterministic path.
- The rewrite step is constrained to tool-grounded text, but you should still treat LLM output as untrusted and keep it gated in production systems.

---

## Next ideas

- Add a `pyproject.toml` and package metadata (entry point like `quote-agent`)
- Add richer quote intake validation (address parsing, photo link capture)
- Add a “conversation export” command for demos
- Add more business tools (dumpster sizes, pricing tiers, distance-based rules)
