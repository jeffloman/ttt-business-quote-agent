# demo.py
"""
Portfolio/demo runner for Local Business Quote Agent.

Runs a curated set of prompts and prints:
- each user prompt
- each agent final answer
- a '/logs' tail at the end
- a final one-line summary scanning the JSONL log file

Usage:
  python demo.py
"""

from __future__ import annotations

import json
import os
from typing import Iterable

from dotenv import load_dotenv

load_dotenv()

from agent import (  # noqa: E402
    clear_log_file,
    read_log_entries,
    reset_session_memory,
    run_agent,
)

WOW_PROMPTS: list[str] = [
    "What services do you offer?",
    "Do you remove pianos?",
    "How much does junk removal cost?",
    "How much?",
    # Should trigger unknown -> LLM routing (when QUOTE_AGENT_ENABLE_LLM=1)
    "Is there a surcharge for stairs or a long carry from the house to the truck?",
    # Should trigger unknown -> LLM routing (when QUOTE_AGENT_ENABLE_LLM=1)
    "Can you provide a certificate of insurance (COI) for my property manager?",
    "Do you take paint or tires?",
    "Do you recycle anything?",
    "Can you donate usable items?",
    "Do I need to be home during the job?",
    "I need a quote",
    "It's junk removal in Cedar Rapids. It's a couch and a mattress. Curbside pickup.",
]


def _print_header() -> None:
    print("\n" + "=" * 60)
    print("LOCAL BUSINESS QUOTE AGENT — DEMO RUN")
    print("=" * 60)
    print("Notes:")
    print("- Prints ONLY final answers (clean demo output).")
    print("- Logging is enabled; a '/logs' tail is printed at the end.")
    print("- Final line prints LLM usage counts by scanning the JSONL log.\n")

    wants_llm = os.getenv("QUOTE_AGENT_ENABLE_LLM", "0").strip().lower() in {"1", "true", "yes", "on"}
    wants_rewrite = os.getenv("QUOTE_AGENT_ENABLE_LLM_REWRITE", "0").strip().lower() in {"1", "true", "yes", "on"}
    if (wants_llm or wants_rewrite) and not os.getenv("OPENAI_API_KEY", "").strip():
        print(
            "WARNING: OpenAI toggles are enabled but OPENAI_API_KEY is missing.\n"
            "         The agent should fall back to rules+tools.\n"
        )


def _run_prompts(prompts: Iterable[str]) -> None:
    for idx, prompt in enumerate(prompts, start=1):
        print(f"\n[{idx}] You: {prompt}")
        result = run_agent(prompt, enable_logging=True)
        print(f"    Agent: {result.get('final_answer', '')}")


def _print_logs_tail(limit: int = 5) -> None:
    print("\n" + "-" * 60)
    print(f"/logs (last {limit} entries)")
    print("-" * 60)

    entries = read_log_entries(limit=limit)
    if not entries:
        print("No log entries found.")
        return

    for i, entry in enumerate(entries, start=1):
        print(f"\nEntry {i}:")
        print(json.dumps(entry, indent=2, sort_keys=True))


def _scan_jsonl_log_for_llm_counts() -> tuple[int, int, int]:
    """
    Returns (llm_used_count, llm_rewrite_used_count, total_entries)
    """
    log_path = os.getenv("QUOTE_AGENT_LOG_PATH", "agent_logs.jsonl").strip() or "agent_logs.jsonl"

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
        return (0, 0, 0)

    return (llm_used_count, llm_rewrite_used_count, total_entries)


def main() -> None:
    _print_header()

    clear_log_file()
    reset_session_memory()

    _run_prompts(WOW_PROMPTS)
    _print_logs_tail(limit=5)

    llm_used_count, llm_rewrite_used_count, total_entries = _scan_jsonl_log_for_llm_counts()
    print(
        f"\nSUMMARY: llm_used_count={llm_used_count}, "
        f"llm_rewrite_used_count={llm_rewrite_used_count}, "
        f"total_entries={total_entries}"
    )

    print("\nDemo complete.\n")


if __name__ == "__main__":
    main()