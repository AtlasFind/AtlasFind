"""AtlasFind tool dataset validation helpers for v0.5.1."""

from __future__ import annotations

from typing import Any
from datetime import date

ALLOWED_PRICING_TYPES = {"free", "freemium", "paid"}
ALLOWED_PLATFORMS = {"windows", "macos", "linux", "android", "ios", "ipados", "web"}
ALLOWED_SYSTEM_LEVELS = {"light", "medium", "heavy", "unknown"}
ALLOWED_LANGUAGE_CODES = {"en", "tr"}
ALLOWED_COLLECTIONS = {"free-tools", "open-source", "low-end-pc", "students", "editor-choice"}

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
    "subcategory": str,
    "popularity_score": int,
    "editor_choice": bool,
    "date_added": str,
    "collections": list,
    "freshness": dict,
    "change_history": list,
    "price_history": list,
}

REQUIRED_PRICING_FIELDS = {"model": str, "note": str}
REQUIRED_VERIFICATION_FIELDS = {"status": str, "date": str, "note": str}

ALLOWED_FRESHNESS_STATUSES = {"current", "review-due", "outdated", "unknown"}
ALLOWED_CHANGE_TYPES = {"data-review", "pricing-change", "feature-added", "feature-removed", "platform-change", "status-change"}

def _valid_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True

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

    for field in ("slug", "name", "description", "category", "pricing", "pricing_type", "rating_source", "website", "system_level", "subcategory", "date_added"):
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


    popularity_score = tool.get("popularity_score")
    if isinstance(popularity_score, bool) or not isinstance(popularity_score, int) or not 0 <= popularity_score <= 100:
        errors.append(f"{label}.popularity_score: must be an integer between 0 and 100")

    collections = tool.get("collections")
    if isinstance(collections, list):
        if not all(_is_non_empty_text(item) for item in collections):
            errors.append(f"{label}.collections: every item must be non-empty text")
        invalid_collections = _normalized_values(collections) - ALLOWED_COLLECTIONS
        if invalid_collections:
            errors.append(f"{label}.collections: unsupported values {sorted(invalid_collections)}")

    date_added = tool.get("date_added")
    if _is_non_empty_text(date_added) and not __import__("re").fullmatch(r"\d{4}-\d{2}-\d{2}", date_added):
        errors.append(f"{label}.date_added: must use YYYY-MM-DD format")

    freshness = tool.get("freshness")
    if isinstance(freshness, dict):
        for field in ("last_checked_at", "last_updated_at", "next_check_at"):
            if not _valid_iso_date(freshness.get(field)):
                errors.append(f"{label}.freshness.{field}: must use a valid YYYY-MM-DD date")
        status = freshness.get("status")
        if status not in ALLOWED_FRESHNESS_STATUSES:
            errors.append(f"{label}.freshness.status: unsupported value")
        if _valid_iso_date(freshness.get("last_checked_at")) and _valid_iso_date(freshness.get("next_check_at")):
            if date.fromisoformat(freshness["next_check_at"]) < date.fromisoformat(freshness["last_checked_at"]):
                errors.append(f"{label}.freshness.next_check_at: cannot precede last_checked_at")

    history = tool.get("change_history")
    if isinstance(history, list):
        previous_date = None
        for history_index, item in enumerate(history):
            item_label = f"{label}.change_history[{history_index}]"
            if not isinstance(item, dict):
                errors.append(f"{item_label}: must be an object")
                continue
            if not _valid_iso_date(item.get("date")):
                errors.append(f"{item_label}.date: must use YYYY-MM-DD")
            if item.get("type") not in ALLOWED_CHANGE_TYPES:
                errors.append(f"{item_label}.type: unsupported change type")
            if not _is_non_empty_text(item.get("summary")):
                errors.append(f"{item_label}.summary: required non-empty text")
            if not isinstance(item.get("changes"), list):
                errors.append(f"{item_label}.changes: must be a list")
            if _valid_iso_date(item.get("date")):
                current_date = date.fromisoformat(item["date"])
                if previous_date is not None and current_date > previous_date:
                    errors.append(f"{label}.change_history: records must be newest first")
                previous_date = current_date

    price_history = tool.get("price_history")
    if isinstance(price_history, list):
        for price_index, item in enumerate(price_history):
            item_label = f"{label}.price_history[{price_index}]"
            if not isinstance(item, dict):
                errors.append(f"{item_label}: must be an object")
                continue
            if not _valid_iso_date(item.get("date")):
                errors.append(f"{item_label}.date: must use YYYY-MM-DD")
            for field in ("old_value", "new_value", "note"):
                if not _is_non_empty_text(item.get(field)):
                    errors.append(f"{item_label}.{field}: required non-empty text")

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
