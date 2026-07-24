"""AtlasFind tool dataset validation helpers for v0.1.3."""

from __future__ import annotations

from typing import Any

ALLOWED_PRICING_TYPES = {"free", "freemium", "paid"}
ALLOWED_PLATFORMS = {"windows", "macos", "linux", "android", "ios", "ipados", "web"}
ALLOWED_SYSTEM_LEVELS = {"light", "medium", "heavy", "unknown"}
ALLOWED_LANGUAGE_CODES = {"en", "tr"}

REQUIRED_FIELDS: dict[str, type | tuple[type, ...]] = {
    "id": int,
    "slug": str,
    "name": str,
    "description": str,
    "category": str,
    "tags": list,
    "pricing": str,
    "pricing_type": str,
    "rating": (int, float),
    "rating_source": str,
    "website": str,
    "platforms": list,
    "open_source": bool,
    "offline": bool,
    "ai_powered": bool,
    "minimum_ram_gb": (int, float, type(None)),
    "system_level": str,
    "languages": list,
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
    "tags", "platforms", "pros", "cons", "target_users", "system_requirements"
}


def _is_non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalized_values(values: list[Any]) -> set[str]:
    return {str(value).strip().lower() for value in values if _is_non_empty_text(value)}


def validate_tool(tool: Any, index: int) -> list[str]:
    errors: list[str] = []
    label = f"tools[{index}]"

    if not isinstance(tool, dict):
        return [f"{label}: entry must be a JSON object"]

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in tool:
            errors.append(f"{label}: missing required field '{field}'")
        elif not isinstance(tool[field], expected_type):
            errors.append(f"{label}.{field}: invalid value type")

    for field in ("slug", "name", "description", "category", "pricing", "pricing_type", "rating_source", "website", "system_level"):
        if field in tool and not _is_non_empty_text(tool[field]):
            errors.append(f"{label}.{field}: value cannot be empty")

    for field in NON_EMPTY_LIST_FIELDS:
        value = tool.get(field)
        if isinstance(value, list):
            if not value:
                errors.append(f"{label}.{field}: list cannot be empty")
            elif not all(_is_non_empty_text(item) for item in value):
                errors.append(f"{label}.{field}: every item must be non-empty text")

    languages = tool.get("languages")
    if isinstance(languages, list):
        if not all(_is_non_empty_text(item) for item in languages):
            errors.append(f"{label}.languages: every item must be non-empty text")
        invalid_languages = _normalized_values(languages) - ALLOWED_LANGUAGE_CODES
        if invalid_languages:
            errors.append(f"{label}.languages: unsupported codes {sorted(invalid_languages)}")

    pricing_type = str(tool.get("pricing_type", "")).strip().lower()
    if pricing_type and pricing_type not in ALLOWED_PRICING_TYPES:
        errors.append(f"{label}.pricing_type: must be one of {sorted(ALLOWED_PRICING_TYPES)}")

    platforms = tool.get("platforms")
    if isinstance(platforms, list):
        normalized = {value.replace(" ", "") for value in _normalized_values(platforms)}
        invalid_platforms = normalized - ALLOWED_PLATFORMS
        if invalid_platforms:
            errors.append(f"{label}.platforms: unsupported values {sorted(invalid_platforms)}")

    system_level = str(tool.get("system_level", "")).strip().lower()
    if system_level and system_level not in ALLOWED_SYSTEM_LEVELS:
        errors.append(f"{label}.system_level: must be one of {sorted(ALLOWED_SYSTEM_LEVELS)}")

    minimum_ram = tool.get("minimum_ram_gb")
    if isinstance(minimum_ram, bool) or (isinstance(minimum_ram, (int, float)) and minimum_ram <= 0):
        errors.append(f"{label}.minimum_ram_gb: must be a positive number or null")

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
