import json
from pathlib import Path

from tool_schema import validate_tools


def validate_import_payload(value):
    tools = value.get("tools") if isinstance(value, dict) else value
    if not isinstance(tools, list):
        return None, ["Import must be a JSON array or an object containing a tools array."]
    errors = validate_tools(tools)
    return tools, errors


def safe_next_url(value):
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return None
