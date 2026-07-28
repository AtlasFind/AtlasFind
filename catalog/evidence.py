"""Evidence and publication quality rules for AtlasFind v1.0.2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

ALLOWED_SOURCE_TYPES = {
    "official-homepage",
    "official-pricing",
    "official-documentation",
    "official-support",
    "official-legal",
    "official-security",
    "official-company",
    "official-store",
    "official-repository",
}

REQUIRED_PUBLISHED_CLAIMS = {
    "identity",
    "website",
    "description",
    "category",
    "platforms",
    "pricing",
}

MAX_EVIDENCE_AGE_DAYS = 180


@dataclass(frozen=True)
class EvidenceIssue:
    code: str
    message: str
    severity: str = "error"


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def audit_evidence(tool: dict, *, today: date | None = None) -> list[EvidenceIssue]:
    """Return evidence issues without mutating a catalog record."""
    today = today or date.today()
    issues: list[EvidenceIssue] = []
    sources = tool.get("source_references", [])
    if not isinstance(sources, list) or not sources:
        return [EvidenceIssue("sources.missing", "No source references are attached")]

    covered_claims: set[str] = set()
    official_domains: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            issues.append(EvidenceIssue("source.invalid", f"Source #{index + 1} must be an object"))
            continue
        source_type = source.get("type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            issues.append(EvidenceIssue("source.type", f"Source #{index + 1} has unsupported type {source_type!r}"))
        claims = source.get("claims", [])
        if not isinstance(claims, list) or not all(isinstance(item, str) and item for item in claims):
            issues.append(EvidenceIssue("source.claims", f"Source #{index + 1} must declare verified claims"))
        else:
            covered_claims.update(claims)
        checked_at = _parse_date(source.get("checked_at"))
        if checked_at is None:
            issues.append(EvidenceIssue("source.date", f"Source #{index + 1} has an invalid checked_at date"))
        elif today - checked_at > timedelta(days=MAX_EVIDENCE_AGE_DAYS):
            issues.append(EvidenceIssue("source.stale", f"Source #{index + 1} is older than {MAX_EVIDENCE_AGE_DAYS} days", "warning"))
        domain = source.get("domain")
        if isinstance(domain, str) and domain.strip():
            official_domains.add(domain.strip().casefold())

    missing_claims = sorted(REQUIRED_PUBLISHED_CLAIMS - covered_claims)
    if missing_claims:
        issues.append(EvidenceIssue("claims.missing", "Missing evidence for: " + ", ".join(missing_claims)))
    if not official_domains:
        issues.append(EvidenceIssue("source.domain", "No official source domain is recorded"))
    return issues


def publication_ready(tool: dict) -> tuple[bool, list[EvidenceIssue]]:
    """Return whether a record satisfies the strict public publication gate."""
    issues = audit_evidence(tool)
    status = tool.get("verification", {}).get("status")
    if status != "verified":
        issues.append(EvidenceIssue("verification.status", "Verification status must be 'verified'"))
    if tool.get("publication_status") != "published":
        issues.append(EvidenceIssue("publication.status", "Publication status must be 'published'"))
    blocking = [issue for issue in issues if issue.severity == "error"]
    return not blocking, issues
