# app.py
import json

from agent import clear_log_file, read_log_entries, run_agent


def _print_log_tail(limit: int = 5):
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


def _print_help():
    print("Commands:")
    print("  /logs        Show the 5 most recent log entries")
    print("  /clearlogs   Delete the current log file")
    print("  /help        Show commands")
    print("  exit         Quit\n")


def main():
    print("Local Business Quote Agent")
    print("Logging is ON for CLI runs.")
    print("Type 'exit' to quit. Type '/help' for commands.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye.")
            break

        if user_input.lower() == "/help":
            _print_help()
            continue

        if user_input.lower() == "/logs":
            _print_log_tail(limit=5)
            continue

        if user_input.lower() == "/clearlogs":
            clear_log_file()
            print("Log file cleared.\n")
            continue

        result = run_agent(user_input, enable_logging=True)

        print("\n--- AGENT RESPONSE OBJECT ---")
        print(json.dumps(result, indent=2))
        print("\n--- FINAL ANSWER ---")
        print(f"Agent: {result['final_answer']}\n")


if __name__ == "__main__":
    main()