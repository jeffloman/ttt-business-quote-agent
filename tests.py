# tests.py
# =========================
# FILE: tests.py
# =========================
from pathlib import Path

from agent import clear_log_file, read_log_entries, reset_session_memory, run_agent
from tools import (
    format_contact_methods,
    format_pricing_info,
    format_services_offered,
)

TEST_CASES = [
    {"input": "How much does junk removal cost?", "expected_intent": "pricing_info", "expected_tool": "get_pricing_info"},
    {"input": "How do I book an appointment?", "expected_intent": "contact_methods", "expected_tool": "get_contact_methods"},
    {"input": "What services do you offer?", "expected_intent": "services_offered", "expected_tool": "get_services_offered"},
    {"input": "When are you available?", "expected_intent": "availability_info", "expected_tool": "get_availability_info"},
    {"input": "How do I get a quote?", "expected_intent": "quote_methods", "expected_tool": "get_quote_methods"},
    {"input": "What do you need for a quote?", "expected_intent": "required_quote_info", "expected_tool": "get_required_quote_info"},
    {"input": "Do you take cash or card?", "expected_intent": "payment_methods", "expected_tool": "get_payment_methods"},
    {"input": "What areas do you serve?", "expected_intent": "service_area", "expected_tool": "get_service_area"},
    {"input": "Are you open on weekends?", "expected_intent": "hours", "expected_tool": "get_hours"},
    {"input": "Can I schedule service for Friday?", "expected_intent": "contact_methods", "expected_tool": "get_contact_methods"},
    {"input": "Do you recycle anything?", "expected_intent": "recycling_policy", "expected_tool": "get_recycling_policy"},
    {"input": "Can you donate usable items?", "expected_intent": "donation_policy", "expected_tool": "get_donation_policy"},
    {"input": "Do I need to help with heavy lifting?", "expected_intent": "heavy_lifting_policy", "expected_tool": "get_heavy_lifting_policy"},
    {"input": "Do you take paint or tires?", "expected_intent": "prohibited_items", "expected_tool": "get_prohibited_items"},
    {"input": "Do I need to be home during the job?", "expected_intent": "home_presence_info", "expected_tool": "get_home_presence_info"},
    {"input": "Are your workers background checked?", "expected_intent": "team_trust_info", "expected_tool": "get_team_trust_info"},
    {"input": "Are you veterans?", "expected_intent": "team_trust_info", "expected_tool": "get_team_trust_info"},
    {"input": "Can you get into a narrow driveway?", "expected_intent": "access_constraints", "expected_tool": "get_access_constraints"},
    {"input": "We have low power lines, is that a problem?", "expected_intent": "access_constraints", "expected_tool": "get_access_constraints"},
    {"input": "How much gravel do I need?", "expected_intent": "gravel_estimate_info", "expected_tool": "get_gravel_estimate_info"},
    {"input": "How much?", "expected_intent": "unknown", "expected_tool": None, "expected_answer_contains": "what are you asking about pricing"},
    {"input": "Can you take that?", "expected_intent": "unknown", "expected_tool": None, "expected_answer_contains": "what item/material are you referring to"},
    {"input": "Do you do it?", "expected_intent": "unknown", "expected_tool": None, "expected_answer_contains": "which service or item"},
    {"input": "Hello", "expected_intent": "greeting", "expected_tool": None},
    {"input": "What is your favorite color?", "expected_intent": "unknown", "expected_tool": None},
]

