# =========================
# FILE: app.py
# (replaces your current version that hard-fails without OPENAI_API_KEY)
# =========================
import json
import os
from typing import Callable

from dotenv import load_dotenv

load_dotenv()

from agent import clear_log_file, read_log_entries, run_agent  # noqa: E402


def _print_log_tail(limit: int = 5) -> None:
    entries = read_log_entries(limit=limit)
    if not entries:
        print("\n--- LOGS ---")
        print("No log entries found.\n")
        return

    print("\n--- LOGS ---")
    for i, entry in enumerate(entries, start=1):
        print(f"Entry {i}:")
        print(json.dumps(entry, indent=2))
    print()


def _print_help() -> None:
    print("Commands:")
    print("  /logs, /log   Show the 5 most recent log entries")
    print("  /clearlogs    Delete the current log file")
    print("  /help         Show commands")
    print("  exit          Quit\n")


def _maybe_warn_missing_openai_key() -> None:
    wants_llm = os.getenv("QUOTE_AGENT_ENABLE_LLM", "0").strip().lower() in {"1", "true", "yes", "on"}
    wants_rewrite = os.getenv("QUOTE_AGENT_ENABLE_LLM_REWRITE", "0").strip().lower() in {"1", "true", "yes", "on"}
    if not (wants_llm or wants_rewrite):
        return
    if os.getenv("OPENAI_API_KEY", "").strip():
        return

    print(
        "WARNING: OpenAI features are enabled (QUOTE_AGENT_ENABLE_LLM and/or QUOTE_AGENT_ENABLE_LLM_REWRITE), "
        "but OPENAI_API_KEY is missing. LLM features will be skipped/fall back to rules+tools.\n"
    )


def main() -> None:
    print("Local Business Quote Agent")
    print("Logging is ON for CLI runs.")
    print("Type 'exit' to quit. Type '/help' for commands.\n")

    _maybe_warn_missing_openai_key()

    commands: dict[str, Callable[[], None]] = {
        "/help": _print_help,
        "/logs": lambda: _print_log_tail(limit=5),
        "/log": lambda: _print_log_tail(limit=5),
        "/clearlogs": lambda: (clear_log_file(), print("Log file cleared.\n")),
    }

    while True:
        user_input = input("You: ").strip()
        lowered = user_input.lower()

        if lowered in {"exit", "quit"}:
            print("Goodbye.")
            break

        if lowered in commands:
            commands[lowered]()
            continue

        if lowered.startswith("/"):
            print("Unknown command. Type '/help' to see available commands.\n")
            continue

        result = run_agent(user_input, enable_logging=True)

        print("\n--- AGENT RESPONSE OBJECT ---")
        print(json.dumps(result, indent=2))
        print("\n--- FINAL ANSWER ---")
        print(f"Agent: {result['final_answer']}\n")


if __name__ == "__main__":
    main()