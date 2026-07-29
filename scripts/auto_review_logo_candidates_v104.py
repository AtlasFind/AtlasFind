from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.logo_import_service import _download

DEFAULT_QUEUE = ROOT / "data" / "branding" / "logo-queue.json"
SAFE_SOURCE_TYPES = {
    "official_product_site",
    "official_brand_kit",
    "official_documentation",
    "official_repository",
    "official_app_store",
    "official_support",
    "official_company_site",
}
SAFE_RELATIONS = {
    "apple-touch-icon",
    "apple-touch-icon-precomposed",
    "manifest-icon",
    "icon",
    "shortcut icon",
    "mask-icon",
    "standard-endpoint-icon",
}
FORBIDDEN_SVG = (
    b"<script",
    b"foreignobject",
    b"onload=",
    b"onclick=",
    b"javascript:",
    b"file:",
)

# These companies publish many unrelated products from one root domain. A root
# favicon or generic touch icon must not silently become every product's logo.
MULTI_PRODUCT_HOSTS = {
    "apple.com",
    "microsoft.com",
    "google.com",
    "adobe.com",
    "amazon.com",
    "aws.amazon.com",
    "awsstatic.com",
    "meta.com",
    "facebook.com",
    "autodesk.com",
    "avid.com",
    "ea.com",
    "oracle.com",
    "atlassian.com",
    "zoho.com",
    "proton.me",
}

CORPORATE_HOST_TOKENS = {
    "apple.com": {"apple"},
    "microsoft.com": {"microsoft"},
    "google.com": {"google"},
    "adobe.com": {"adobe"},
    "amazon.com": {"amazon"},
    "aws.amazon.com": {"amazon", "aws"},
    "awsstatic.com": {"amazon", "aws"},
    "meta.com": {"meta"},
    "facebook.com": {"facebook", "meta"},
    "autodesk.com": {"autodesk"},
    "avid.com": {"avid"},
    "ea.com": {"ea", "electronic", "arts"},
    "oracle.com": {"oracle"},
    "atlassian.com": {"atlassian"},
    "zoho.com": {"zoho"},
    "proton.me": {"proton"},
}

GENERIC_ASSET_NAMES = {
    "favicon.ico",
    "favicon.png",
    "favicon.svg",
    "apple-touch-icon.png",
    "apple-touch-icon-precomposed.png",
    "touch-icon.png",
    "icon.png",
    "logo.png",
}
TOKEN_STOPWORDS = {
    "app",
    "apps",
    "application",
    "software",
    "tool",
    "tools",
    "official",
    "the",
    "for",
    "and",
    "pro",
    "studio",
    "cloud",
    "online",
    "desktop",
    "web",
}


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _registrableish(host: str) -> str:
    """Return a conservative host suffix without requiring a PSL dependency."""
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _same_site(left: str, right: str) -> bool:
    left_host, right_host = _host(left), _host(right)
    if not left_host or not right_host:
        return False
    return (
        left_host == right_host
        or left_host.endswith("." + right_host)
        or right_host.endswith("." + left_host)
        or _registrableish(left_host) == _registrableish(right_host)
    )


def _related_site(candidate_url: str, source_page: str, official_url: str) -> bool:
    # A candidate can live on an asset CDN, provided the page that declared it
    # is itself an official source. This preserves CDN support without trusting
    # arbitrary URLs copied into the queue.
    return _same_site(candidate_url, source_page) or _same_site(source_page, official_url)


def _relation_is_safe(relation: str) -> bool:
    normalized = " ".join(str(relation or "").lower().split())
    return normalized in SAFE_RELATIONS or (
        "icon" in normalized and "og:" not in normalized and "twitter" not in normalized
    )


def _slug_tokens(item: dict) -> set[str]:
    values = [item.get("slug"), item.get("name"), item.get("short_name")]
    values.extend(item.get("aliases") or [])
    tokens: set[str] = set()
    for value in values:
        normalized = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
        tokens.update(token for token in normalized.split() if len(token) >= 3 and token not in TOKEN_STOPWORDS)
    return tokens