FOLLOWUP_CONVERSATIONS = [
    {
        "name": "Quote follow-up: requirements after quote methods",
        "turns": [
            {"input": "How do I get a quote?", "expected_intent": "quote_methods", "expected_tool": "get_quote_methods"},
            {"input": "What do you need for that?", "expected_intent": "required_quote_info", "expected_tool": "get_required_quote_info"},
        ],
    },
    {
        "name": "Pricing follow-up: how much is that after services",
        "turns": [
            {"input": "What services do you offer?", "expected_intent": "services_offered", "expected_tool": "get_services_offered"},
            {"input": "How much is that?", "expected_intent": "pricing_info", "expected_tool": "get_pricing_info"},
        ],
    },
    {
        "name": "Booking follow-up: book that for Friday after services",
        "turns": [
            {"input": "Do you do junk removal?", "expected_intent": "services_offered", "expected_tool": "get_services_offered"},
            {"input": "Can I book that for Friday?", "expected_intent": "contact_methods", "expected_tool": "get_contact_methods"},
        ],
    },
    {
        "name": "Take/accept follow-up: after payment methods",
        "turns": [
            {"input": "Do you take cash or card?", "expected_intent": "payment_methods", "expected_tool": "get_payment_methods"},
            {"input": "Do you take that?", "expected_intent": "payment_methods", "expected_tool": "get_payment_methods"},
        ],
    },
    {
        "name": "Take/accept follow-up: after prohibited items",
        "turns": [
            {"input": "Do you take paint or tires?", "expected_intent": "prohibited_items", "expected_tool": "get_prohibited_items"},
            {"input": "Do you take that?", "expected_intent": "prohibited_items", "expected_tool": "get_prohibited_items"},
        ],
    },
    {
        "name": "Time-only follow-up: Friday? after booking/availability",
        "turns": [
            {"input": "Can I schedule service for Friday?", "expected_intent": "contact_methods", "expected_tool": "get_contact_methods"},
            {"input": "Saturday?", "expected_intent": "contact_methods", "expected_tool": "get_contact_methods"},
        ],
    },
    {
        "name": "Time-only follow-up: next week after availability",
        "turns": [
            {"input": "When are you available?", "expected_intent": "availability_info", "expected_tool": "get_availability_info"},
            {"input": "How about next week?", "expected_intent": "contact_methods", "expected_tool": "get_contact_methods"},
        ],
    },
    {
        "name": "Quote methods then active quote request starts intake",
        "turns": [
            {"input": "How do I get a quote?", "expected_intent": "quote_methods", "expected_tool": "get_quote_methods"},
            {"input": "I need a quote", "expected_intent": "quote_intake", "expected_tool": None},
        ],
    },
    {
        "name": "Quote intake validation: bad phone re-prompts",
        "turns": [
            {"input": "I need a quote", "expected_intent": "quote_intake", "expected_tool": None, "expected_answer_contains": "name"},
            {"input": "Jeff", "expected_intent": "quote_intake", "expected_tool": None, "expected_answer_contains": "phone"},
            {"input": "555", "expected_intent": "quote_intake", "expected_tool": None, "expected_answer_contains": "phone"},
            {"input": "555-123-4567", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "Cedar Rapids", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "junk removal", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "no", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "old couch", "expected_intent": "quote_intake", "expected_tool": "get_contact_methods"},
        ],
    },
    {
        "name": "Quote intake: collect required fields",
        "turns": [
            {"input": "I need a quote", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "Jeff", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "(555) 123-4567", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "I'm in Cedar Rapids", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "junk removal", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "yes", "expected_intent": "quote_intake", "expected_tool": None},
            {"input": "couch and a mattress, 1 flight of stairs", "expected_intent": "quote_intake", "expected_tool": "get_contact_methods"},
        ],
    },
    {
        "name": "Day 5 follow-up: How much? after services",
        "turns": [
            {"input": "What services do you offer?", "expected_intent": "services_offered", "expected_tool": "get_services_offered"},
            {"input": "How much?", "expected_intent": "pricing_info", "expected_tool": "get_pricing_info"},
        ],
    },
    {
        "name": "Day 5 follow-up: What about pianos? after pricing",
        "turns": [
            {"input": "How much does junk removal cost?", "expected_intent": "pricing_info", "expected_tool": "get_pricing_info"},
            {"input": "What about pianos?", "expected_intent": "services_offered", "expected_tool": "get_services_offered"},
        ],
    },
    {
        "name": "Day 5 follow-up: Can I text you? after quote methods",
        "turns": [
            {"input": "How do I get a quote?", "expected_intent": "quote_methods", "expected_tool": "get_quote_methods"},
            {"input": "Can I text you?", "expected_intent": "contact_methods", "expected_tool": "get_contact_methods"},
        ],
    },
]


