"""Strict cross-file validation for the AtlasFind v1.0.2 catalog."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from typing import Any
from urllib.parse import urlparse

from tool_schema import validate_tool as validate_legacy_tool
from .constants import PUBLICATION_STATUSES, VERIFICATION_STATUSES
from .evidence import ALLOWED_SOURCE_TYPES

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CatalogValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        preview = "\n".join(f"- {error}" for error in errors[:100])
        suffix = f"\n... and {len(errors) - 100} more" if len(errors) > 100 else ""
        super().__init__(f"Catalog validation failed with {len(errors)} error(s):\n{preview}{suffix}")


def _is_url(value: Any, *, https_required: bool = True) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlparse(value.strip())
    if parsed.scheme not in ({"https"} if https_required else {"http", "https"}):
        return False
    return bool(parsed.netloc and "." in parsed.netloc)


def _is_iso_date(value: Any) -> bool:
    try:
        date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return False
    return True


def _validate_v102_fields(tool: dict, index: int) -> list[str]:
    label = f"tools[{index}]"
    errors: list[str] = []
    slug = tool.get("slug")
    if not isinstance(slug, str) or not SLUG_PATTERN.fullmatch(slug):
        errors.append(f"{label}.slug: must be lowercase kebab-case")

    status = tool.get("publication_status", "published")
    if status not in PUBLICATION_STATUSES:
        errors.append(f"{label}.publication_status: unsupported value {status!r}")

    verification = tool.get("verification")
    if isinstance(verification, dict):
        normalized = verification.get("status")
        legacy_map = {"catalog_seed": "pending", "editorial_seed": "partially_verified", "review_due": "pending"}
        normalized = legacy_map.get(str(normalized), normalized)
        if normalized not in VERIFICATION_STATUSES:
            errors.append(f"{label}.verification.status: unsupported value {verification.get('status')!r}")
        checked = verification.get("date")
        if checked and not _is_iso_date(checked):
            errors.append(f"{label}.verification.date: must use YYYY-MM-DD")

    website = tool.get("website")
    if not _is_url(website):
        errors.append(f"{label}.website: must be an absolute HTTPS URL")

    aliases = tool.get("aliases", [])
    if not isinstance(aliases, list) or not all(isinstance(alias, str) and alias.strip() for alias in aliases):
        errors.append(f"{label}.aliases: must be a list of non-empty strings")

    source_refs = tool.get("source_references", [])
    if not isinstance(source_refs, list):
        errors.append(f"{label}.source_references: must be a list")
    else:
        for source_index, source in enumerate(source_refs):
            source_label = f"{label}.source_references[{source_index}]"
            if not isinstance(source, dict):
                errors.append(f"{source_label}: must be an object")
                continue
            if not isinstance(source.get("label"), str) or not source["label"].strip():
                errors.append(f"{source_label}.label: required")
            if not _is_url(source.get("url")):
                errors.append(f"{source_label}.url: must be an absolute HTTPS URL")
            if not _is_iso_date(source.get("checked_at")):
                errors.append(f"{source_label}.checked_at: must use YYYY-MM-DD")
            source_type = source.get("type")
            if source_type not in ALLOWED_SOURCE_TYPES:
                errors.append(f"{source_label}.type: unsupported source type {source_type!r}")
            claims = source.get("claims")
            if not isinstance(claims, list) or not all(isinstance(claim, str) and claim.strip() for claim in claims):
                errors.append(f"{source_label}.claims: must be a list of non-empty strings")
            domain = source.get("domain")
            if not isinstance(domain, str) or not domain.strip():
                errors.append(f"{source_label}.domain: required")

    return errors


def validate_catalog(tools: Any) -> list[str]:
    if not isinstance(tools, list):
        return ["catalog: root must be a JSON array"]

    errors: list[str] = []
    for index, tool in enumerate(tools):
        errors.extend(validate_legacy_tool(tool, index))
        if isinstance(tool, dict):
            errors.extend(_validate_v102_fields(tool, index))

    ids = [tool.get("id") for tool in tools if isinstance(tool, dict)]
    slugs = [str(tool.get("slug", "")).casefold() for tool in tools if isinstance(tool, dict)]
    names = [str(tool.get("name", "")).strip().casefold() for tool in tools if isinstance(tool, dict)]
    websites = []
    for tool in tools:
        if isinstance(tool, dict):
            parsed = urlparse(str(tool.get("website", "")))
            normalized_url = str(tool.get("website", "")).strip().rstrip("/").casefold()
            if normalized_url:
                websites.append(normalized_url)

    for field, values in (("id", ids), ("slug", slugs), ("name", names), ("website URL", websites)):
        for value, count in Counter(values).items():
            if value not in (None, "") and count > 1:
                errors.append(f"catalog: duplicate {field} {value!r} appears {count} times")

    return errors
