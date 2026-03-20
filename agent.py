# agent.py
# =========================
# FILE: agent.py
# =========================
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
import urllib.request
import urllib.error


from tools import (
    format_access_constraints,
    format_availability_info,
    format_contact_methods,
    format_donation_policy,
    format_gravel_estimate_info,
    format_heavy_lifting_policy,
    format_home_presence_info,
    format_hours,
    format_payment_methods,
    format_pricing_info,
    format_prohibited_items,
    format_quote_methods,
    format_recycling_policy,
    format_required_quote_info,
    format_service_area,
    format_services_offered,
    format_team_trust_info,
    get_access_constraints,
    get_availability_info,
    get_contact_methods,
    get_donation_policy,
    get_gravel_estimate_info,
    get_heavy_lifting_policy,
    get_home_presence_info,
    get_hours,
    get_payment_methods,
    get_pricing_info,
    get_prohibited_items,
    get_quote_methods,
    get_recycling_policy,
    get_required_quote_info,
    get_service_area,
    get_services_offered,
    get_team_trust_info,
)

TOOL_REGISTRY = {
    "service_area": {
        "tool_name": "get_service_area",
        "tool_function": get_service_area,
        "formatter": format_service_area,
    },
    "quote_methods": {
        "tool_name": "get_quote_methods",
        "tool_function": get_quote_methods,
        "formatter": format_quote_methods,
    },
    "payment_methods": {
        "tool_name": "get_payment_methods",
        "tool_function": get_payment_methods,
        "formatter": format_payment_methods,
    },
    "required_quote_info": {
        "tool_name": "get_required_quote_info",
        "tool_function": get_required_quote_info,
        "formatter": format_required_quote_info,
    },
    "hours": {
        "tool_name": "get_hours",
        "tool_function": get_hours,
        "formatter": format_hours,
    },
    "contact_methods": {
        "tool_name": "get_contact_methods",
        "tool_function": get_contact_methods,
        "formatter": format_contact_methods,
    },
    "services_offered": {
        "tool_name": "get_services_offered",
        "tool_function": get_services_offered,
        "formatter": format_services_offered,
    },
    "pricing_info": {
        "tool_name": "get_pricing_info",
        "tool_function": get_pricing_info,
        "formatter": format_pricing_info,
    },
    "availability_info": {
        "tool_name": "get_availability_info",
        "tool_function": get_availability_info,
        "formatter": format_availability_info,
    },
    "recycling_policy": {
        "tool_name": "get_recycling_policy",
        "tool_function": get_recycling_policy,
        "formatter": format_recycling_policy,
    },
    "donation_policy": {
        "tool_name": "get_donation_policy",
        "tool_function": get_donation_policy,
        "formatter": format_donation_policy,
    },
    "heavy_lifting_policy": {
        "tool_name": "get_heavy_lifting_policy",
        "tool_function": get_heavy_lifting_policy,
        "formatter": format_heavy_lifting_policy,
    },
    "prohibited_items": {
        "tool_name": "get_prohibited_items",
        "tool_function": get_prohibited_items,
        "formatter": format_prohibited_items,
    },
    "home_presence_info": {
        "tool_name": "get_home_presence_info",
        "tool_function": get_home_presence_info,
        "formatter": format_home_presence_info,
    },
    "team_trust_info": {
        "tool_name": "get_team_trust_info",
        "tool_function": get_team_trust_info,
        "formatter": format_team_trust_info,
    },
    "access_constraints": {
        "tool_name": "get_access_constraints",
        "tool_function": get_access_constraints,
        "formatter": format_access_constraints,
    },
    "gravel_estimate_info": {
        "tool_name": "get_gravel_estimate_info",
        "tool_function": get_gravel_estimate_info,
        "formatter": format_gravel_estimate_info,
    },
}


DEFAULT_LOG_PATH = Path(os.getenv("QUOTE_AGENT_LOG_PATH", "agent_logs.jsonl"))


def _normalize_log_path(log_path: str | Path | None = None) -> Path:
    if log_path is None:
        return DEFAULT_LOG_PATH
    return Path(log_path)


def logging_enabled(enable_logging: bool | None = None) -> bool:
    if enable_logging is not None:
        return enable_logging
    return os.getenv("QUOTE_AGENT_ENABLE_LOGGING", "0").strip().lower() in {"1", "true", "yes", "on"}


def append_log_entry(entry: dict, log_path: str | Path | None = None):
    path = _normalize_log_path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_log_entries(log_path: str | Path | None = None, limit: int | None = None) -> list[dict]:
    path = _normalize_log_path(log_path)
    if not path.exists():
        return []

    entries: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                parsed = {"raw_line": line, "malformed": True}
            entries.append(parsed)

    if limit is not None and limit >= 0:
        return entries[-limit:]
    return entries


def clear_log_file(log_path: str | Path | None = None):
    path = _normalize_log_path(log_path)
    if path.exists():
        path.unlink()


def _build_log_entry(result: dict) -> dict:
    tool_result = result.get("tool_result")
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "user_input": result.get("user_input"),
        "intent": result.get("intent"),
        "matched_keywords": result.get("matched_keywords"),
        "tool_called": result.get("tool_called"),
        "tool_ok": tool_result.get("ok") if isinstance(tool_result, dict) else None,
        "final_answer": result.get("final_answer"),
        "routing_reason": result.get("routing_reason"),
        # Day 10: include model routing metadata for inspection via CLI /logs
        "llm_used": bool(result.get("llm_used", False)),
        "llm_decision": result.get("llm_decision"),
    }


