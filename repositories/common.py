import json


def normalize_tool_payload(payload):
    """Return a tool dictionary with safe defaults for public rendering.

    Admin drafts may legitimately be incomplete. Public templates must never
    crash because an optional nested field is missing.
    """
    tool = dict(payload or {})

    tool.setdefault("slug", "")
    tool.setdefault("name", "Unnamed tool")
    tool.setdefault("description", "No description is available yet.")
    tool.setdefault("category", "Uncategorized")
    tool.setdefault("subcategory", "")
    tool.setdefault("pricing", tool.get("pricing_type", "Unknown") or "Unknown")
    tool.setdefault("pricing_type", "unknown")
    tool.setdefault("rating", 0)
    tool.setdefault("website", "#")

    for key in (
        "platforms", "languages", "tags", "collections", "pros", "cons",
        "target_users", "system_requirements", "change_history", "price_history",
    ):
        value = tool.get(key)
        tool[key] = value if isinstance(value, list) else []

    for key in ("open_source", "offline", "ai_powered", "editor_choice"):
        tool[key] = bool(tool.get(key, False))

    pricing_details = tool.get("pricing_details")
    if not isinstance(pricing_details, dict):
        pricing_details = {}
    tool["pricing_details"] = {
        "model": pricing_details.get("model") or tool.get("pricing") or "Unknown",
        "note": pricing_details.get("note") or "Pricing details have not been reviewed yet. Confirm current plans on the official website.",
    }

    verification = tool.get("verification")
    if not isinstance(verification, dict):
        verification = {}
    tool["verification"] = {
        "status": verification.get("status") or "Unverified",
        "date": verification.get("date"),
        "note": verification.get("note") or "This listing has not completed an editorial verification review yet.",
    }

    freshness = tool.get("freshness")
    tool["freshness"] = freshness if isinstance(freshness, dict) else {}
    return tool


def decode_payload(row):
    return normalize_tool_payload(json.loads(row["payload_json"]))
