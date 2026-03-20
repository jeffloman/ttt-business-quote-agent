# app.py
import json
import os
from typing import Callable

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is missing. Put it in your .env file.")

from agent import clear_log_file, read_log_entries, run_agent


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


def main() -> None:
    print("Local Business Quote Agent")
    print("Logging is ON for CLI runs.")
    print("Type 'exit' to quit. Type '/help' for commands.\n")

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