def maybe_log_result(result: dict, enable_logging: bool | None = None, log_path: str | Path | None = None):
    if not logging_enabled(enable_logging):
        return
    append_log_entry(_build_log_entry(result), log_path=log_path)


class LLMResolver(Protocol):
    """Resolve an unknown user request into a known intent in a controlled, tool-grounded way."""

    def resolve(self, *, user_input: str, memory: dict, allowed_intents: list[str]) -> dict | None:
        """
        Return None for "no decision".

        Expected dict schema:
            {
              "intent": str,            # must be in allowed_intents
              "confidence": str,        # "low" | "medium" | "high"
              "reason": str,            # short explanation for logs/debug
            }
        """
        raise NotImplementedError


def llm_enabled(enable_llm: bool | None = None) -> bool:
    if enable_llm is not None:
        return enable_llm
    return os.getenv("QUOTE_AGENT_ENABLE_LLM", "0").strip().lower() in {"1", "true", "yes", "on"}


def _openai_resolve_unknown_intent(*, user_input: str, allowed_intents: list[str]) -> dict | None:
    """
    Best-effort OpenAI call that returns a safe intent selection.

    This is intentionally narrow:
    - Only used when rule-based routing returns "unknown".
    - Output is restricted to allowed_intents.
    - If anything is off, returns None (no decision).
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    model = os.getenv("QUOTE_AGENT_LLM_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"

    intent_guide = """
Intent definitions:
- services_offered:
  Use when the user is asking what kinds of jobs, items, or service categories the business handles.
  Examples:
  - "Do you remove furniture?"
  - "Do you handle yard debris?"
  - "What kind of things do you take?"
  - "I'm not sure what category this falls under."
  - "Is this something you handle?"

- pricing_info:
  Use when the user is asking about price, cost, rates, estimates, or how much something might cost.

- contact_methods:
  Use when the user is asking how to call, text, reach, or contact the business.

- availability_info:
  Use when the user is asking about schedule, openings, appointments, dates, time slots, or when service is available.

- quote_request:
  Use when the user clearly wants to start getting a quote, estimate, or booking request for their specific job.

- prohibited_items:
  Use ONLY when the user is specifically asking whether something is not allowed, prohibited, hazardous, restricted, unsafe, or cannot be removed.
  Strong examples:
  - "Do you take paint?"
  - "Are tires allowed?"
  - "Can you remove chemicals?"
  - "What items are prohibited?"
  Do NOT use this intent for general "do you handle this?" or "what category is this?" questions.

- business_info:
  Use when the user asks general business facts such as service area, company details, or general background.

- unknown:
  Use when none of the above are a reasonably good match.

