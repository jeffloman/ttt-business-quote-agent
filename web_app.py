# FILE: web_app.py
"""
Local Business Quote Agent — Flask Demo UI.

Upgrades:
- Pretty HTML rendering (cards, per-run output, collapsible raw JSON/logs)
- Free-port selection (avoids PORT=3000 conflicts)
- Small health endpoint for uptime checks

Run:
  python web_app.py

Env:
  PORT=3000 (optional; will try this first)
"""

from __future__ import annotations

import json
import os
import socket
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

from agent import (  # noqa: E402
    clear_log_file,
    read_log_entries,
    reset_session_memory,
    run_agent,
)

from demo import WOW_PROMPTS  # noqa: E402

app = Flask(__name__)


def _bool_env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _log_path() -> str:
    return os.getenv("QUOTE_AGENT_LOG_PATH", "agent_logs.jsonl").strip() or "agent_logs.jsonl"


def _scan_jsonl_log_for_llm_counts() -> dict[str, int]:
    log_path = _log_path()
    llm_used_count = 0
    llm_rewrite_used_count = 0
    total_entries = 0

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total_entries += 1
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if bool(obj.get("llm_used")):
                    llm_used_count += 1
                if bool(obj.get("llm_answer_used")):
                    llm_rewrite_used_count += 1
    except FileNotFoundError:
        pass

    return {
        "llm_used_count": llm_used_count,
        "llm_rewrite_used_count": llm_rewrite_used_count,
        "total_entries": total_entries,
    }


def _warning_banner() -> str | None:
    wants_llm = _bool_env("QUOTE_AGENT_ENABLE_LLM", "0")
    wants_rewrite = _bool_env("QUOTE_AGENT_ENABLE_LLM_REWRITE", "0")
    if not (wants_llm or wants_rewrite):
        return None
    if os.getenv("OPENAI_API_KEY", "").strip():
        return None

    return (
        "OpenAI features are enabled (QUOTE_AGENT_ENABLE_LLM and/or QUOTE_AGENT_ENABLE_LLM_REWRITE) "
        "but OPENAI_API_KEY is missing. The agent will fall back to rules+tools."
    )


def _is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except OSError:
            return False
        return True


def _pick_port(host: str, preferred: int) -> int:
    if preferred == 0:
        return 0
    if _is_port_free(host, preferred):
        return preferred
    for p in range(preferred + 1, preferred + 51):
        if _is_port_free(host, p):
            return p
    return 0  # let OS pick an ephemeral port


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.get("/")
def index():
    return render_template(
        "index.html",
        warning=_warning_banner(),
        llm_enabled=_bool_env("QUOTE_AGENT_ENABLE_LLM", "0"),
        rewrite_enabled=_bool_env("QUOTE_AGENT_ENABLE_LLM_REWRITE", "0"),
        log_path=_log_path(),
        demo_prompt_count=len(WOW_PROMPTS),
    )


@app.post("/api/prompt")
def api_prompt():
    payload: dict[str, Any] = request.get_json(force=True) or {}
    user_input = str(payload.get("prompt", "")).strip()
    show_raw = bool(payload.get("show_raw", False))

    if not user_input:
        return jsonify({"ok": False, "error": "Prompt is empty."}), 400

    result = run_agent(user_input, enable_logging=True)
    response: dict[str, Any] = {
        "ok": True,
        "final_answer": result.get("final_answer", ""),
    }
    if show_raw:
        response["raw"] = result
    return jsonify(response)


@app.post("/api/demo")
def api_demo():
    payload: dict[str, Any] = request.get_json(force=True) or {}
    show_raw = bool(payload.get("show_raw", False))

    clear_log_file()
    reset_session_memory()

    runs: list[dict[str, Any]] = []
    for prompt in WOW_PROMPTS:
        result = run_agent(prompt, enable_logging=True)
        row: dict[str, Any] = {
            "prompt": prompt,
            "final_answer": result.get("final_answer", ""),
        }
        if show_raw:
            row["raw"] = result
        runs.append(row)

    summary = _scan_jsonl_log_for_llm_counts()
    logs_tail = read_log_entries(limit=10)

    return jsonify(
        {
            "ok": True,
            "runs": runs,
            "summary": summary,
            "logs_tail": logs_tail,
        }
    )


@app.post("/api/reset")
def api_reset():
    clear_log_file()
    reset_session_memory()
    return jsonify({"ok": True})


def main() -> None:
    host = "0.0.0.0"
    preferred = int(os.getenv("PORT", "3000"))
    port = _pick_port(host, preferred)
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()