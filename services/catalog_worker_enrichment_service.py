"""Evidence-first enrichment helpers for AtlasFind catalog candidates."""

from __future__ import annotations

import base64
import json
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


PLATFORM_PATTERNS = {
    "Windows": r"\bwindows(?: 10| 11)?\b",
    "macOS": r"\b(?:macos|mac os|os x)\b",
    "Linux": r"\blinux\b",
    "Android": r"\bandroid\b",
    "iOS": r"\b(?:ios|iphone|ipad)\b",
    "Web": r"\b(?:web app|browser-based|in your browser)\b",
}
FEATURE_HEADINGS = {"features", "key features", "highlights", "capabilities", "what it does"}
INSTALL_HEADINGS = {"install", "installation", "downloads", "download", "requirements", "supported platforms"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_markdown(value: str) -> str:
    value = re.sub(r"!\[[^]]*]\([^)]*\)", "", value)
    value = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[`*_~]", "", value)
    return " ".join(value.split()).strip(" -:.;")


def _sections(markdown: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"intro": []}
    current = "intro"
    fenced = False
    for raw in markdown.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = re.match(r"^#{1,4}\s+(.+)$", line)
        if heading:
            current = _clean_markdown(heading.group(1)).casefold()
            sections.setdefault(current, [])
        elif line:
            sections.setdefault(current, []).append(line)
    return sections


def extract_readme_evidence(markdown: str) -> dict[str, Any]:
    """Extract conservative claims and retain the exact supporting section."""
    sections = _sections(markdown[:250_000])
    purpose = ""
    # README prose commonly sits below the H1 product title, not before it.
    for heading, lines in sections.items():
        if heading in FEATURE_HEADINGS or heading in INSTALL_HEADINGS:
            break
        for line in lines:
            cleaned = _clean_markdown(line)
            if 35 <= len(cleaned) <= 700 and not cleaned.casefold().startswith(("build status", "license", "http")):
                purpose = cleaned
                break
        if purpose:
            break

    features: list[dict[str, str]] = []
    for heading, lines in sections.items():
        if heading not in FEATURE_HEADINGS:
            continue
        for line in lines:
            if not re.match(r"^(?:[-*+] |\d+[.)] )", line):
                continue
            cleaned = _clean_markdown(re.sub(r"^(?:[-*+] |\d+[.)] )", "", line))
            if 8 <= len(cleaned) <= 240 and cleaned not in {item["text"] for item in features}:
                features.append({"text": cleaned, "evidence_section": heading})
            if len(features) == 12:
                break

    install_text = "\n".join("\n".join(lines) for heading, lines in sections.items() if heading in INSTALL_HEADINGS)
    platforms = [name for name, pattern in PLATFORM_PATTERNS.items() if re.search(pattern, install_text, re.I)]
    lower = markdown.casefold()
    pricing = None
    if re.search(r"\bfree and open[ -]source\b|\bopen[ -]source and free\b", lower):
        pricing = {"model": "Free", "pricing_type": "free", "evidence": "README explicitly describes the product as free and open-source."}

    return {"purpose": purpose, "features": features, "platforms": platforms, "pricing": pricing}


def github_api(path: str) -> dict[str, Any]:
    headers = {"User-Agent": "AtlasFind-catalog-worker", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request("https://api.github.com" + path, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_repository_evidence(repository: str) -> dict[str, Any]:
    """Fetch first-party GitHub metadata and README without executing content."""
    safe_repository = "/".join(quote(part, safe="") for part in repository.split("/", 1))
    metadata = github_api(f"/repos/{safe_repository}")
    readme_response = github_api(f"/repos/{safe_repository}/readme")
    if readme_response.get("encoding") != "base64":
        raise ValueError("Unsupported README encoding")
    markdown = base64.b64decode(readme_response.get("content", ""), validate=False).decode("utf-8", errors="replace")
    evidence = extract_readme_evidence(markdown)
    evidence.update({
        "repository_checked_at": utc_now(),
        "repository_source_url": metadata.get("html_url"),
        "readme_source_url": readme_response.get("html_url"),
        "default_branch": metadata.get("default_branch"),
        "archived": bool(metadata.get("archived")),
        "disabled": bool(metadata.get("disabled")),
        "license": (metadata.get("license") or {}).get("spdx_id"),
        "latest_push_at": metadata.get("pushed_at"),
    })
    return evidence


def enrich_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    result = dict(candidate)
    repository = str(candidate.get("repository") or "")
    if repository.count("/") != 1:
        result["enrichment_status"] = "not_applicable"
        result["enrichment_error"] = "No valid official repository was recorded."
        return result
    try:
        result["official_evidence"] = fetch_repository_evidence(repository)
        result["enrichment_status"] = "evidence_collected"
        result.pop("enrichment_error", None)
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        result["enrichment_status"] = "retry_required"
        result["enrichment_error"] = f"{type(exc).__name__}: {exc}"
    return result
