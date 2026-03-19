# tools.py
"""Business-domain tools and formatters.

Tool contract:
- Each tool returns:
    {
      "tool": str,
      "ok": bool,
      "data": Any | None,
      "error": str | None
    }

Formatter contract:
- Must never raise due to malformed tool results.
- If tool_result["ok"] is False or required fields are missing, return a friendly fallback.
"""

from __future__ import annotations

from typing import Any, TypedDict

from business_data import BUSINESS_INFO


class ToolResult(TypedDict):
    tool: str
    ok: bool
    data: Any | None
    error: str | None


def _tool_result(
    tool: str,
    *,
    data: Any | None = None,
    ok: bool = True,
    error: str | None = None,
) -> ToolResult:
    return {"tool": tool, "ok": ok, "data": data, "error": error}


def _safe_data(tool_result: dict) -> Any:
    if not isinstance(tool_result, dict):
        return None
    if tool_result.get("ok") is False:
        return None
    return tool_result.get("data")


def _format_tool_error(tool_result: Any, *, fallback: str) -> str:
    if not isinstance(tool_result, dict):
        return fallback
    error = tool_result.get("error")
    if isinstance(error, str) and error.strip():
        return f"{fallback} ({error.strip()})"
    return fallback

# -----------------------------
# Tools
# -----------------------------
def get_service_area() -> ToolResult:
    try:
        return _tool_result(
            "get_service_area",
            data={
                "service_areas": BUSINESS_INFO.get("service_areas", []),
                "priority_areas": BUSINESS_INFO.get("priority_areas", []),
            },
        )
    except Exception as e:
        return _tool_result("get_service_area", ok=False, error=str(e))


def get_quote_methods() -> ToolResult:
    try:
        return _tool_result("get_quote_methods", data=BUSINESS_INFO.get("quote_methods", []))
    except Exception as e:
        return _tool_result("get_quote_methods", ok=False, error=str(e))


def get_payment_methods() -> ToolResult:
    try:
        return _tool_result("get_payment_methods", data=BUSINESS_INFO.get("payment_methods", []))
    except Exception as e:
        return _tool_result("get_payment_methods", ok=False, error=str(e))


def get_required_quote_info() -> ToolResult:
    try:
        return _tool_result("get_required_quote_info", data=BUSINESS_INFO.get("required_quote_info", []))
    except Exception as e:
        return _tool_result("get_required_quote_info", ok=False, error=str(e))


def get_hours() -> ToolResult:
    try:
        return _tool_result("get_hours", data=BUSINESS_INFO.get("hours", {}))
    except Exception as e:
        return _tool_result("get_hours", ok=False, error=str(e))


def get_contact_methods() -> ToolResult:
    try:
        return _tool_result("get_contact_methods", data=BUSINESS_INFO.get("contact_methods", {}))
    except Exception as e:
        return _tool_result("get_contact_methods", ok=False, error=str(e))


def get_services_offered() -> ToolResult:
    try:
        return _tool_result("get_services_offered", data=BUSINESS_INFO.get("services_offered", {}))
    except Exception as e:
        return _tool_result("get_services_offered", ok=False, error=str(e))


def get_pricing_info() -> ToolResult:
    try:
        return _tool_result("get_pricing_info", data=BUSINESS_INFO.get("pricing_info", {}))
    except Exception as e:
        return _tool_result("get_pricing_info", ok=False, error=str(e))


def get_availability_info() -> ToolResult:
    """
    Your business_data.py stores availability under `calendar_setup`.
    We adapt that into a {message: str} shape expected by format_availability_info().
    """
    try:
        calendar_setup = BUSINESS_INFO.get("calendar_setup", {})
        message = ""
        if isinstance(calendar_setup, dict):
            message = str(calendar_setup.get("message", "")).strip()
        if not message:
            message = "Availability varies—please call or text to confirm a time."
        return _tool_result("get_availability_info", data={"message": message})
    except Exception as e:
        return _tool_result("get_availability_info", ok=False, error=str(e))


def get_recycling_policy() -> ToolResult:
    try:
        return _tool_result("get_recycling_policy", data=BUSINESS_INFO.get("recycling_policy", {}))
    except Exception as e:
        return _tool_result("get_recycling_policy", ok=False, error=str(e))


def get_donation_policy() -> ToolResult:
    try:
        return _tool_result("get_donation_policy", data=BUSINESS_INFO.get("donation_policy", {}))
    except Exception as e:
        return _tool_result("get_donation_policy", ok=False, error=str(e))


def get_heavy_lifting_policy() -> ToolResult:
    try:
        return _tool_result("get_heavy_lifting_policy", data=BUSINESS_INFO.get("heavy_lifting_policy", {}))
    except Exception as e:
        return _tool_result("get_heavy_lifting_policy", ok=False, error=str(e))


def get_prohibited_items() -> ToolResult:
    try:
        return _tool_result("get_prohibited_items", data=BUSINESS_INFO.get("prohibited_items", {}))
    except Exception as e:
        return _tool_result("get_prohibited_items", ok=False, error=str(e))


def get_home_presence_info() -> ToolResult:
    try:
        return _tool_result("get_home_presence_info", data=BUSINESS_INFO.get("home_presence_info", {}))
    except Exception as e:
        return _tool_result("get_home_presence_info", ok=False, error=str(e))


