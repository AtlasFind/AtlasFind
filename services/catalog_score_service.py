"""Deterministic, evidence-based catalog scores for every public tool.

This score is deliberately separate from the manually reviewed editorial score.
It only evaluates facts available in the AtlasFind catalog and never pretends that
performance, security or ease of use were laboratory tested.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


VERSION = "1.0.0"


def _capped_ratio(value: int, target: int) -> float:
    return min(max(value, 0) / target, 1.0)


def _list(tool: dict[str, Any], key: str) -> list[Any]:
    value = tool.get(key)
    return value if isinstance(value, list) else []


def calculate_catalog_score(tool: dict[str, Any]) -> dict[str, Any]:
    """Return a transparent 0-10 score derived from catalog evidence only."""
    tags = _list(tool, "tags")
    pros = _list(tool, "pros")
    cons = _list(tool, "cons")
    targets = _list(tool, "target_users")
    requirements = _list(tool, "system_requirements")
    platforms = _list(tool, "platforms")
    languages = _list(tool, "languages")
    collections = _list(tool, "collections")

    # Breadth of documented capabilities and use cases (30%).
    capability = 10 * (
        0.35 * _capped_ratio(len(tags), 5)
        + 0.30 * _capped_ratio(len(pros), 4)
        + 0.20 * _capped_ratio(len(targets), 4)
        + 0.15 * _capped_ratio(len(requirements), 3)
    )

    # Reach across devices and languages (20%). Web counts as a platform too.
    accessibility = 10 * (
        0.72 * _capped_ratio(len(platforms), 5)
        + 0.28 * _capped_ratio(len(languages), 4)
    )

    pricing_type = str(tool.get("pricing_type") or tool.get("pricing") or "").lower()
    pricing_base = {"free": 1.0, "freemium": 0.82, "paid": 0.62}.get(pricing_type, 0.48)
    flexibility = sum((bool(tool.get("open_source")), bool(tool.get("offline")))) / 2
    value = 10 * (0.72 * pricing_base + 0.28 * flexibility)

    website = str(tool.get("website") or "")
    parsed = urlparse(website)
    valid_website = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    verification = tool.get("verification") if isinstance(tool.get("verification"), dict) else {}
    freshness = tool.get("freshness") if isinstance(tool.get("freshness"), dict) else {}
    verified = str(verification.get("status") or "").lower() == "verified"
    current = str(freshness.get("status") or "").lower() in {"current", "review-due"}
    balanced = bool(pros) and bool(cons)
    transparency = 10 * (0.30 * valid_website + 0.30 * verified + 0.25 * current + 0.15 * balanced)

    # How complete the catalog record is; this also controls confidence.
    required = (
        tool.get("description"), tool.get("category"), tool.get("pricing_details"),
        platforms, tags, pros, cons, targets, requirements, website,
        verification, freshness,
    )
    completeness = 10 * sum(bool(item) for item in required) / len(required)

    components = {
        "capability": round(capability, 1),
        "accessibility": round(accessibility, 1),
        "value": round(value, 1),
        "transparency": round(transparency, 1),
        "completeness": round(completeness, 1),
    }
    score = round(
        capability * 0.30
        + accessibility * 0.20
        + value * 0.20
        + transparency * 0.20
        + completeness * 0.10,
        1,
    )
    confidence = "high" if completeness >= 9 and verified and current else "medium" if completeness >= 7 else "low"
    return {
        "version": VERSION,
        "score": score,
        "display_score": f"{score:.1f}",
        "scale": 10,
        "automated": True,
        "confidence": confidence,
        "components": components,
        "signals": {
            "platform_count": len(platforms),
            "language_count": len(languages),
            "documented_advantage_count": len(pros),
            "documented_limitation_count": len(cons),
            "collection_count": len(collections),
        },
    }


def enrich_tool_catalog_score(tool: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(tool)
    catalog_score = calculate_catalog_score(enriched)
    enriched["catalog_score"] = catalog_score
    # Existing filters/sorts use a five-point compatibility value. A genuinely
    # published editor score still wins; otherwise use the automated score.
    editor_rating = enriched.get("rating_v103") or {}
    if not editor_rating.get("publishable"):
        enriched["rating"] = catalog_score["score"] / 2
        enriched["rating_source"] = "atlasfind_catalog_v1"
    return enriched
