"""Review-first official logo pipeline for catalog-worker candidates."""

from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from PIL import Image

from services.logo_discovery_service import discover_logo_candidates
from services.logo_import_service import ALLOWED_CONTENT_TYPES, _download
from validators.image_validator import MAX_PIXELS, validate_svg

MIN_DISCOVERY_SCORE = 85
QUARANTINE_ROOT = Path(__file__).resolve().parents[1] / "data" / "research" / "catalog-worker-assets"


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").casefold().removeprefix("www.")


def _same_site(left: str, right: str) -> bool:
    a, b = _host(left), _host(right)
    return bool(a and b and (a == b or a.endswith("." + b) or b.endswith("." + a)))


def _safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.casefold()).strip("-") or "tool"


def rank_worker_logo_candidates(official_url: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep plausible official assets, but never auto-approve one as the brand logo."""
    accepted: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in candidates:
        url = str(raw.get("url") or "")
        relation = str(raw.get("relation") or "").casefold()
        score = int(raw.get("score") or 0)
        if not url.startswith("https://") or url in seen:
            continue
        same_site = _same_site(url, official_url)
        declared_by_official_page = _same_site(str(raw.get("source_page") or ""), official_url)
        # Social cards often contain text/screenshots and are not app avatars.
        social_card = relation == "og:image"
        product_marker = any(token in url.casefold() for token in ("logo", "icon", "favicon", "app-icon"))
        if score < MIN_DISCOVERY_SCORE or (social_card and not product_marker) or not (same_site or declared_by_official_page):
            continue
        seen.add(url)
        item = dict(raw)
        item.update({
            "review_status": "pending_human_review",
            "brand_match_status": "official_domain_candidate" if same_site else "declared_by_official_page",
            "auto_publish_allowed": False,
            "rejection_reason": None,
        })
        accepted.append(item)
    return sorted(accepted, key=lambda item: (-int(item.get("score") or 0), str(item.get("url"))))


def discover_worker_logo_candidates(record: dict[str, Any]) -> dict[str, Any]:
    official_url = str(record.get("website") or "")
    alternatives = []
    for source in record.get("source_references") or []:
        source_type = source.get("type")
        if source_type == "official-repository":
            alternatives.append({"url": source.get("url"), "source_type": "official_repository"})
        elif source_type in {"official-documentation", "official-brand-kit", "official-app-store"}:
            alternatives.append({"url": source.get("url"), "source_type": source_type.replace("-", "_")})
    candidates, attempts = discover_logo_candidates(official_url, alternatives)
    accepted = rank_worker_logo_candidates(official_url, candidates)
    return {
        "status": "candidates_found" if accepted else "official_asset_not_found",
        "candidates": accepted,
        "attempts": attempts,
        "requires_human_selection": True,
        "selected_candidate": None,
    }


def quarantine_logo_candidate(slug: str, candidate: dict[str, Any], *, root: Path = QUARANTINE_ROOT) -> dict[str, Any]:
    """Download and inspect an official candidate without making it public."""
    if candidate.get("review_status") not in {"pending_human_review", "selected_for_preflight"}:
        raise ValueError("Only review candidates can enter quarantine")
    body, content_type, final_url = _download(str(candidate.get("url") or ""))
    suffix = ALLOWED_CONTENT_TYPES[content_type]
    checksum = hashlib.sha256(body).hexdigest()
    folder = root / _safe_slug(slug)
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / f"{checksum[:16]}{suffix}"
    metadata: dict[str, Any]
    if content_type == "image/svg+xml":
        destination.write_bytes(body)
        errors = validate_svg(destination)
        if errors:
            destination.unlink(missing_ok=True)
            raise ValueError("; ".join(errors))
        metadata = {"format": "svg", "width": None, "height": None, "transparent": True}
    else:
        try:
            with Image.open(io.BytesIO(body)) as image:
                image.verify()
            with Image.open(io.BytesIO(body)) as image:
                width, height = image.size
                if width * height > MAX_PIXELS:
                    raise ValueError("Image exceeds maximum pixel area")
                if min(width, height) < 64:
                    raise ValueError(f"Logo resolution is too low ({width}x{height})")
                metadata = {"format": (image.format or "").casefold(), "width": width, "height": height,
                            "transparent": "A" in image.getbands()}
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        destination.write_bytes(body)
    return {
        "status": "quarantined_needs_human_review",
        "source_url": candidate.get("source_page"),
        "asset_url": final_url,
        "source_type": candidate.get("source_type"),
        "checksum": checksum,
        "file_size_bytes": len(body),
        "quarantine_path": destination.as_posix(),
        "auto_publish_allowed": False,
        **metadata,
    }