def get_team_trust_info() -> ToolResult:
    try:
        return _tool_result("get_team_trust_info", data=BUSINESS_INFO.get("team_trust_info", {}))
    except Exception as e:
        return _tool_result("get_team_trust_info", ok=False, error=str(e))


def get_access_constraints() -> ToolResult:
    try:
        return _tool_result("get_access_constraints", data=BUSINESS_INFO.get("access_constraints", {}))
    except Exception as e:
        return _tool_result("get_access_constraints", ok=False, error=str(e))


def get_gravel_estimate_info() -> ToolResult:
    try:
        return _tool_result("get_gravel_estimate_info", data=BUSINESS_INFO.get("gravel_estimate_info", {}))
    except Exception as e:
        return _tool_result("get_gravel_estimate_info", ok=False, error=str(e))


# -----------------------------
# Formatters (resilient)
# -----------------------------
def format_team_trust_info(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve team trust info right now.")
    return str(data["message"])


def format_access_constraints(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve access constraint info right now.")
    return str(data["message"])


def format_gravel_estimate_info(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve gravel estimate info right now.")
    return str(data["message"])


def format_service_area(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict):
        return _format_tool_error(tool_result, fallback="I couldn't retrieve service area info right now.")

    service_areas = data.get("service_areas") if isinstance(data.get("service_areas"), list) else []
    priority_areas = data.get("priority_areas") if isinstance(data.get("priority_areas"), list) else []

    if not service_areas and not priority_areas:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve service area details right now.")

    areas = ", ".join(map(str, service_areas)) if service_areas else "our local area"
    priority = ", ".join(map(str, priority_areas)) if priority_areas else "our most common routes"
    return f"We typically serve these areas: {areas}. Our priority areas for more calls are: {priority}."


def format_quote_methods(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, list):
        return _format_tool_error(tool_result, fallback="I couldn't retrieve quote methods right now.")
    return "You can get a quote by: " + ", ".join(map(str, data)) + "."


def format_payment_methods(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, list):
        return _format_tool_error(tool_result, fallback="I couldn't retrieve payment methods right now.")
    return "We accept these payment methods: " + ", ".join(map(str, data)) + "."


def format_required_quote_info(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, list):
        return _format_tool_error(tool_result, fallback="I couldn't retrieve quote requirements right now.")
    return "To give you a quote, we usually need: " + ", ".join(map(str, data)) + "."


def format_hours(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict):
        return _format_tool_error(tool_result, fallback="I couldn't retrieve business hours right now.")

    weekday = data.get("weekday")
    weekend = data.get("weekend")

    if not weekday and not weekend:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve business hours right now.")

    parts: list[str] = []
    if weekday:
        parts.append(f"Weekdays: {weekday}")
    if weekend:
        parts.append(f"Weekends: {weekend}")
    return "Our hours are: " + " | ".join(parts) + "."


def format_contact_methods(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict):
        return _format_tool_error(tool_result, fallback="I couldn't retrieve contact methods right now.")

    phone = data.get("phone")
    text = data.get("text")
    email = data.get("email")
    booking = data.get("booking")

    parts: list[str] = []
    if phone:
        parts.append(f"Call: {phone}")
    if text:
        parts.append(f"Text: {text}")
    if email:
        parts.append(f"Email: {email}")
    if booking:
        parts.append(f"Book online: {booking}")

    if not parts:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve contact methods right now.")

    return "You can reach us via: " + " | ".join(parts) + "."


def format_services_offered(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict):
        return _format_tool_error(tool_result, fallback="I couldn't retrieve services offered right now.")

    general_services = data.get("general_services") if isinstance(data.get("general_services"), list) else []
    common_items = data.get("common_items") if isinstance(data.get("common_items"), list) else []
    note = data.get("note") if isinstance(data.get("note"), str) else ""

    if not general_services and not common_items:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve services offered right now.")

    general_services_s = ", ".join(map(str, general_services)) if general_services else "junk removal"
    common_items_s = ", ".join(map(str, common_items)) if common_items else "common household and jobsite items"

    msg = (
        f"We offer services such as: {general_services_s}. "
        f"We commonly handle items/jobs like: {common_items_s}."
    )
    return f"{msg} {note}".strip()


def format_pricing_info(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve pricing info right now.")
    return str(data["message"])


def format_availability_info(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve availability info right now.")
    return str(data["message"])


def format_recycling_policy(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve recycling info right now.")
    return str(data["message"])


def format_donation_policy(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve donation info right now.")
    return str(data["message"])


def format_heavy_lifting_policy(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve heavy lifting info right now.")
    return str(data["message"])


def format_prohibited_items(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict):
        return _format_tool_error(tool_result, fallback="I couldn't retrieve prohibited item info right now.")

    message = data.get("message")
    not_removed = data.get("not_removed") if isinstance(data.get("not_removed"), list) else []

    if not message:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve prohibited item info right now.")

    if not not_removed:
        return str(message)

    return f"{message} Items generally not removed include: {', '.join(map(str, not_removed))}."


def format_home_presence_info(tool_result: dict) -> str:
    data = _safe_data(tool_result)
    if not isinstance(data, dict) or "message" not in data:
        return _format_tool_error(tool_result, fallback="I couldn't retrieve home presence info right now.")
    return str(data["message"])