"""Transparent AtlasFind rating calculations. No template-side arithmetic."""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_PATH = BASE_DIR / "config" / "rating_profiles.json"
CRITERIA = ("features", "ease_of_use", "value", "performance", "security", "platforms", "support", "transparency")

@dataclass(frozen=True)
class RatingResult:
    overall_score: float | None
    raw_score: float | None
    coverage: float
    publishable: bool
    confidence_score: int
    confidence_level: str
    errors: tuple[str, ...]


def load_rating_config() -> dict[str, Any]:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def profile_weights(profile: str) -> dict[str, float]:
    config = load_rating_config()
    profiles = config["profiles"]
    if profile not in profiles:
        raise ValueError(f"Unknown rating profile: {profile}")
    weights = {key: float(value) for key, value in profiles[profile].items()}
    if set(weights) != set(CRITERIA):
        raise ValueError(f"Profile {profile} must define exactly: {', '.join(CRITERIA)}")
    if abs(sum(weights.values()) - 1.0) > 0.000001:
        raise ValueError(f"Profile {profile} weights must total 1.0")
    return weights


def display_score(value: float | None) -> str | None:
    if value is None:
        return None
    return str(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def confidence_level(score: int) -> str:
    if score >= 90: return "very_high"
    if score >= 75: return "high"
    if score >= 60: return "medium"
    if score >= 40: return "low"
    return "insufficient"


def calculate_confidence(rating: dict[str, Any]) -> int:
    criteria = rating.get("criteria") or {}
    sources = rating.get("sources") or []
    verified = [item for item in criteria.values() if item.get("status") == "verified"]
    official = sum(1 for source in sources if source.get("type", "").startswith("official_"))
    current = sum(1 for source in sources if source.get("status", "active") == "active")
    evidence_ratio = sum(1 for item in verified if item.get("evidence_ids")) / max(len(CRITERIA), 1)
    coverage = sum(float(item.get("weight", 0)) for item in verified)
    editor_verified = 1.0 if rating.get("reviewed_by") else 0.0
    approved = 1.0 if rating.get("approved_by") else 0.0
    source_ratio = min(official / 3, 1.0)
    freshness_ratio = min(current / 3, 1.0)
    score = (source_ratio * 25) + (freshness_ratio * 20) + (editor_verified * 10) + (approved * 10) + (evidence_ratio * 15) + (coverage * 20)
    return max(0, min(100, round(score)))


def evaluate_rating(rating: dict[str, Any], category: str = "") -> RatingResult:
    errors: list[str] = []
    profile = str(rating.get("category_profile") or "default")
    try:
        weights = profile_weights(profile)
    except ValueError as exc:
        return RatingResult(None, None, 0.0, False, 0, "insufficient", (str(exc),))
    criteria = rating.get("criteria") or {}
    total = 0.0
    coverage = 0.0
    for key in CRITERIA:
        item = criteria.get(key)
        if not item or item.get("status") != "verified":
            continue
        score = item.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 10:
            errors.append(f"{key}: score must be between 0 and 10")
            continue
        reason_tr = str(item.get("reason_tr") or "").strip()
        reason_en = str(item.get("reason_en") or "").strip()
        if not reason_tr or not reason_en:
            errors.append(f"{key}: bilingual reason is required")
        if not item.get("evidence_ids"):
            errors.append(f"{key}: evidence is required")
        weight = weights[key]
        total += float(score) * weight
        coverage += weight
    critical = load_rating_config().get("critical_criteria", {}).get(profile, [])
    for key in critical:
        if (criteria.get(key) or {}).get("status") != "verified":
            errors.append(f"{key}: critical criterion is missing")
    minimum = float(load_rating_config().get("minimum_coverage", 0.8))
    confidence = calculate_confidence({**rating, "criteria": criteria})
    publishable = coverage >= minimum and not errors and bool(rating.get("reviewed_by")) and bool(rating.get("approved_by")) and rating.get("reviewed_by") != rating.get("approved_by")
    if rating.get("reviewed_by") and rating.get("reviewed_by") == rating.get("approved_by"):
        errors.append("reviewer cannot approve their own rating")
        publishable = False
    raw = total if coverage else None
    overall = raw if publishable else None
    return RatingResult(overall, raw, coverage, publishable, confidence, confidence_level(confidence), tuple(errors))


def enrich_tool_rating(tool: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(tool)
    rating = dict(enriched.get("rating_v103") or {})
    result = evaluate_rating(rating, str(enriched.get("category") or "")) if rating else RatingResult(None, None, 0, False, 0, "insufficient", ())
    rating["calculated_score"] = result.raw_score
    rating["overall_score"] = result.overall_score
    rating["display_score"] = display_score(result.overall_score)
    rating["coverage"] = round(result.coverage * 100, 1)
    rating["publishable"] = result.publishable
    rating["confidence_score"] = result.confidence_score
    rating["confidence_level"] = result.confidence_level
    rating["validation_errors"] = list(result.errors)
    enriched["rating_v103"] = rating
    enriched["rating"] = (result.overall_score / 2) if result.overall_score is not None else 0
    enriched["rating_source"] = "atlasfind_v103" if result.publishable else "not-rated"
    return enriched


def bayesian_user_score(vote_sum: float, vote_count: int, global_mean: float = 7.0, minimum_votes: int = 10) -> float | None:
    if vote_count <= 0:
        return None
    return ((vote_count * (vote_sum / vote_count)) + (minimum_votes * global_mean)) / (vote_count + minimum_votes)
