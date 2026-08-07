"""Build AtlasFind-compatible review records from discovery candidates.

These records are deliberately not publishable.  They use the public catalog
shape so an editor can promote a reviewed record without a second migration,
while ``research_metadata`` keeps provisional and missing claims explicit.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


CLAIM_NAMES = (
    "identity",
    "purpose",
    "description",
    "features",
    "category",
    "subcategory",
    "pricing",
    "platforms",
    "open_source",
    "avatar",
)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _domain(url: str) -> str:
    return urlparse(url).netloc.casefold().removeprefix("www.")


def _initials(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name)
    return "".join(word[0] for word in words[:2]).upper() or "AF"


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _unique_text(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean_text(value)
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return output


def _source(label: str, url: str, source_type: str, checked_at: str, claims: list[str]) -> dict[str, Any]:
    return {
        "label": label,
        "url": url,
        "type": source_type,
        "checked_at": checked_at,
        "domain": _domain(url),
        "claims": claims,
    }


def _claim(status: str, source_types: list[str], note: str) -> dict[str, Any]:
    return {"status": status, "source_types": source_types, "note": note}


def next_available_ids(catalog: list[dict[str, Any]], count: int) -> list[int]:
    """Return deterministic, collision-free IDs following the catalog maximum."""
    maximum = max((item.get("id", 0) for item in catalog if isinstance(item.get("id"), int)), default=0)
    return list(range(maximum + 1, maximum + count + 1))


def build_review_record(candidate: dict[str, Any], tool_id: int, *, today: date | None = None) -> dict[str, Any]:
    """Convert one discovery item into a schema-complete pending record."""
    checked = today or date.today()
    checked_at = checked.isoformat()
    name = _clean_text(candidate.get("name"))
    slug = _slugify(candidate.get("slug") or name)
    description = _clean_text(candidate.get("description_source_text"))
    website = _clean_text(candidate.get("official_url") or candidate.get("repository_url"))
    repository_url = _clean_text(candidate.get("repository_url"))
    category = _clean_text(candidate.get("category_suggestion")) or "Other"
    subcategory = _clean_text(candidate.get("subcategory_suggestion")) or "Needs Classification"
    topics = _unique_text(candidate.get("topics") or [])
    evidence = candidate.get("official_evidence") if isinstance(candidate.get("official_evidence"), dict) else {}
    evidence_features = [item.get("text") for item in evidence.get("features", []) if isinstance(item, dict)]
    evidence_platforms = _unique_text(evidence.get("platforms") or [])
    purpose = _clean_text(evidence.get("purpose"))
    license_id = _clean_text(candidate.get("license"))
    open_source = bool(license_id and license_id.upper() not in {"NOASSERTION", "OTHER"})

    if not name or not slug or not website.startswith("https://") or len(description) < 20:
        raise ValueError("candidate requires a name, HTTPS source URL and meaningful source description")

    primary_type = "official-repository" if repository_url and repository_url.rstrip("/") == website.rstrip("/") else "official-homepage"
    primary_claims = ["identity", "website", "description"]
    if primary_type == "official-repository" and open_source:
        primary_claims.append("open_source")
    sources = [_source(f"{name} discovery source", website, primary_type, checked_at, primary_claims)]
    if repository_url.startswith("https://") and repository_url.rstrip("/") != website.rstrip("/"):
        repo_claims = ["identity", "description"] + (["open_source"] if open_source else [])
        sources.append(_source(f"{name} official repository", repository_url, "official-repository", checked_at, repo_claims))
    readme_url = _clean_text(evidence.get("readme_source_url"))
    if readme_url.startswith("https://"):
        claims_from_readme = [name for name, value in (("purpose", purpose), ("features", evidence_features),
                                                       ("platforms", evidence_platforms), ("pricing", evidence.get("pricing"))) if value]
        sources.append(_source(f"{name} official documentation", readme_url, "official-documentation", checked_at, claims_from_readme))

    claim_review = {
        "identity": _claim("provisionally_supported", [sources[0]["type"]], "A human must confirm that the source belongs to the product."),
        "purpose": _claim("provisionally_supported" if purpose else "needs_enrichment", ["official-documentation"] if purpose else [], "Extracted from the official README; human confirmation is required." if purpose else "A detailed purpose statement has not been researched yet."),
        "description": _claim("provisionally_supported", [sources[0]["type"]], "Currently based on source-provided summary text."),
        "features": _claim("provisionally_supported" if evidence_features else "missing", ["official-documentation"] if evidence_features else [], "Feature bullets were extracted from the official README and require human confirmation." if evidence_features else "Feature claims require official product or documentation sources."),
        "category": _claim("suggested", [], "Discovery query supplied this category; editorial confirmation is required."),
        "subcategory": _claim("suggested", [], "Discovery query supplied this subcategory; editorial confirmation is required."),
        "pricing": _claim("provisionally_supported" if evidence.get("pricing") else "missing", ["official-documentation"] if evidence.get("pricing") else [], "README contains an explicit free/open-source statement." if evidence.get("pricing") else "No pricing claim is made until an official pricing source is checked."),
        "platforms": _claim("provisionally_supported" if evidence_platforms else "missing", ["official-documentation"] if evidence_platforms else [], "Platform names were found in an official installation/download section." if evidence_platforms else "No platform claim is made until official downloads or documentation are checked."),
        "open_source": _claim("provisionally_supported" if open_source and "official-repository" in {source["type"] for source in sources} else "unknown", ["official-repository"] if open_source and "official-repository" in {source["type"] for source in sources} else [],
                              f"Repository reports license {license_id}." if open_source else "A usable license was not confirmed."),
        "avatar": _claim("missing", [], "GitHub preview images are not accepted as an official product avatar."),
    }

    # Required catalog values below are explicit review placeholders, never facts.
    pricing_evidence = evidence.get("pricing") if isinstance(evidence.get("pricing"), dict) else {}
    pricing = pricing_evidence.get("model") or ("Free (unverified)" if open_source else "Pricing pending review")
    pricing_type = pricing_evidence.get("pricing_type") or ("free" if open_source else "freemium")
    fallback = f"/static/icons/generated/{slug}.svg"
    tags = _unique_text([subcategory, category, *topics[:3]]) or ["Software"]
    return {
        "id": tool_id,
        "slug": slug,
        "name": name,
        "description": description,
        "category": category,
        "tags": tags,
        "pricing": pricing,
        "pricing_type": pricing_type,
        "rating": 0,
        "rating_source": "not-rated",
        "website": website,
        "platforms": evidence_platforms or ["Web"],
        "open_source": open_source,
        "offline": False,
        "ai_powered": False,
        "minimum_ram_gb": None,
        "system_level": "unknown",
        "languages": [],
        "pros": ["An official-source review record has been created"],
        "cons": ["Features, pricing, platforms and avatar still require verification"],
        "target_users": ["Users comparing software in this category"],
        "system_requirements": ["Check official documentation before publication"],
        "pricing_details": {"model": pricing, "note": "Review placeholder; not eligible for public display."},
        "verification": {"status": "pending", "date": checked_at, "note": "Discovery completed; detailed official-source review is still required."},
        "subcategory": subcategory,
        "popularity_score": min(100, max(0, int(candidate.get("stars") or 0) // 1000)),
        "editor_choice": False,
        "date_added": checked_at,
        "collections": ["open-source"] if open_source else [],
        "freshness": {"last_checked_at": checked_at, "last_updated_at": checked_at,
                      "next_check_at": (checked + timedelta(days=30)).isoformat(), "status": "unknown"},
        "change_history": [{"date": checked_at, "type": "data-review", "summary": "Created as a non-public catalog worker review record.", "changes": []}],
        "price_history": [],
        "quality_status": "unverified",
        "quality_review": {"scope": "automated-discovery", "reviewed_at": checked_at, "note": "Automation only; human verification is required before publication."},
        "icon_url": fallback,
        "icon_source": "local-generated",
        "icon_alt": f"{name} temporary review icon",
        "icon_fallback_url": fallback,
        "icon_meta": {"fallback": "local-svg-monogram", "initials": _initials(name), "domain": _domain(website), "lazy_load": True, "review_status": "needs-official-asset"},
        "aliases": [],
        "publication_status": "research_only",
        "source_references": sources,
        "features": _unique_text(evidence_features),
        "purpose": purpose,
        "research_metadata": {
            "schema_version": 1,
            "record_kind": "atlasfind_catalog_review",
            "discovered_at": candidate.get("discovered_at"),
            "discovery_query": candidate.get("discovery_query"),
            "repository": candidate.get("repository"),
            "stars": int(candidate.get("stars") or 0),
            "license": license_id or None,
            "official_evidence": evidence,
            "logo_review": {
                "status": "not_started",
                "candidates": [],
                "attempts": [],
                "requires_human_selection": True,
                "selected_candidate": None,
            },
            "claim_review": claim_review,
            "required_claims": list(CLAIM_NAMES),
            "missing_claims": [name for name, review in claim_review.items() if review["status"] in {"missing", "needs_enrichment", "unknown"}],
            "publication_blockers": ["human_review_required", "official_avatar_required", "claim_verification_incomplete"],
        },
    }


def build_review_records(candidates: list[dict[str, Any]], catalog: list[dict[str, Any]], *, today: date | None = None) -> list[dict[str, Any]]:
    """Build records while skipping catalog/candidate slug collisions deterministically."""
    known = {_slugify(item.get("slug", "")) for item in catalog}
    accepted: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        slug = _slugify(candidate.get("slug") or candidate.get("name", ""))
        if not slug or slug in known or slug in seen:
            continue
        seen.add(slug)
        accepted.append(candidate)
    ids = next_available_ids(catalog, len(accepted))
    return [build_review_record(candidate, tool_id, today=today) for candidate, tool_id in zip(accepted, ids)]