MISSING_DATA_TESTS = [
    {
        "name": "Formatter: pricing_info handles ok=False",
        "formatter": format_pricing_info,
        "tool_result": {"tool": "get_pricing_info", "ok": False, "data": None, "error": "db down"},
        "expected_substring": "couldn't retrieve pricing",
    },
    {
        "name": "Formatter: services_offered handles missing keys",
        "formatter": format_services_offered,
        "tool_result": {"tool": "get_services_offered", "ok": True, "data": {}, "error": None},
        "expected_substring": "couldn't retrieve services",
    },
    {
        "name": "Formatter: contact_methods handles malformed tool_result",
        "formatter": format_contact_methods,
        "tool_result": "not a dict",
        "expected_substring": "couldn't retrieve contact",
    },
]


def print_failure_details(result: dict):
    print(f"  Routing reason:   {result['routing_reason']}")
    print(f"  Matched keywords: {result['matched_keywords']}")
    print(f"  Tool called:      {result['tool_called']}")
    print(f"  Debug:            {result.get('debug')}")
    print(f"  Memory before:    {result.get('memory_before')}")
    print(f"  Memory after:     {result.get('memory_after')}")


def _check_tool_schema(result: dict, expected_tool: str | None) -> tuple[bool, list[str]]:
    errors: list[str] = []
    tool_result = result.get("tool_result")

    if expected_tool is None:
        if tool_result is not None:
            errors.append("Expected tool_result to be None for tool-free intents.")
        return (len(errors) == 0), errors

    if not isinstance(tool_result, dict):
        return False, ["Expected tool_result to be a dict for tool-using intents."]

    for key in ("tool", "ok", "data", "error"):
        if key not in tool_result:
            errors.append(f"Missing tool_result key: {key!r}")

    if tool_result.get("tool") != expected_tool:
        errors.append(
            f"tool_result['tool'] mismatch: expected {expected_tool!r}, got {tool_result.get('tool')!r}"
        )

    if tool_result.get("ok") is not True:
        errors.append(f"Expected tool_result['ok'] to be True, got {tool_result.get('ok')!r}")

    if tool_result.get("error") not in (None, ""):
        errors.append(f"Expected tool_result['error'] to be None/empty, got {tool_result.get('error')!r}")

    return (len(errors) == 0), errors


def _check_answer_contains(result: dict, expected_substring: str | None) -> tuple[bool, str | None]:
    if expected_substring is None:
        return True, None
    answer = result.get("final_answer") or ""
    if expected_substring.lower() in str(answer).lower():
        return True, None
    return False, f"Expected final_answer to contain {expected_substring!r}"


