"""Conservative accuracy audit for catalog-worker review records."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from tool_schema import validate_tool


SUPPORTED = {"verified", "provisionally_supported"}


def audit_record(record: dict[str, Any], *, catalog_slugs: set[str] | None = None, catalog_domains: set[str] | None = None) -> dict[str, Any]:
    errors, warnings = validate_tool(record, 0), []
    metadata = record.get("research_metadata") or {}
    claims = metadata.get("claim_review") or {}
    sources = record.get("source_references") or []
    source_types = {str(source.get("type") or "") for source in sources}
    slug = str(record.get("slug") or "").casefold()
    domain = (urlparse(str(record.get("website") or "")).hostname or "").casefold().removeprefix("www.")
    if catalog_slugs and slug in catalog_slugs:
        errors.append("Duplicate slug already exists in public catalog")
    if catalog_domains and domain in catalog_domains:
        errors.append("Duplicate official domain already exists in public catalog")
    for source in sources:
        url = str(source.get("url") or "")
        if urlparse(url).scheme != "https" or not urlparse(url).hostname:
            errors.append("Evidence source is not public HTTPS")
        if not source.get("claims"):
            warnings.append("Evidence source does not declare supported claims")
    for name, claim in claims.items():
        status = claim.get("status")
        declared = set(claim.get("source_types") or [])
        if status in SUPPORTED and not declared:
            errors.append(f"Claim '{name}' is supported without a source type")
        missing_types = declared - source_types
        if status in SUPPORTED and missing_types:
            errors.append(f"Claim '{name}' references absent source types: {sorted(missing_types)}")
        supporting_sources = [source for source in sources if source.get("type") in declared and name in (source.get("claims") or [])]
        if status in SUPPORTED and declared and not supporting_sources:
            errors.append(f"Claim '{name}' is not listed by its declared evidence source")
    if record.get("features") and claims.get("features", {}).get("status") not in SUPPORTED:
        errors.append("Feature values exist without a supported feature claim")
    evidence = metadata.get("official_evidence") or {}
    if evidence.get("archived") or evidence.get("disabled"):
        errors.append("Official repository is archived or disabled")
    logo = metadata.get("logo_review") or {}
    if logo.get("status") == "verified_official_asset":
        selected = logo.get("selected_candidate") or {}
        if not selected.get("checksum") or selected.get("status") not in {"verified_official_asset", "quarantined_needs_human_review"}:
            errors.append("Verified logo status has no inspected asset checksum")
    if record.get("publication_status") == "published":
        errors.append("Worker record is not allowed to publish directly")
    score = max(0, 100 - len(errors) * 20 - len(warnings) * 5)
    return {"slug": slug, "score": score, "passed": not errors, "errors": errors, "warnings": warnings}


def audit_records(records: list[dict[str, Any]], catalog: list[dict[str, Any]]) -> dict[str, Any]:
    slugs = {str(item.get("slug") or "").casefold() for item in catalog}
    domains = {(urlparse(str(item.get("website") or "")).hostname or "").casefold().removeprefix("www.") for item in catalog}
    seen_slugs: set[str] = set()
    seen_domains: set[str] = set()
    results = []
    for record in records:
        result = audit_record(record, catalog_slugs=slugs, catalog_domains=domains)
        slug = str(record.get("slug") or "").casefold()
        domain = (urlparse(str(record.get("website") or "")).hostname or "").casefold().removeprefix("www.")
        if slug in seen_slugs:
            result["errors"].append("Duplicate slug inside worker records")
        if domain and domain in seen_domains:
            result["errors"].append("Duplicate domain inside worker records")
        result["passed"] = not result["errors"]
        result["score"] = max(0, 100 - len(result["errors"]) * 20 - len(result["warnings"]) * 5)
        seen_slugs.add(slug)
        if domain:
            seen_domains.add(domain)
        results.append(result)
    passed = sum(1 for result in results if result["passed"])
    return {
        "total": len(results), "passed": passed, "failed": len(results) - passed,
        "average_score": round(sum(result["score"] for result in results) / len(results), 2) if results else 100,
        "publication_allowed": False, "results": results,
    }