Disambiguation rules:
- If the user is asking whether the business handles a type of job/item in general, prefer services_offered.
- If the user is asking whether an item is forbidden, dangerous, or not accepted, use prohibited_items.
- If the user is asking vague "what would I need to do next?" style questions, prefer quote_request only if they are clearly moving toward getting service for their own job. Otherwise use unknown.
- When in doubt between a real intent and unknown, prefer unknown.
""".strip()

    system = (
        "You are a routing helper for a local business quote assistant. "
        "Your job is to map a single user message to exactly ONE intent from a fixed allowed list. "
        "Do not invent new intents. "
        "Use the intent definitions and disambiguation rules carefully. "
        "Be conservative. If the message does not clearly fit an intent, choose 'unknown'. "
        "Return strict JSON with exactly these keys: intent, confidence, reason."
    )

    allowed = ", ".join(allowed_intents)
    user = (
        f"Allowed intents: [{allowed}]\n\n"
        f"{intent_guide}\n\n"
        f"User message: {user_input!r}\n\n"
        "Return JSON only."
    )

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "text": {"format": {"type": "json_object"}},
        "max_output_tokens": 250,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    text_out: str | None = None
    if isinstance(parsed, dict):
        output = parsed.get("output")
        if isinstance(output, list) and output:
            item0 = output[0]
            if isinstance(item0, dict):
                content = item0.get("content")
                if isinstance(content, list) and content:
                    c0 = content[0]
                    if isinstance(c0, dict):
                        text_out = c0.get("text") if isinstance(c0.get("text"), str) else None

    if not text_out:
        return None

    try:
        decision = json.loads(text_out)
    except json.JSONDecodeError:
        return None

    if not isinstance(decision, dict):
        return None

    intent = decision.get("intent")
    confidence = decision.get("confidence")
    reason = decision.get("reason")

    if intent == "prohibited_items":
        lowered = user_input.lower()
        prohibition_cues = [
            "prohibited",
            "allowed",
            "not allowed",
            "can you take",
            "do you take",
            "hazardous",
            "chemical",
            "chemicals",
            "paint",
            "tire",
            "tires",
            "explosive",
            "explosives",
            "restricted",
            "forbidden",
            "unsafe",
        ]
        if not any(cue in lowered for cue in prohibition_cues):
            intent = "services_offered" if "services_offered" in allowed_intents else "unknown"
            confidence = "low"
            reason = "Adjusted model decision: general item/job-fit question should not map to prohibited_items without explicit prohibition cues."

    if not isinstance(intent, str) or intent not in allowed_intents:
        return None
    if not isinstance(confidence, str) or confidence not in {"low", "medium", "high"}:
        confidence = "low"
    if not isinstance(reason, str):
        reason = "Model-assisted unknown routing."

    return {"intent": intent, "confidence": confidence, "reason": reason}


class OpenAIUnknownIntentResolver:
    """LLMResolver that uses OpenAI only for unknown-intent resolution."""

    def resolve(self, *, user_input: str, memory: dict, allowed_intents: list[str]) -> dict | None:
        _ = memory
        return _openai_resolve_unknown_intent(user_input=user_input, allowed_intents=allowed_intents)


SESSION_MEMORY = {
    "last_intent": None,
    "last_tool_called": None,
    "last_topic": None,
    "last_entity": None,
    "last_item_service": None,
    "last_user_input": None,
    "last_final_answer": None,
    "quote_intake_active": False,
    "quote_intake_data": {},
    "quote_intake_next_field": None,
}


def reset_session_memory():
    """
    Reset global session memory.

    Why: tests and CLI debugging often need a clean slate.
    """
    for k in SESSION_MEMORY:
        SESSION_MEMORY[k] = None
    SESSION_MEMORY["quote_intake_active"] = False
    SESSION_MEMORY["quote_intake_data"] = {}
    SESSION_MEMORY["quote_intake_next_field"] = None


QUOTE_INTAKE_FIELDS_ORDER = [
    "name",
    "phone_number",
    "job_location",
    "job_type",
    "photos",
    "short_description",
]


def _should_start_quote_intake(user_input: str) -> bool:
    text = user_input.lower().strip()
    if "quote" not in text and "estimate" not in text:
        return False
    if any(p in text for p in ["how do", "how to", "what do you need", "need for a quote"]):
        return False
    return any(
        p in text
        for p in ["need", "looking", "want", "request", "can i get", "i'd like", "i would like"]
    )


def _start_quote_intake():
    SESSION_MEMORY["quote_intake_active"] = True
    SESSION_MEMORY["quote_intake_data"] = {}
    SESSION_MEMORY["quote_intake_next_field"] = QUOTE_INTAKE_FIELDS_ORDER[0]


def _stop_quote_intake():
    SESSION_MEMORY["quote_intake_active"] = False
    SESSION_MEMORY["quote_intake_next_field"] = None


def _get_quote_data() -> dict:
    data = SESSION_MEMORY.get("quote_intake_data")
    return data if isinstance(data, dict) else {}


def _quote_missing_fields() -> list[str]:
    data = _get_quote_data()
    missing: list[str] = []
    for field in QUOTE_INTAKE_FIELDS_ORDER:
        val = data.get(field)
        if val in (None, "", {}):
            missing.append(field)
    return missing


def _set_quote_field(field: str, value: str | bool):
    data = _get_quote_data()
    data[field] = value
    SESSION_MEMORY["quote_intake_data"] = data


def _quote_field_prompt(field: str) -> str:
    prompts = {
        "name": "What’s your name?",
        "phone_number": "What’s the best phone number to reach you?",
        "job_location": "What’s the job location (city/town or address)?",
        "job_type": "What kind of job is it (junk removal, dumpster rental, gravel delivery, demolition, land clearing, etc.)?",
        "photos": "Do you have photos you can text/email? (yes/no)",
        "short_description": "Give me a short description of what you need removed/delivered (main items + anything tricky like stairs).",
    }
    return prompts.get(field, "What info can you share for the quote?")


def _parse_phone_number(text: str) -> str | None:
    digits = re.sub(r"\D", "", text)
    if len(digits) < 10:
        return None
    return digits


def _parse_yes_no(text: str) -> bool | None:
    t = text.lower()
    if any(w in t for w in ["yes", "yep", "yeah", "sure", "i do", "can send", "have photos"]):
        return True
    if any(w in t for w in ["no", "nope", "nah", "don't", "do not", "cant", "can't"]):
        return False
    return None


def _parse_name(text: str) -> str | None:
    t = text.strip()
    m = re.search(
        r"\bmy name is\s+([A-Za-z][A-Za-z\-']+(?:\s+[A-Za-z][A-Za-z\-']+)*)\b",
        t,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    if re.fullmatch(r"[A-Za-z][A-Za-z\-']+(?:\s+[A-Za-z][A-Za-z\-']+){0,2}", t):
        return t
    return None


def _parse_job_type(text: str) -> str | None:
    t = text.lower()
    known = [
        "junk removal",
        "dumpster rental",
        "gravel delivery",
        "demolition",
        "land clearing",
        "hauling",
    ]
    for k in known:
        if k in t:
            return k
    if len(t.split()) <= 8:
        return text.strip()
    return None


def _parse_location(text: str) -> str | None:
    t = text.strip()
    if not t:
        return None
    m = re.search(r"\bin\s+([A-Za-z0-9][A-Za-z0-9 ,.'\-#]+)$", t, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    if any(ch.isdigit() for ch in t) and len(t) >= 5:
        return t
    if len(t.split()) <= 6:
        return t
    return None


def _parse_quote_field(field: str, user_input: str) -> str | bool | None:
    if field == "phone_number":
        return _parse_phone_number(user_input)
    if field == "photos":
        return _parse_yes_no(user_input)
    if field == "name":
        return _parse_name(user_input)
    if field == "job_location":
        return _parse_location(user_input)
    if field == "job_type":
        return _parse_job_type(user_input)
    if field == "short_description":
        cleaned = user_input.strip()
        return cleaned if len(cleaned) >= 3 else None
    return None


def _advance_quote_intake() -> str | None:
    missing = _quote_missing_fields()
    if not missing:
        SESSION_MEMORY["quote_intake_next_field"] = None
        return None
    SESSION_MEMORY["quote_intake_next_field"] = missing[0]
    return missing[0]


def handle_quote_intake_turn(user_input: str) -> tuple[bool, str, str | None, dict | None]:
    """Returns: (completed, final_answer, tool_called, tool_result)"""
    next_field = SESSION_MEMORY.get("quote_intake_next_field")
    if not isinstance(next_field, str) or not next_field:
        next_field = _advance_quote_intake()

    if next_field:
        parsed = _parse_quote_field(next_field, user_input)
        if parsed is None:
            return False, _quote_field_prompt(next_field), None, None

        _set_quote_field(next_field, parsed)
        next_field = _advance_quote_intake()

        if next_field:
            return False, _quote_field_prompt(next_field), None, None

    data = _get_quote_data()
    _stop_quote_intake()

    contact_tool_result = get_contact_methods()
    contact_msg = format_contact_methods(contact_tool_result)

    photos_val = data.get("photos")
    photos_note = ""
    if photos_val is False:
        photos_note = " If you can, photos help us quote faster."

    summary = (
        "Got it — here’s what I captured for your quote:\n"
        f"- Name: {data.get('name')}\n"
        f"- Phone: {data.get('phone_number')}\n"
        f"- Location: {data.get('job_location')}\n"
        f"- Job type: {data.get('job_type')}\n"
        f"- Photos: {'yes' if data.get('photos') else 'no'}\n"
        f"- Description: {data.get('short_description')}\n\n"
        f"Next step: {contact_msg}{photos_note}"
    )
    return True, summary, "get_contact_methods", contact_tool_result


INTENT_RULES = [
    {
        "intent": "greeting",
        "keywords": ["hi", "hello", "hey", "yo"],
        "match_type": "exact",
        "confidence": "high",
        "priority": 100,
        "routing_reason": "Matched a greeting exactly, so no tool is needed.",
    },
    {
        "intent": "contact_methods",
        "keywords": [
            "contact",
            "reach",
            "phone",
            "number",
            "call",
            "text",
            "email",
            "book",
            "booking",
            "appointment",
            "voicemail",
            "schedule service",
            "schedule a job",
        ],
        "match_type": "contains",
        "confidence": "high",
        "priority": 80,
        "routing_reason": "Matched contact or booking keywords, so route to contact methods.",
    },
    {
        "intent": "pricing_info",
        "keywords": ["price", "pricing", "cost", "how much", "minimum", "estimate", "rates", "fee"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 75,
        "routing_reason": "Matched pricing keywords, so route to pricing info.",
    },
    {
        "intent": "availability_info",
        "keywords": [
            "availability",
            "available",
            "openings",
            "when can",
            "soonest",
            "start with",
            "next week",
            "tomorrow",
            "today",
            "friday",
            "saturday",
            "sunday",
        ],
        "match_type": "contains",
        "confidence": "high",
        "priority": 60,
        "routing_reason": "Matched availability keywords, so route to availability info.",
    },
    {
        "intent": "hours",
        "keywords": ["hours", "open", "close", "weekend", "weekends"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 55,
        "routing_reason": "Matched business hours keywords, so route to hours.",
    },
    {
        "intent": "service_area",
        "keywords": ["areas", "serve", "service area", "towns", "counties", "distance"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 55,
        "routing_reason": "Matched service area keywords, so route to service area info.",
    },
    {
        "intent": "recycling_policy",
        "keywords": ["recycle", "recycling", "recycled"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 70,
        "routing_reason": "Matched recycling keywords, so route to recycling policy.",
    },
    {
        "intent": "donation_policy",
        "keywords": ["donate", "donation", "donate usable", "charity"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 70,
        "routing_reason": "Matched donation keywords, so route to donation policy.",
    },
    {
        "intent": "heavy_lifting_policy",
        "keywords": ["heavy", "lifting", "help lift", "do i need to help"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 72,
        "routing_reason": "Matched heavy lifting keywords, so route to heavy lifting policy.",
    },
    {
        "intent": "prohibited_items",
        "keywords": [
            "paint",
            "tire",
            "tires",
            "hazardous",
            "chemical",
            "chemicals",
            "explosive",
            "explosives",
        ],
        "match_type": "contains",
        "confidence": "high",
        "priority": 78,
        "routing_reason": "Matched prohibited item keywords, so route to prohibited items.",
    },
    {
        "intent": "home_presence_info",
        "keywords": ["be home", "need to be home", "home during", "present", "do i need to be there"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 74,
        "routing_reason": "Matched home presence keywords, so route to home presence info.",
    },
    {
        "intent": "team_trust_info",
        "keywords": ["background", "checked", "insured", "bonded", "veteran", "veterans"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 76,
        "routing_reason": "Matched team trust keywords, so route to team trust info.",
    },
    {
        "intent": "access_constraints",
        "keywords": ["driveway", "narrow", "low power lines", "access", "gate", "clearance"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 73,
        "routing_reason": "Matched access constraints keywords, so route to access constraints.",
    },
    {
        "intent": "gravel_estimate_info",
        "keywords": ["gravel", "how much gravel", "tons", "yards", "estimate gravel"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 77,
        "routing_reason": "Matched gravel estimate keywords, so route to gravel estimate info.",
    },
    {
        "intent": "services_offered",
        "keywords": [
            "services",
            "offer",
            "do you do",
            "junk",
            "removal",
            "hauling",
            "gravel",
            "dumpster",
            "land clearing",
            "demolition",
            "piano",
            "pianos",
            "appliance",
            "appliances",
            "trailer",
            "trailers",
            "furniture",
            "furniture",
            "mattress",
            "mattresses",
        ],
        "match_type": "contains",
        "confidence": "medium",
        "priority": 40,
        "routing_reason": "Matched services keywords, so route to services offered.",
    },
    {
        "intent": "payment_methods",
        "keywords": ["cash", "card", "credit", "debit", "venmo", "paypal", "check"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 65,
        "routing_reason": "Matched payment keywords, so route to payment methods.",
    },
    {
        "intent": "required_quote_info",
        "keywords": ["need for a quote", "required", "what do you need", "info for a quote", "for that"],
        "match_type": "contains",
        "confidence": "high",
        "priority": 85,
        "routing_reason": "Matched quote requirements keywords, so route to required quote info.",
    },
    {
        "intent": "quote_methods",
        "keywords": ["quote", "estimate", "how do i get a quote", "get a quote"],
        "match_type": "contains",
        "confidence": "medium",
        "priority": 50,
        "routing_reason": "Matched quote keywords, so route to quote methods.",
    },
]


def get_keyword_matches(text: str, rule: dict) -> list[str]:
    if rule["match_type"] == "exact":
        if text in rule["keywords"]:
            return [text]
        return []

    if rule["match_type"] == "contains":
        return [kw for kw in rule["keywords"] if kw in text]

    if rule["match_type"] == "contains_any_two":
        matches = [kw for kw in rule["keywords"] if kw in text]
        return matches if len(matches) >= 2 else []

    return []


def detect_intent(user_input: str) -> dict:
    text = user_input.lower().strip()
    candidates = []

    for rule in INTENT_RULES:
        matched_keywords = get_keyword_matches(text, rule)
        if not matched_keywords:
            continue

        base_score = len(matched_keywords)
        specificity_bonus = sum(1 for kw in matched_keywords if " " in kw)
        total_score = base_score + specificity_bonus

        candidates.append(
            {
                "intent": rule["intent"],
                "matched_keywords": matched_keywords,
                "confidence": rule["confidence"],
                "routing_reason": rule["routing_reason"],
                "priority": rule["priority"],
                "base_score": base_score,
                "specificity_bonus": specificity_bonus,
                "score": total_score,
            }
        )

    if not candidates:
        return {
            "intent": "unknown",
            "matched_keywords": [],
            "confidence": "low",
            "routing_reason": "No rule matched the user input, so the request is treated as unknown.",
            "debug": {"candidates": [], "winner": "unknown"},
        }

    sorted_candidates = sorted(candidates, key=lambda c: (c["score"], c["priority"]), reverse=True)
    best = sorted_candidates[0]

    debug_candidates = [
        {
            "intent": c["intent"],
            "matched_keywords": c["matched_keywords"],
            "base_score": c["base_score"],
            "specificity_bonus": c["specificity_bonus"],
            "score": c["score"],
            "priority": c["priority"],
        }
        for c in sorted_candidates
    ]

    return {
        "intent": best["intent"],
        "matched_keywords": best["matched_keywords"],
        "confidence": best["confidence"],
        "routing_reason": best["routing_reason"],
        "debug": {"candidates": debug_candidates, "winner": best["intent"]},
    }


def answer_directly(intent: str) -> str:
    if intent == "greeting":
        return "Hi! How can I help you today?"
    if intent == "unknown":
        return "I’m not sure about that. You can ask about services, pricing, quotes, scheduling, or business info."
    return "I can help with that."


def is_time_specific_booking_request(user_input: str) -> bool:
    text = user_input.lower()
    return any(day in text for day in ["today", "tomorrow", "friday", "saturday", "sunday", "next week"])


def build_mixed_booking_availability_answer(contact_tool_result: dict, availability_tool_result: dict) -> str:
    return f"{format_contact_methods(contact_tool_result)} {format_availability_info(availability_tool_result)}"


def _extract_last_entity(user_input: str) -> str | None:
    text = user_input.lower()

    entity_map = {
        "cash": ["cash"],
        "card": ["card", "credit", "debit"],
        "venmo": ["venmo"],
        "paypal": ["paypal"],
        "check": ["check", "cheque"],
        "paint": ["paint"],
        "tires": ["tire", "tires"],
        "chemicals": ["chemical", "chemicals", "hazardous"],
        "explosives": ["explosive", "explosives"],
        "junk removal": ["junk"],
        "piano": ["piano"],
        "appliance": ["appliance", "appliances"],
        "furniture": ["furniture"],
        "mattress": ["mattress", "mattresses"],
        "debris": ["debris"],
        "gravel": ["gravel"],
        "dumpster": ["dumpster"],
        "demolition": ["demolition"],
        "land clearing": ["land clearing"],
        "quote": ["quote", "estimate"],
        "booking": ["book", "booking", "appointment", "schedule"],
        "availability": ["available", "availability", "openings", "soonest"],
        "hours": ["hours", "open", "close"],
        "service area": ["service area", "serve", "areas"],
        "recycling": ["recycle", "recycling"],
        "donation": ["donate", "donation"],
        "trust": ["insured", "bonded", "background", "checked", "veteran", "veterans"],
        "access": ["driveway", "narrow", "clearance", "gate", "access"],
    }

    for canonical, synonyms in entity_map.items():
        if any(s in text for s in synonyms):
            return canonical

    return None


def _extract_service_items(user_input: str) -> list[str]:
    text = user_input.lower()
    item_synonyms = {
        "piano": ["piano", "pianos"],
        "appliance": [
            "appliance",
            "appliances",
            "fridge",
            "refrigerator",
            "washer",
            "dryer",
            "stove",
            "oven",
        ],
        "trailer": ["trailer", "trailers"],
        "furniture": ["furniture", "couch", "sofa", "table", "dresser", "bed frame"],
        "mattress": ["mattress", "mattresses"],
    }

    found: list[str] = []
    for canonical, synonyms in item_synonyms.items():
        if any(s in text for s in synonyms):
            found.append(canonical)

    return found


def build_targeted_services_answer(user_input: str, tool_result: dict) -> str | None:
    items = _extract_service_items(user_input)
    if not items:
        return None

    data = tool_result.get("data") or {}
    note = data.get("note", "Send photos for the fastest quote.")

    if len(items) == 1:
        item = items[0]
        if item == "piano":
            return (
                "Yes — we can help with piano removal/hauling. "
                "Because pianos are heavy and awkward, access (stairs/tight turns) matters. "
                f"{note}"
            )
        if item == "appliance":
            return f"Yes — we can pick up and haul away appliances. {note}"
        if item == "trailer":
            return f"Yes — we can haul trailers in many cases. {note}"
        if item == "furniture":
            return f"Yes — we commonly remove/haul furniture. {note}"
        if item == "mattress":
            return f"Yes — we can pick up and haul away mattresses. {note}"

    items_readable = ", ".join(items)
    return f"Yes — we can often help with {items_readable}. {note}"


def get_memory_snapshot() -> dict:
    return dict(SESSION_MEMORY)


def update_session_memory(
    user_input: str,
    intent: str,
    tool_called: str | None,
    final_answer: str,
    entity: str | None,
):
    SESSION_MEMORY["last_user_input"] = user_input
    SESSION_MEMORY["last_intent"] = intent
    SESSION_MEMORY["last_tool_called"] = tool_called
    SESSION_MEMORY["last_final_answer"] = final_answer

    if intent in TOOL_REGISTRY:
        SESSION_MEMORY["last_topic"] = intent

    if entity is not None:
        SESSION_MEMORY["last_entity"] = entity

        if entity in {
            "piano",
            "appliance",
            "trailer",
            "furniture",
            "mattress",
            "junk removal",
            "dumpster",
            "gravel",
            "demolition",
            "land clearing",
        }:
            SESSION_MEMORY["last_item_service"] = entity


def resolve_followup_intent(user_input: str, memory: dict) -> dict | None:
    text = user_input.lower().strip()
    last_intent = memory.get("last_intent")
    last_topic = memory.get("last_topic")
    last_entity = memory.get("last_entity")

    followup_markers = ["that", "it", "this", "those", "them", "for that", "about that"]

    short_pricing_markers = ["how much", "cost", "price"]
    short_contact_markers = ["text", "call", "phone", "email"]
    what_about_marker = "what about"

    if any(m in text for m in short_pricing_markers) and len(text.split()) <= 3 and last_topic:
        return {
            "intent": "pricing_info",
            "matched_keywords": ["followup_short_pricing"],
            "confidence": "medium",
            "routing_reason": "Short pricing follow-up; using recent context.",
            "debug": {"followup": True, "based_on": last_topic, "entity": last_entity},
        }

    if what_about_marker in text and last_topic:
        if any(
            k in text
            for k in ["piano", "pianos", "appliance", "appliances", "furniture", "mattress", "mattresses"]
        ):
            return {
                "intent": "services_offered",
                "matched_keywords": ["followup_what_about"],
                "confidence": "medium",
                "routing_reason": "Follow-up question about another service item.",
                "debug": {"followup": True, "based_on": last_topic, "entity": last_entity},
            }

    if any(m in text for m in followup_markers) and last_topic:
        if any(k in text for k in short_contact_markers):
            return {
                "intent": "contact_methods",
                "matched_keywords": ["followup"],
                "confidence": "medium",
                "routing_reason": "Follow-up question about contact/booking.",
                "debug": {"followup": True, "based_on": last_topic, "entity": last_entity},
            }

        if any(k in text for k in short_pricing_markers):
            return {
                "intent": "pricing_info",
                "matched_keywords": ["followup"],
                "confidence": "medium",
                "routing_reason": "Follow-up question about pricing.",
                "debug": {"followup": True, "based_on": last_topic, "entity": last_entity},
            }

        if any(k in text for k in ["book", "schedule", "appointment"]):
            return {
                "intent": "contact_methods",
                "matched_keywords": ["followup"],
                "confidence": "medium",
                "routing_reason": "Follow-up question about booking/contact.",
                "debug": {"followup": True, "based_on": last_topic, "entity": last_entity},
            }

        if "take" in text or "accept" in text:
            if last_topic in ["payment_methods", "prohibited_items"]:
                return {
                    "intent": last_topic,
                    "matched_keywords": ["followup"],
                    "confidence": "medium",
                    "routing_reason": "Follow-up question reuses prior 'take/accept' topic.",
                    "debug": {"followup": True, "based_on": last_topic, "entity": last_entity},
                }

    if last_intent == "contact_methods" and len(text.split()) <= 2 and any(
        day in text
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    ):
        return {
            "intent": "contact_methods",
            "matched_keywords": ["followup_time_only"],
            "confidence": "medium",
            "routing_reason": "Time-only follow-up after booking prompt; continue booking instructions.",
            "debug": {"followup": True, "based_on": last_intent, "entity": last_entity},
        }

    if last_intent == "availability_info" and any(k in text for k in ["next week", "tomorrow", "today", "friday"]):
        return {
            "intent": "contact_methods",
            "matched_keywords": ["followup_availability_to_booking"],
            "confidence": "medium",
            "routing_reason": "Availability follow-up suggests moving to booking/contact.",
            "debug": {"followup": True, "based_on": last_intent, "entity": last_entity},
        }

    return None


def _is_short_ambiguous_pricing(user_input: str, memory: dict) -> bool:
    text = user_input.lower().strip()
    if len(text.split()) > 3:
        return False
    if not any(k in text for k in ["how much", "cost", "price"]):
        return False

    entity = _extract_last_entity(user_input)
    if entity in {
        "piano",
        "appliance",
        "trailer",
        "furniture",
        "mattress",
        "junk removal",
        "dumpster",
        "gravel",
        "demolition",
        "land clearing",
    }:
        return False

    if memory.get("last_topic"):
        return False

    return True


def _is_ambiguous_pronoun_request(user_input: str, memory: dict) -> bool:
    text = user_input.lower().strip()

    if len(text.split()) > 5:
        return False

    tokens = re.findall(r"[a-z']+", text)
    pronouns = {"that", "it", "this", "those", "them"}
    if not any(t in pronouns for t in tokens):
        return False

    if memory.get("last_topic"):
        return False

    domain_markers = [
        "low power lines",
        "driveway",
        "clearance",
        "gravel",
        "dumpster",
        "junk",
        "piano",
        "appliance",
    ]
    if any(dm in text for dm in domain_markers):
        return False

    verbs = ["take", "accept", "remove", "haul", "do", "book", "schedule", "cost", "price", "charge"]
    return any(v in text for v in verbs)


def _is_low_info_service_question(user_input: str, memory: dict) -> bool:
    text = user_input.lower().strip()
    if text in {
        "do you do it",
        "do you do it?",
        "do you do that",
        "do you do that?",
        "do you do this",
        "do you do this?",
    }:
        return True
    if len(text.split()) <= 4 and ("do you do" in text) and any(p in text for p in ["it", "that", "this", "them"]):
        if not memory.get("last_topic"):
            return True
    return False


def _clarifying_fallback_answer(user_input: str) -> str:
    text = user_input.lower().strip()
    if any(k in text for k in ["how much", "cost", "price"]):
        return (
            "Quick check — what are you asking about pricing for (junk removal, dumpster rental, gravel delivery, demolition, etc.)?"
        )
    if "take" in text or "accept" in text:
        return "What item/material are you referring to (and your location)?"
    if "do you do" in text:
        return "Which service or item are you asking about (junk removal, dumpster rental, gravel delivery, a piano, appliances, etc.)?"
    return "Can you clarify what you’re referring to (the service/item)?"


def _route_ambiguity(user_input: str, memory_before: dict) -> dict | None:
    if _is_short_ambiguous_pricing(user_input, memory_before):
        return {
            "intent": "unknown",
            "final_answer": _clarifying_fallback_answer(user_input),
            "routing_reason": "Ambiguous short pricing question without context; asking clarifying question.",
            "matched_keywords": ["ambiguous_short_pricing"],
            "confidence": "low",
            "debug": {"ambiguity_guard": True, "kind": "pricing"},
        }

    if _is_low_info_service_question(user_input, memory_before):
        return {
            "intent": "unknown",
            "final_answer": _clarifying_fallback_answer(user_input),
            "routing_reason": "Vague service question without context; asking clarifying question.",
            "matched_keywords": ["ambiguous_vague_service"],
            "confidence": "low",
            "debug": {"ambiguity_guard": True, "kind": "vague_service"},
        }

    if _is_ambiguous_pronoun_request(user_input, memory_before):
        return {
            "intent": "unknown",
            "final_answer": _clarifying_fallback_answer(user_input),
            "routing_reason": "Pronoun-only request without context; asking clarifying question.",
            "matched_keywords": ["ambiguous_pronoun"],
            "confidence": "low",
            "debug": {"ambiguity_guard": True, "kind": "pronoun"},
        }

    return None


def build_response(
    user_input: str,
    llm_used: bool,
    llm_decision: dict | None,
    intent: str,
    should_use_tool: bool,
    tool_called: str | None,
    tool_result: dict | None,
    final_answer: str,
    routing_reason: str,
    matched_keywords: list[str],
    confidence: str,
    debug: dict,
    memory_before: dict,
    memory_after: dict,
) -> dict:
    return {
        "user_input": user_input,
        "llm_used": llm_used,
        "llm_decision": llm_decision,
        "intent": intent,
        "should_use_tool": should_use_tool,
        "tool_called": tool_called,
        "tool_result": tool_result,
        "final_answer": final_answer,
        "routing_reason": routing_reason,
        "matched_keywords": matched_keywords,
        "confidence": confidence,
        "debug": debug,
        "memory_before": memory_before,
        "memory_after": memory_after,
    }


def run_agent(
    user_input: str,
    enable_logging: bool | None = None,
    log_path: str | Path | None = None,
    enable_llm: bool | None = None,
    llm_resolver: LLMResolver | None = None,
) -> dict:
    memory_before = get_memory_snapshot()
    llm_used = False
    llm_decision: dict | None = None

    if SESSION_MEMORY.get("quote_intake_active") is True:
        completed, answer, tool_called, tool_result = handle_quote_intake_turn(user_input)
        entity = _extract_last_entity(user_input)

        update_session_memory(
            user_input=user_input,
            intent="quote_intake",
            tool_called=tool_called,
            final_answer=answer,
            entity=entity,
        )

        memory_after = get_memory_snapshot()
        result = build_response(
            user_input=user_input,
            llm_used=llm_used,
            llm_decision=llm_decision,
            intent="quote_intake",
            should_use_tool=tool_called is not None,
            tool_called=tool_called,
            tool_result=tool_result,
            final_answer=answer,
            routing_reason="Quote intake is active; collecting required quote information.",
            matched_keywords=["quote_intake"],
            confidence="high",
            debug={"quote_intake": True, "completed": completed},
            memory_before=memory_before,
            memory_after=memory_after,
        )
        maybe_log_result(result, enable_logging=enable_logging, log_path=log_path)
        return result

    if _should_start_quote_intake(user_input):
        _start_quote_intake()
        first_field = SESSION_MEMORY.get("quote_intake_next_field") or QUOTE_INTAKE_FIELDS_ORDER[0]
        prompt = _quote_field_prompt(str(first_field))
        entity = _extract_last_entity(user_input)

        update_session_memory(
            user_input=user_input,
            intent="quote_intake",
            tool_called=None,
            final_answer=prompt,
            entity=entity,
        )

        memory_after = get_memory_snapshot()
        result = build_response(
            user_input=user_input,
            llm_used=llm_used,
            llm_decision=llm_decision,
            intent="quote_intake",
            should_use_tool=False,
            tool_called=None,
            tool_result=None,
            final_answer=prompt,
            routing_reason="Detected an active quote request; starting quote intake flow.",
            matched_keywords=["quote", "intake"],
            confidence="high",
            debug={"quote_intake": True, "started": True},
            memory_before=memory_before,
            memory_after=memory_after,
        )
        maybe_log_result(result, enable_logging=enable_logging, log_path=log_path)
        return result

    ambiguity_override = _route_ambiguity(user_input, memory_before)
    if ambiguity_override is not None:
        entity = _extract_last_entity(user_input)
        update_session_memory(
            user_input=user_input,
            intent=ambiguity_override["intent"],
            tool_called=None,
            final_answer=str(ambiguity_override["final_answer"]),
            entity=entity,
        )

        memory_after = get_memory_snapshot()
        result = build_response(
            user_input=user_input,
            llm_used=llm_used,
            llm_decision=llm_decision,
            intent=ambiguity_override["intent"],
            should_use_tool=False,
            tool_called=None,
            tool_result=None,
            final_answer=str(ambiguity_override["final_answer"]),
            routing_reason=str(ambiguity_override["routing_reason"]),
            matched_keywords=list(ambiguity_override["matched_keywords"]),
            confidence=str(ambiguity_override["confidence"]),
            debug=dict(ambiguity_override.get("debug") or {}),
            memory_before=memory_before,
            memory_after=memory_after,
        )
        maybe_log_result(result, enable_logging=enable_logging, log_path=log_path)
        return result

    followup_routing = resolve_followup_intent(user_input, memory_before)
    routing = followup_routing if followup_routing is not None else detect_intent(user_input)

    intent = routing["intent"]
    matched_keywords = routing["matched_keywords"]
    confidence = routing["confidence"]
    routing_reason = routing["routing_reason"]
    debug = routing["debug"]

    if intent == "unknown" and llm_enabled(enable_llm):
        if llm_resolver is None:
            llm_resolver = OpenAIUnknownIntentResolver()

        allowed_intents = sorted(set(list(TOOL_REGISTRY.keys()) + ["unknown", "greeting"]))
        llm_decision = llm_resolver.resolve(
            user_input=user_input,
            memory=memory_before,
            allowed_intents=allowed_intents,
        )

        if isinstance(llm_decision, dict):
            llm_used = True
            chosen_intent = llm_decision.get("intent")
            if isinstance(chosen_intent, str) and chosen_intent in TOOL_REGISTRY:
                intent = chosen_intent
                matched_keywords = ["llm_unknown_intent"]
                confidence = str(llm_decision.get("confidence") or "medium")
                routing_reason = f"Model-assisted routing for unknown intent. ({llm_decision.get('reason')})"
                debug = {"llm": llm_decision, "previous": routing}

    if intent not in TOOL_REGISTRY:
        final_answer = answer_directly(intent)
        entity = _extract_last_entity(user_input)

        update_session_memory(
            user_input=user_input,
            intent=intent,
            tool_called=None,
            final_answer=final_answer,
            entity=entity,
        )

        memory_after = get_memory_snapshot()
        result = build_response(
            user_input=user_input,
            llm_used=llm_used,
            llm_decision=llm_decision,
            intent=intent,
            should_use_tool=False,
            tool_called=None,
            tool_result=None,
            final_answer=final_answer,
            routing_reason=routing_reason,
            matched_keywords=matched_keywords,
            confidence=confidence,
            debug=debug,
            memory_before=memory_before,
            memory_after=memory_after,
        )
        maybe_log_result(result, enable_logging=enable_logging, log_path=log_path)
        return result

    tool_config = TOOL_REGISTRY[intent]
    tool_function = tool_config["tool_function"]
    formatter = tool_config["formatter"]
    tool_name = tool_config["tool_name"]

    tool_result = tool_function()
    final_answer = formatter(tool_result)

    if intent == "services_offered":
        targeted = build_targeted_services_answer(user_input, tool_result)
        if targeted is not None:
            final_answer = targeted

    if intent == "contact_methods" and is_time_specific_booking_request(user_input):
        availability_tool_result = get_availability_info()
        final_answer = build_mixed_booking_availability_answer(
            contact_tool_result=tool_result,
            availability_tool_result=availability_tool_result,
        )

    entity = _extract_last_entity(user_input)
    update_session_memory(
        user_input=user_input,
        intent=intent,
        tool_called=tool_name,
        final_answer=final_answer,
        entity=entity,
    )

    memory_after = get_memory_snapshot()
    result = build_response(
        user_input=user_input,
        llm_used=llm_used,
        llm_decision=llm_decision,
        intent=intent,
        should_use_tool=True,
        tool_called=tool_name,
        tool_result=tool_result,
        final_answer=final_answer,
        routing_reason=routing_reason,
        matched_keywords=matched_keywords,
        confidence=confidence,
        debug=debug,
        memory_before=memory_before,
        memory_after=memory_after,
    )
    maybe_log_result(result, enable_logging=enable_logging, log_path=log_path)
    return result