def _candidate_text(candidate: dict) -> str:
    fields = (
        candidate.get("url"),
        candidate.get("source_page"),
        candidate.get("label"),
        candidate.get("title"),
        candidate.get("manifest_name"),
    )
    return " ".join(unquote(str(value or "")).lower() for value in fields)


def _product_relevance(item: dict, candidate: dict) -> tuple[bool, str]:
    tokens = _slug_tokens(item)
    if not tokens:
        return False, "missing_product_tokens"

    text = _candidate_text(candidate)
    candidate_url = str(candidate.get("url") or "")
    candidate_host = _host(candidate_url)
    path = unquote(urlparse(candidate_url).path).lower()
    basename = Path(path).name
    source_page = str(candidate.get("source_page") or item.get("official_url") or "")

    token_matches = {token for token in tokens if token in text}
    host_matches = {token for token in tokens if token in candidate_host}
    path_matches = {token for token in tokens if token in path}

    corporate_host = next(
        (
            host
            for host in MULTI_PRODUCT_HOSTS
            if candidate_host == host or candidate_host.endswith("." + host)
        ),
        None,
    )
    generic_asset = (
        basename in GENERIC_ASSET_NAMES
        or basename.startswith("apple-touch-icon")
        or basename.startswith("touch-icon")
        or "favicon" in basename
    )

    # A generic root asset from a multi-product company is not product evidence.
    # A product name appearing only in the declaring page is insufficient; the
    # asset URL, host, filename, label, or manifest metadata must identify the
    # product itself. This blocks generic Apple/AWS/Microsoft touch icons.
    asset_text = " ".join(
        unquote(str(value or "")).lower()
        for value in (
            candidate.get("url"),
            candidate.get("label"),
            candidate.get("title"),
            candidate.get("manifest_name"),
        )
    )
    asset_token_matches = {token for token in tokens if token in asset_text}
    company_tokens = CORPORATE_HOST_TOKENS.get(corporate_host or "", set())
    product_tokens = tokens - company_tokens
    product_asset_matches = {token for token in product_tokens if token in asset_text}
    product_host_matches = {token for token in product_tokens if token in candidate_host}
    product_path_matches = {token for token in product_tokens if token in path}

    # On a multi-product corporate host, matching only the company name is not
    # product evidence. OneDrive needs "onedrive", Amazon S3 needs "s3", etc.
    if corporate_host:
        if not product_tokens:
            return False, "missing_distinct_product_token"
        if generic_asset and not (product_asset_matches or product_host_matches or product_path_matches):
            return False, "generic_corporate_asset"
        if not (product_asset_matches or product_host_matches or product_path_matches):
            return False, "corporate_asset_without_product_marker"
        return True, "product_match"

    if token_matches or host_matches or path_matches:
        return True, "product_match"

    # Single-product official domains may legitimately use a generic icon path.
    if _same_site(candidate_url, item.get("official_url") or "") and not corporate_host:
        return True, "single_product_official_domain"

    return False, "product_name_not_present"


def _preflight(candidate: dict, min_size: int) -> tuple[bool, str, dict]:
    try:
        body, content_type, final_url = _download(str(candidate.get("url") or ""))
        checksum = hashlib.sha256(body).hexdigest()
        if content_type == "image/svg+xml":
            lowered = body.lower()
            if any(token in lowered for token in FORBIDDEN_SVG):
                return False, "unsafe_svg", {"checksum": checksum}
            return True, "safe_svg", {
                "content_type": content_type,
                "final_url": final_url,
                "checksum": checksum,
            }
        with Image.open(io.BytesIO(body)) as image:
            image.load()
            width, height = image.size
        if min(width, height) < min_size:
            return False, f"low_resolution_{width}x{height}", {
                "width": width,
                "height": height,
                "checksum": checksum,
            }
        return True, "raster_ok", {
            "content_type": content_type,
            "final_url": final_url,
            "width": width,
            "height": height,
            "checksum": checksum,
        }
    except Exception as exc:
        return False, str(exc), {}


