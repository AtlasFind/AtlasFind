"""Persistent, non-destructive editorial decisions for catalog-worker records."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REVIEWS_PATH = ROOT / "data/research/catalog-worker-reviews.json"
EDITABLE_FIELDS = {"name", "description", "purpose", "features", "category", "subcategory", "website", "pricing", "platforms"}
DECISIONS = {"pending", "changes_requested", "rejected", "approved_for_export"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_reviews(path: Path = REVIEWS_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "updated_at": now(), "records": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    value.setdefault("version", 1)
    value.setdefault("records", {})
    return value


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.stem + "-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_review(slug: str, payload: dict[str, Any], *, path: Path = REVIEWS_PATH) -> dict[str, Any]:
    decision = str(payload.get("decision") or "pending")
    if decision not in DECISIONS:
        raise ValueError("Unsupported review decision")
    edits = payload.get("edits") or {}
    if not isinstance(edits, dict) or set(edits) - EDITABLE_FIELDS:
        raise ValueError("Review contains unsupported editable fields")
    if "features" in edits and (not isinstance(edits["features"], list) or not all(isinstance(x, str) and x.strip() for x in edits["features"])):
        raise ValueError("Features must be a list of non-empty text values")
    if "platforms" in edits and (not isinstance(edits["platforms"], list) or not all(isinstance(x, str) and x.strip() for x in edits["platforms"])):
        raise ValueError("Platforms must be a list of non-empty text values")
    reviews = load_reviews(path)
    record = {
        "slug": slug,
        "decision": decision,
        "note": " ".join(str(payload.get("note") or "").split()),
        "edits": edits,
        "reviewed_at": now(),
        "reviewed_by": "local_editor",
        "auto_publish_allowed": False,
    }
    reviews["records"][slug] = record
    reviews["updated_at"] = now()
    _atomic_write(path, reviews)
    return record


def merge_reviews(records: list[dict[str, Any]], reviews: dict[str, Any]) -> list[dict[str, Any]]:
    merged = []
    decisions = reviews.get("records", {})
    for source in records:
        record = dict(source)
        review = decisions.get(record.get("slug"), {})
        for field, value in review.get("edits", {}).items():
            record[field] = value
        record["editorial_review"] = review or {"decision": "pending", "edits": {}, "note": "", "auto_publish_allowed": False}
        merged.append(record)
    return merged


def export_readiness(record: dict[str, Any]) -> list[str]:
    """Return human-readable reasons why a record cannot enter an export bundle."""
    blockers: list[str] = []
    metadata = record.get("research_metadata") or {}
    missing = metadata.get("missing_claims") or []
    if missing:
        blockers.append("Missing verified claims: " + ", ".join(str(item) for item in missing))
    logo_review = metadata.get("logo_review") or {}
    if logo_review.get("status") != "verified_official_asset":
        blockers.append("Official avatar has not been selected and verified")
    if not record.get("source_references"):
        blockers.append("No official evidence source is recorded")
    for field in ("name", "description", "purpose", "category", "subcategory", "website"):
        if not str(record.get(field) or "").strip():
            blockers.append(f"Required field is empty: {field}")
    if not record.get("features"):
        blockers.append("At least one verified feature is required")
    return blockers
