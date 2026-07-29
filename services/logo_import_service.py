"""Secure download, validation and local import of approved tool logos."""
from __future__ import annotations

import hashlib
import io
import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, build_opener

from PIL import Image, ImageOps

from services.image_service import BASE_DIR, TOOLS_IMAGE_DIR, normalize_branding, safe_slug
from services.logo_discovery_service import (
    TIMEOUT_SECONDS,
    USER_AGENT,
    _LimitedRedirect,
    validate_remote_url,
)
from validators.image_validator import MAX_FILE_BYTES, MAX_PIXELS, validate_svg

BACKUP_DIR = BASE_DIR / "backups" / "v1.0.4-images" / "original"
ALLOWED_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
}


def _ascii_safe_url(url: str) -> str:
    """Percent-encode non-ASCII path/query characters without changing the host."""
    parts = urlsplit(url)
    path = quote(parts.path, safe="/%:@!$&'()*+,;=-._~")
    query = quote(parts.query, safe="=&?/:;+,%@!$'()*-._~")
    fragment = quote(parts.fragment, safe="-._~")
    return urlunsplit((parts.scheme, parts.netloc, path, query, fragment))


def _sniff_content_type(body: bytes) -> str | None:
    sample = body[:512].lstrip()
    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if body.startswith((b"\xff\xd8\xff",)):
        return "image/jpeg"
    if body.startswith(b"RIFF") and body[8:12] == b"WEBP":
        return "image/webp"
    if body.startswith(b"\x00\x00\x01\x00"):
        return "image/x-icon"
    lowered = sample.lower()
    if lowered.startswith(b"<?xml") or b"<svg" in lowered[:400]:
        return "image/svg+xml"
    return None


def _download(url: str, *, timeout_seconds: int | None = None) -> tuple[bytes, str, str]:
    safe_url = _ascii_safe_url(url)
    if not validate_remote_url(safe_url):
        raise ValueError("Logo URL must be a public HTTPS address")
    request = Request(
        safe_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    effective_timeout = timeout_seconds if timeout_seconds is not None else TIMEOUT_SECONDS
    with build_opener(_LimitedRedirect()).open(request, timeout=effective_timeout) as response:
        final_url = _ascii_safe_url(response.geturl())
        if not validate_remote_url(final_url):
            raise ValueError("Logo redirected to a blocked address")
        declared = response.headers.get("Content-Length")
        if declared and int(declared) > MAX_FILE_BYTES:
            raise ValueError("Logo exceeds the file size limit")
        body = response.read(MAX_FILE_BYTES + 1)
        if not body or len(body) > MAX_FILE_BYTES:
            raise ValueError("Logo is empty or too large")

        reported = response.headers.get_content_type()
        sniffed = _sniff_content_type(body)
        content_type = sniffed or reported
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Unsupported logo content type: {reported}")
        if reported in {"text/html", "application/xhtml+xml"} and sniffed is None:
            raise ValueError(f"Unsupported logo content type: {reported}")
        return body, content_type, final_url


def _convert_raster(body: bytes, destination: Path) -> dict:
    with Image.open(io.BytesIO(body)) as source:
        source.load()
        width, height = source.size
        if width * height > MAX_PIXELS:
            raise ValueError("Logo exceeds the maximum pixel area")
        if min(width, height) < 32:
            raise ValueError(f"Logo resolution is too low ({width}x{height})")
        frame = ImageOps.exif_transpose(source).convert("RGBA")
        frame.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        frame.save(destination, "WEBP", quality=92, method=6, exact=True)
        return {
            "width": frame.width,
            "height": frame.height,
            "transparent_background": frame.getextrema()[3][0] < 255,
            "original_width": width,
            "original_height": height,
        }


def import_approved_logo(tool: dict, candidate: dict, *, verified_by: str, timeout_seconds: int | None = None) -> dict:
    if candidate.get("review_status") != "approved":
        raise ValueError("Only approved logo candidates can be imported")
    source_url = str(candidate.get("url") or "")
    body, content_type, final_url = _download(source_url, timeout_seconds=timeout_seconds)
    slug = safe_slug(str(tool.get("slug") or tool.get("name") or "tool"))
    folder = TOOLS_IMAGE_DIR / slug
    folder.mkdir(parents=True, exist_ok=True)
    original_suffix = ALLOWED_CONTENT_TYPES[content_type]
    original_checksum = hashlib.sha256(body).hexdigest()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    original_path = BACKUP_DIR / f"{slug}-{original_checksum[:12]}{original_suffix}"
    if not original_path.exists():
        original_path.write_bytes(body)

    if content_type == "image/svg+xml":
        temp_svg = folder / "source.svg"
        temp_svg.write_bytes(body)
        svg_errors = validate_svg(temp_svg)
        if svg_errors:
            temp_svg.unlink(missing_ok=True)
            raise ValueError("; ".join(svg_errors))
        destination = folder / "logo.svg"
        shutil.move(str(temp_svg), destination)
        metadata = {"width": None, "height": None, "transparent_background": True}
        served_format = "svg"
    else:
        destination = folder / "logo.webp"
        metadata = _convert_raster(body, destination)
        served_format = "webp"

    checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
    local_path = destination.relative_to(BASE_DIR).as_posix()
    branding = normalize_branding(tool)
    branding["logo"].update({
        "status": "verified",
        "local_path": local_path,
        "source_url": candidate.get("source_page") or final_url,
        "asset_url": final_url,
        "source_type": candidate.get("source_type") or "official_product_site",
        "original_format": original_suffix.lstrip("."),
        "served_format": served_format,
        "width": metadata.get("width"),
        "height": metadata.get("height"),
        "aspect_ratio": (
            f"{metadata.get('width')}:{metadata.get('height')}"
            if metadata.get("width") and metadata.get("height") else "vector"
        ),
        "file_size_bytes": destination.stat().st_size,
        "checksum": checksum,
        "transparent_background": metadata.get("transparent_background"),
        "supports_light_theme": bool(candidate.get("supports_light_theme", True)),
        "supports_dark_theme": bool(candidate.get("supports_dark_theme", True)),
        "verified_at": date.today().isoformat(),
        "verified_by": verified_by,
        "license_status": candidate.get("license_status") or "brand_usage",
        "attribution_required": bool(candidate.get("attribution_required", False)),
        "notes": candidate.get("notes") or "Imported from an approved official-site candidate.",
    })
    metadata_path = folder / "metadata.json"
    metadata_path.write_text(json.dumps({
        "tool_slug": slug,
        "source_url": branding["logo"]["source_url"],
        "asset_url": final_url,
        "source_type": branding["logo"]["source_type"],
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "verified_at": branding["logo"]["verified_at"],
        "verified_by": verified_by,
        "checksum": checksum,
        "original_checksum": original_checksum,
        "original_format": branding["logo"]["original_format"],
        "served_format": served_format,
        "license_status": branding["logo"]["license_status"],
        "attribution_required": branding["logo"]["attribution_required"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return branding