def run_regression_tests():
    passed = 0
    failed = 0

    print("Running Quote Agent regression tests...\n")

    for i, test in enumerate(TEST_CASES, start=1):
        reset_session_memory()

        user_input = test["input"]
        expected_intent = test["expected_intent"]
        expected_tool = test["expected_tool"]

        result = run_agent(user_input)
        actual_intent = result["intent"]
        actual_tool = result["tool_called"]

        intent_ok = actual_intent == expected_intent
        tool_ok = actual_tool == expected_tool

        schema_ok, schema_errors = _check_tool_schema(result, expected_tool)
        answer_ok, answer_error = _check_answer_contains(result, test.get("expected_answer_contains"))

        if intent_ok and tool_ok and schema_ok and answer_ok:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        print(f"Test {i}: {status}")
        print(f"  Input:            {user_input}")
        print(f"  Expected intent:  {expected_intent}")
        print(f"  Actual intent:    {actual_intent}")
        print(f"  Expected tool:    {expected_tool}")
        print(f"  Actual tool:      {actual_tool}")

        if not schema_ok:
            for e in schema_errors:
                print(f"  Tool schema:      {e}")

        if not answer_ok and answer_error:
            print(f"  Answer check:    {answer_error}")

        if not intent_ok or not tool_ok or not schema_ok or not answer_ok:
            print_failure_details(result)

        print()

    print("Running follow-up (multi-turn) tests...\n")

    for convo in FOLLOWUP_CONVERSATIONS:
        reset_session_memory()
        print(f"Conversation: {convo['name']}")

        for j, turn in enumerate(convo["turns"], start=1):
            user_input = turn["input"]
            expected_intent = turn["expected_intent"]
            expected_tool = turn["expected_tool"]

            result = run_agent(user_input)
            actual_intent = result["intent"]
            actual_tool = result["tool_called"]

            intent_ok = actual_intent == expected_intent
            tool_ok = actual_tool == expected_tool

            schema_ok, schema_errors = _check_tool_schema(result, expected_tool)
            answer_ok, answer_error = _check_answer_contains(result, turn.get("expected_answer_contains"))

            if intent_ok and tool_ok and schema_ok and answer_ok:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"

            print(f"  Turn {j}: {status}")
            print(f"    Input:           {user_input}")
            print(f"    Expected intent: {expected_intent}")
            print(f"    Actual intent:   {actual_intent}")
            print(f"    Expected tool:   {expected_tool}")
            print(f"    Actual tool:     {actual_tool}")

            if not schema_ok:
                for e in schema_errors:
                    print(f"    Tool schema:     {e}")

            if not answer_ok and answer_error:
                print(f"    Answer check:   {answer_error}")

            if not intent_ok or not tool_ok or not schema_ok or not answer_ok:
                print_failure_details(result)

        print()

    print("Running missing-data (formatter robustness) tests...\n")

    for case in MISSING_DATA_TESTS:
        name = case["name"]
        formatter = case["formatter"]
        tool_result = case["tool_result"]
        expected_substring = case.get("expected_substring")

        try:
            out = formatter(tool_result)  # type: ignore[arg-type]
            ok = True
        except Exception as e:
            out = f"<EXCEPTION: {e}>"
            ok = False

        contains_ok = True
        if expected_substring is not None:
            contains_ok = expected_substring.lower() in str(out).lower()

        if ok and contains_ok:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        print(f"Missing-data: {status}")
        print(f"  Case: {name}")
        if not ok:
            print(f"  Exception/Output: {out}")
        else:
            print(f"  Output: {out}")
        if not contains_ok:
            print(f"  Expected substring: {expected_substring!r}")
        print()

    print("---- SUMMARY ----")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")


LOG_TEST_PATH = Path("test_agent_logs.jsonl")


def run_logging_harness():
    print("Running Day 8 logging harness...\n")

    clear_log_file(LOG_TEST_PATH)
    reset_session_memory()

    prompts = [
        "How much does junk removal cost?",
        "What services do you offer?",
    ]

    for prompt in prompts:
        _ = run_agent(prompt, enable_logging=True, log_path=LOG_TEST_PATH)

    entries = read_log_entries(LOG_TEST_PATH)
    ok = True

    if len(entries) != len(prompts):
        ok = False
        print(f"Harness FAIL: expected {len(prompts)} log entries, got {len(entries)}")

    required_keys = {
        "timestamp_utc",
        "user_input",
        "intent",
        "matched_keywords",
        "tool_called",
        "tool_ok",
        "final_answer",
        "routing_reason",
    }

    for i, entry in enumerate(entries, start=1):
        missing = sorted(required_keys - set(entry.keys()))
        if missing:
            ok = False
            print(f"Harness FAIL: entry {i} missing keys: {missing}")

    if ok:
        print("Logging harness: PASS")
        print(f"  Log path: {LOG_TEST_PATH}")
        print(f"  Entries:  {len(entries)}")
        print("  Last entry preview:")
        print(f"    user_input:   {entries[-1]['user_input']}")
        print(f"    intent:       {entries[-1]['intent']}")
        print(f"    tool_called:  {entries[-1]['tool_called']}")

    print()


def run_all_tests():
    run_regression_tests()
    run_logging_harness()


if __name__ == "__main__":
    run_all_tests()