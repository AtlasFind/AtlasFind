"""Freshness and change-history helpers for AtlasFind v0.4.1."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

CURRENT_MAX_AGE_DAYS = 90
OUTDATED_AGE_DAYS = 180
DEFAULT_CHECK_INTERVAL_DAYS = 90
ALLOWED_FRESHNESS_STATUSES = {"current", "review-due", "outdated", "unknown"}
ALLOWED_CHANGE_TYPES = {
    "data-review",
    "pricing-change",
    "feature-added",
    "feature-removed",
    "platform-change",
    "status-change",
}


def parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def get_next_check_date(last_checked_at: Any, interval_days: int = DEFAULT_CHECK_INTERVAL_DAYS) -> str | None:
    parsed = parse_iso_date(last_checked_at)
    if parsed is None:
        return None
    return (parsed + timedelta(days=interval_days)).isoformat()


def calculate_freshness_status(last_checked_at: Any, *, today: date | None = None) -> str:
    parsed = parse_iso_date(last_checked_at)
    if parsed is None:
        return "unknown"
    reference = today or date.today()
    age = (reference - parsed).days
    if age < 0:
        return "unknown"
    if age <= CURRENT_MAX_AGE_DAYS:
        return "current"
    if age <= OUTDATED_AGE_DAYS:
        return "review-due"
    return "outdated"


def is_content_outdated(updated_at: Any, *, today: date | None = None) -> bool:
    return calculate_freshness_status(updated_at, today=today) == "outdated"


def content_freshness(updated_at: Any, *, today: date | None = None) -> dict[str, str | bool | None]:
    status = calculate_freshness_status(updated_at, today=today)
    labels = {
        "current": "Updated recently",
        "review-due": "Review recommended",
        "outdated": "Potentially outdated",
        "unknown": "Update status unknown",
    }
    return {
        "status": status,
        "label": labels[status],
        "is_outdated": status == "outdated",
        "next_check_at": get_next_check_date(updated_at),
    }


def normalize_change_history(history: Any) -> list[dict[str, Any]]:
    if not isinstance(history, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        changes = item.get("changes")
        normalized.append(
            {
                "date": item.get("date") if parse_iso_date(item.get("date")) else None,
                "type": item.get("type") if item.get("type") in ALLOWED_CHANGE_TYPES else "data-review",
                "summary": str(item.get("summary") or "Update recorded."),
                "changes": changes if isinstance(changes, list) else [],
            }
        )
    normalized.sort(key=lambda item: item.get("date") or "", reverse=True)
    return normalized


def tool_freshness(tool: dict[str, Any], *, today: date | None = None) -> dict[str, Any]:
    raw = tool.get("freshness") if isinstance(tool.get("freshness"), dict) else {}
    verification = tool.get("verification") if isinstance(tool.get("verification"), dict) else {}
    last_checked = raw.get("last_checked_at") or verification.get("date")
    last_updated = raw.get("last_updated_at") or last_checked
    next_check = raw.get("next_check_at") or get_next_check_date(last_checked)
    derived_status = calculate_freshness_status(last_checked, today=today)
    labels = {
        "current": "Current",
        "review-due": "Review due",
        "outdated": "Outdated",
        "unknown": "Unknown",
    }
    return {
        "last_checked_at": last_checked,
        "last_updated_at": last_updated,
        "next_check_at": next_check,
        "status": derived_status,
        "label": labels[derived_status],
        "is_outdated": derived_status == "outdated",
        "history": normalize_change_history(tool.get("change_history")),
        "price_history": tool.get("price_history") if isinstance(tool.get("price_history"), list) else [],
    }
