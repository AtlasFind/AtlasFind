"""AtlasFind tool dataset validation helpers.

Keeps every current and future tool entry aligned with the professional
v0.1.2 detail-page data contract without adding third-party dependencies.
"""

from __future__ import annotations

from typing import Any

REQUIRED_FIELDS: dict[str, type | tuple[type, ...]] = {
    "id": int,
    "slug": str,
    "name": str,
    "description": str,
    "category": str,
    "tags": list,
    "pricing": str,
    "rating": (int, float),
    "rating_source": str,
    "website": str,
    "platforms": list,
    "open_source": bool,
    "offline": bool,
    "ai_powered": bool,
    "pros": list,
    "cons": list,
    "target_users": list,
    "system_requirements": list,
    "pricing_details": dict,
    "verification": dict,
}

REQUIRED_PRICING_FIELDS = {"model": str, "note": str}
REQUIRED_VERIFICATION_FIELDS = {"status": str, "date": str, "note": str}
NON_EMPTY_LIST_FIELDS = {
    "tags",
    "platforms",
    "pros",
    "cons",
    "target_users",
    "system_requirements",
}


def _is_non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_tool(tool: Any, index: int) -> list[str]:
    """Return human-readable validation errors for one tool entry."""
    errors: list[str] = []
    label = f"tools[{index}]"

    if not isinstance(tool, dict):
        return [f"{label}: entry must be a JSON object"]

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in tool:
            errors.append(f"{label}: missing required field '{field}'")
            continue
        if not isinstance(tool[field], expected_type):
            errors.append(f"{label}.{field}: invalid value type")

    for field in ("slug", "name", "description", "category", "pricing", "rating_source", "website"):
        if field in tool and not _is_non_empty_text(tool[field]):
            errors.append(f"{label}.{field}: value cannot be empty")

    for field in NON_EMPTY_LIST_FIELDS:
        value = tool.get(field)
        if isinstance(value, list):
            if not value:
                errors.append(f"{label}.{field}: list cannot be empty")
            elif not all(_is_non_empty_text(item) for item in value):
                errors.append(f"{label}.{field}: every item must be non-empty text")

    pricing_details = tool.get("pricing_details")
    if isinstance(pricing_details, dict):
        for field, expected_type in REQUIRED_PRICING_FIELDS.items():
            value = pricing_details.get(field)
            if not isinstance(value, expected_type) or not value.strip():
                errors.append(f"{label}.pricing_details.{field}: required non-empty text")

    verification = tool.get("verification")
    if isinstance(verification, dict):
        for field, expected_type in REQUIRED_VERIFICATION_FIELDS.items():
            value = verification.get(field)
            if not isinstance(value, expected_type) or not value.strip():
                errors.append(f"{label}.verification.{field}: required non-empty text")

    rating = tool.get("rating")
    if isinstance(rating, (int, float)) and not 0 <= rating <= 5:
        errors.append(f"{label}.rating: must be between 0 and 5")

    return errors


def validate_tools(tools: Any) -> list[str]:
    """Validate the complete dataset, including unique IDs and slugs."""
    if not isinstance(tools, list):
        return ["Dataset root must be a JSON array"]

    errors: list[str] = []
    ids: set[int] = set()
    slugs: set[str] = set()

    for index, tool in enumerate(tools):
        errors.extend(validate_tool(tool, index))
        if not isinstance(tool, dict):
            continue

        tool_id = tool.get("id")
        if isinstance(tool_id, int):
            if tool_id in ids:
                errors.append(f"tools[{index}].id: duplicate ID {tool_id}")
            ids.add(tool_id)

        slug = tool.get("slug")
        if _is_non_empty_text(slug):
            normalized_slug = slug.strip().lower()
            if normalized_slug in slugs:
                errors.append(f"tools[{index}].slug: duplicate slug '{slug}'")
            slugs.add(normalized_slug)

    return errors