def _candidate_is_eligible(
    item: dict,
    candidate: dict,
    threshold: int,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    official_url = str(item.get("official_url") or "")
    url = str(candidate.get("url") or "")
    source_page = str(candidate.get("source_page") or official_url)
    relation = str(candidate.get("relation") or "")
    score = int(candidate.get("score") or 0)

    if candidate.get("source_type") not in SAFE_SOURCE_TYPES:
        reasons.append("source_type")
    if not _relation_is_safe(relation):
        reasons.append("relation")
    if not _related_site(url, source_page, official_url):
        reasons.append("unrelated_source")
    if score < threshold:
        reasons.append("score")
    if urlparse(url).scheme.lower() != "https":
        reasons.append("https")

    relevant, relevance_reason = _product_relevance(item, candidate)
    if not relevant:
        reasons.append(relevance_reason)
    candidate["product_relevance"] = relevance_reason
    return not reasons, reasons


def _candidate_rank(item: dict, candidate: dict) -> tuple[int, int, str]:
    relevance = candidate.get("product_relevance")
    relevance_bonus = 20 if relevance == "product_match" else 5
    return (
        -(int(candidate.get("score") or 0) + relevance_bonus),
        -len(_slug_tokens(item).intersection(set(_candidate_text(candidate).split()))),
        str(candidate.get("url") or ""),
    )


def _load_items(payload: dict) -> list[dict]:
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise SystemExit("Queue items must be a list.")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Preflight and conservatively approve product-specific logo candidates. "
            "Generic corporate icons and duplicate assets are held for review."
        )
    )
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE.relative_to(ROOT)))
    parser.add_argument("--threshold", type=int, default=100)
    parser.add_argument("--min-size", type=int, default=64)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--no-preflight", action="store_true", help="Skip network/image validation (not recommended).")
    parser.add_argument("--candidates-per-tool", type=int, default=6)
    args = parser.parse_args()

    queue_path = (ROOT / args.queue).resolve()
    if not queue_path.is_relative_to(ROOT) or not queue_path.exists():
        raise SystemExit("Queue not found or outside the project directory.")

    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    items = _load_items(payload)
    candidate_pools: list[tuple[dict, list[tuple[int, dict, dict]]]] = []
    skipped = Counter()

    for item in items:
        if item.get("status") == "imported":
            skipped["imported"] += 1
            continue
        if any(candidate.get("review_status") == "approved" for candidate in item.get("candidates", [])):
            skipped["already_approved"] += 1
            continue
        if item.get("status") not in {"review", "approved", "error", "no_candidate"}:
            skipped[item.get("status", "unknown")] += 1
            continue

        eligible: list[tuple[int, dict]] = []
        for index, candidate in enumerate(item.get("candidates", [])):
            ok, reasons = _candidate_is_eligible(item, candidate, args.threshold)
            candidate["auto_review_rejections"] = reasons
            if ok:
                eligible.append((index, candidate))
        eligible.sort(key=lambda pair: _candidate_rank(item, pair[1]))
        if not eligible:
            skipped["no_safe_candidate"] += 1
            continue

        passed: list[tuple[int, dict, dict]] = []
        for index, candidate in eligible[: max(1, args.candidates_per_tool)]:
            if args.no_preflight:
                metadata = {"preflight": "skipped"}
                passed.append((index, candidate, metadata))
                continue
            ok, reason, metadata = _preflight(candidate, args.min_size)
            candidate["preflight_status"] = "passed" if ok else "failed"
            candidate["preflight_reason"] = reason
            candidate["preflight_metadata"] = metadata
            candidate["preflight_at"] = datetime.now(timezone.utc).isoformat()
            if ok:
                passed.append((index, candidate, metadata))
        if passed:
            candidate_pools.append((item, passed))
        else:
            skipped["preflight_failed"] += 1

    # Resolve duplicate URLs/checksums globally. When the best candidate is used
    # by another product, try the next safe candidate for this tool.
    selected: list[tuple[dict, int, dict, dict]] = []
    used_urls: dict[str, str] = {}
    used_checksums: dict[str, str] = {}
    collision_log: list[dict] = []

    for item, pool in candidate_pools:
        if args.limit and len(selected) >= args.limit:
            break
        chosen = None
        for index, candidate, metadata in pool:
            url_key = str(metadata.get("final_url") or candidate.get("url") or "").lower()
            checksum = str(metadata.get("checksum") or "")
            url_owner = used_urls.get(url_key)
            checksum_owner = used_checksums.get(checksum) if checksum else None
            if url_owner and url_owner != item.get("slug"):
                candidate["auto_review_rejections"] = list(candidate.get("auto_review_rejections") or []) + [
                    f"duplicate_url_with:{url_owner}"
                ]
                collision_log.append({"slug": item.get("slug"), "owner": url_owner, "type": "url", "url": url_key})
                continue
            if checksum_owner and checksum_owner != item.get("slug"):
                candidate["auto_review_rejections"] = list(candidate.get("auto_review_rejections") or []) + [
                    f"duplicate_checksum_with:{checksum_owner}"
                ]
                collision_log.append({
                    "slug": item.get("slug"),
                    "owner": checksum_owner,
                    "type": "checksum",
                    "checksum": checksum,
                })
                continue
            chosen = (item, index, candidate, metadata)
            used_urls[url_key] = str(item.get("slug"))
            if checksum:
                used_checksums[checksum] = str(item.get("slug"))
            break
        if chosen:
            selected.append(chosen)
        else:
            skipped["duplicate_or_shared_asset"] += 1

    print(f"Queue items: {len(items)}")
    print(f"Product-specific preflight selections: {len(selected)}")
    print(f"Threshold: {args.threshold}; minimum raster size: {args.min_size}px")
    print(f"Duplicate/shared asset collisions: {len(collision_log)}")
    for key, value in sorted(skipped.items()):
        print(f"Skipped {key}: {value}")
    for item, index, candidate, metadata in selected[:25]:
        size = f" {metadata.get('width')}x{metadata.get('height')}" if metadata.get("width") else ""
        print(
            f"PREVIEW {item['slug']} #{index} score={candidate.get('score')}{size} "
            f"relevance={candidate.get('product_relevance')} {candidate.get('url')}"
        )
    if len(selected) > 25:
        print(f"... and {len(selected) - 25} more")
    for collision in collision_log[:10]:
        print(f"COLLISION {collision['slug']} shares {collision['type']} with {collision['owner']}")
    if len(collision_log) > 10:
        print(f"... and {len(collision_log) - 10} more collision(s)")

    diagnostics_path = queue_path.with_name("logo-auto-review-diagnostics.json")
    diagnostics_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "selected": [
                    {
                        "slug": item.get("slug"),
                        "candidate_index": index,
                        "url": candidate.get("url"),
                        "score": candidate.get("score"),
                        "product_relevance": candidate.get("product_relevance"),
                        "preflight_metadata": metadata,
                    }
                    for item, index, candidate, metadata in selected
                ],
                "collisions": collision_log,
                "skipped": dict(skipped),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if not args.apply:
        queue_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Diagnostics: {diagnostics_path.relative_to(ROOT)}")
        print("Dry run only. Use --apply after reviewing the product-specific selections.")
        return 0

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = queue_path.with_name(f"logo-queue.before-brand-guard-review.{timestamp}.json")
    backup_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    reviewed_at = datetime.now(timezone.utc).isoformat()

    for item, _, best, metadata in selected:
        for candidate in item.get("candidates", []):
            if candidate.get("review_status") == "pending":
                candidate["review_status"] = "rejected"
        best.update(
            {
                "review_status": "approved",
                "license_status": "brand_usage_review_required",
                "supports_light_theme": True,
                "supports_dark_theme": True,
                "review_method": "product_specific_brand_guard_preflight",
                "reviewed_at": reviewed_at,
                "approved_checksum": metadata.get("checksum"),
                "notes": (
                    "Auto-approved after official-source, product relevance, image preflight, "
                    "and duplicate asset checks; visual audit remains available."
                ),
            }
        )
        item["status"] = "approved"
        item["updated_at"] = reviewed_at

    queue_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Approved candidates written: {len(selected)}")
    print(f"Backup: {backup_path.relative_to(ROOT)}")
    print(f"Diagnostics: {diagnostics_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
