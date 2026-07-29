"""Image metadata and file security validation for AtlasFind v1.0.4."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

from services.image_service import BASE_DIR, STATIC_DIR, normalize_branding, safe_slug

ALLOWED_STATUS = {"missing", "pending", "downloaded", "processing", "needs_review", "verified", "rejected", "broken", "outdated", "license_unknown"}
ALLOWED_SOURCE_TYPES = {"official_brand_kit", "official_product_site", "official_app_store", "official_repository", "manual_verified"}
ALLOWED_EXTENSIONS = {".webp", ".png", ".jpg", ".jpeg", ".svg", ".ico"}
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 25_000_000
EVENT_HANDLER_RE = re.compile(r"^on[a-z]+$", re.I)
DANGEROUS_SVG_TOKENS = ("javascript:", "file://", "data:text/html", "<!entity", "<!doctype")

@dataclass
class ImageValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    @property
    def valid(self) -> bool:
        return not self.errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_local_path(value: str | None) -> Path | None:
    if not value:
        return None
    raw = str(value).replace("\\", "/").lstrip("/")
    if raw.startswith("static/"):
        raw = raw[7:]
    path = (STATIC_DIR / raw).resolve()
    try:
        path.relative_to(STATIC_DIR.resolve())
    except ValueError:
        return None
    if path.is_symlink():
        return None
    return path


def validate_source_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc) and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}


def validate_svg(path: Path) -> list[str]:
    errors: list[str] = []
    raw = path.read_text(encoding="utf-8", errors="replace")
    lowered = raw.lower()
    if any(token in lowered for token in DANGEROUS_SVG_TOKENS):
        errors.append("SVG contains a dangerous external or executable reference")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return errors + ["SVG XML cannot be parsed"]
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in {"script", "foreignobject", "iframe", "object", "embed"}:
            errors.append(f"SVG contains forbidden element: {tag}")
        for name, value in element.attrib.items():
            local_name = name.rsplit("}", 1)[-1]
            if EVENT_HANDLER_RE.match(local_name):
                errors.append(f"SVG contains event handler: {local_name}")
            if local_name in {"href", "src"} and ("://" in value or value.lower().startswith(("javascript:", "file:"))):
                errors.append("SVG contains an external reference")
    return sorted(set(errors))


def inspect_raster(path: Path) -> tuple[dict, list[str]]:
    try:
        from PIL import Image
    except ImportError:
        return {}, ["Pillow is required to inspect raster images"]
    errors: list[str] = []
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            if width * height > MAX_PIXELS:
                errors.append("Image exceeds the maximum pixel area")
            metadata = {"width": width, "height": height, "format": (image.format or "").lower(), "transparent": "A" in image.getbands()}
    except Exception as exc:
        return {}, [f"Image cannot be decoded: {exc}"]
    return metadata, errors


def validate_tool_branding(tool: dict) -> ImageValidationResult:
    result = ImageValidationResult()
    branding = normalize_branding(tool)
    logo = branding["logo"]
    status = logo.get("status")
    if status not in ALLOWED_STATUS:
        result.errors.append(f"Unknown logo status: {status}")
    if branding.get("tool_slug") != safe_slug(str(tool.get("slug") or tool.get("name") or "tool")):
        result.errors.append("Branding slug does not match the tool slug")
    if status != "verified":
        result.warnings.append("Verified official logo is not available; safe local fallback will be used")
        return result
    if logo.get("source_type") not in ALLOWED_SOURCE_TYPES:
        result.errors.append("Verified logo has an invalid source type")
    if not validate_source_url(logo.get("source_url")):
        result.errors.append("Verified logo requires a valid HTTPS source URL")
    path = safe_local_path(logo.get("local_path"))
    if path is None:
        result.errors.append("Logo path escapes the static directory or is invalid")
        return result
    if not path.is_file():
        result.errors.append("Verified logo file is missing")
        return result
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        result.errors.append("Logo extension is not allowed")
    size = path.stat().st_size
    if not size or size > MAX_FILE_BYTES:
        result.errors.append("Logo file size is invalid")
    if path.suffix.lower() == ".svg":
        result.errors.extend(validate_svg(path))
        metadata = {"format": "svg"}
    else:
        metadata, image_errors = inspect_raster(path)
        result.errors.extend(image_errors)
        width = metadata.get("width", 0)
        height = metadata.get("height", 0)
        if min(width, height) < 128:
            result.warnings.append("Logo resolution is below the preferred 128 px minimum")
    checksum = sha256_file(path) if path.is_file() else None
    if logo.get("checksum") and checksum != logo.get("checksum"):
        result.errors.append("Logo checksum does not match")
    result.metadata = {**metadata, "file_size_bytes": size, "checksum": checksum}
    return result
