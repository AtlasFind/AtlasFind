import json


def parse_json_payload(raw_text):
    try:
        value = json.loads(raw_text or "{}")
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON: line {exc.lineno}, column {exc.colno}: {exc.msg}"
    if not isinstance(value, dict):
        return None, "Payload must be a JSON object."
    return value, None


def missing_tool_fields(payload):
    required = ["name", "slug", "description", "category", "pricing_type", "platforms", "languages"]
    return [field for field in required if payload.get(field) in (None, "", [])]


def missing_article_fields(payload):
    required = ["title", "slug", "description", "content_type", "sections"]
    return [field for field in required if payload.get(field) in (None, "", [])]
