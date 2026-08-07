"""Central, local-first tool image resolution for AtlasFind v1.0.4."""
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from pathlib import Path
from urllib.parse import quote

from icon_system import ensure_local_icon, icon_initials

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"
TOOLS_IMAGE_DIR = STATIC_DIR / "images" / "tools"
PUBLISHABLE_STATUSES = {"verified"}
SAFE_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_LOGO_FILENAMES = ("logo.webp", "logo.png", "logo.jpg", "logo.jpeg", "logo.svg")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "tool").lower()).strip("-")
    return slug or "tool"


def default_branding(tool: dict) -> dict:
    slug = safe_slug(str(tool.get("slug") or tool.get("name") or "tool"))
    return {
        "logo": {
            "status": "missing",
            "local_path": None,
            "source_url": None,
            "source_type": None,
            "original_format": None,
            "served_format": None,
            "width": None,
            "height": None,
            "aspect_ratio": None,
            "file_size_bytes": None,
            "checksum": None,
            "transparent_background": None,
            "supports_light_theme": None,
            "supports_dark_theme": None,
            "verified_at": None,
            "verified_by": None,
            "license_status": "unknown",
            "attribution_required": None,
            "notes": "Official logo verification required.",
        },
        "logo_light": None,
        "logo_dark": None,
        "icon": None,
        "fallback": {"type": "initials", "value": icon_initials(str(tool.get("name") or "AtlasFind"))},
        "version": 1,
        "tool_slug": slug,
    }


def normalize_branding(tool: dict) -> dict:
    branding = default_branding(tool)
    supplied = tool.get("branding")
    if isinstance(supplied, dict):
        for key, value in supplied.items():
            if key == "logo" and isinstance(value, dict):
                branding["logo"].update(value)
            else:
                branding[key] = deepcopy(value)
    branding["tool_slug"] = safe_slug(str(tool.get("slug") or tool.get("name") or "tool"))
    return branding


def _safe_static_path(local_path: str | None) -> Path | None:
    if not local_path:
        return None
    raw = str(local_path).replace("\\", "/").lstrip("/")
    if raw.startswith("static/"):
        raw = raw[7:]
    candidate = (STATIC_DIR / raw).resolve()
    try:
        candidate.relative_to(STATIC_DIR.resolve())
    except ValueError:
        return None
    return candidate


def _static_url(path: Path) -> str:
    relative = path.resolve().relative_to(STATIC_DIR.resolve()).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    return f"/static/{quote(relative)}?v={digest}"


def _variant(branding: dict, theme: str) -> dict | None:
    if theme == "dark" and isinstance(branding.get("logo_dark"), dict):
        return branding["logo_dark"]
    if theme == "light" and isinstance(branding.get("logo_light"), dict):
        return branding["logo_light"]
    return branding.get("logo") if isinstance(branding.get("logo"), dict) else None


def _catalog_local_logo(tool_slug: str) -> Path | None:
    """Recover an audited local logo when older database rows lack branding metadata."""
    if not SAFE_SLUG_RE.fullmatch(tool_slug):
        return None
    logo_directory = TOOLS_IMAGE_DIR / tool_slug
    for filename in LOCAL_LOGO_FILENAMES:
        candidate = logo_directory / filename
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def resolve_tool_image(tool: dict, theme: str = "default") -> dict:
    branding = normalize_branding(tool)
    candidate = _variant(branding, theme)
    if candidate and candidate.get("status") in PUBLISHABLE_STATUSES:
        path = _safe_static_path(candidate.get("local_path"))
        if path and path.is_file() and path.stat().st_size > 0:
            return {
                "url": _static_url(path),
                "fallback_url": ensure_local_icon(str(tool.get("name") or "AtlasFind"), branding["tool_slug"]),
                "status": candidate.get("status"),
                "is_fallback": False,
                "width": candidate.get("width") or 128,
                "height": candidate.get("height") or 128,
            }
    local_logo = _catalog_local_logo(branding["tool_slug"])
    if local_logo:
        return {
            "url": _static_url(local_logo),
            "fallback_url": ensure_local_icon(str(tool.get("name") or "AtlasFind"), branding["tool_slug"]),
            "status": "verified-local",
            "is_fallback": False,
            "width": 128,
            "height": 128,
        }
    fallback_url = ensure_local_icon(str(tool.get("name") or "AtlasFind"), branding["tool_slug"])
    return {"url": fallback_url, "fallback_url": fallback_url, "status": branding["logo"].get("status", "missing"), "is_fallback": True, "width": 128, "height": 128}


def enrich_tool_branding(tool: dict, theme: str = "default") -> dict:
    enriched = dict(tool)
    enriched["branding"] = normalize_branding(tool)
    resolved = resolve_tool_image(enriched, theme)
    enriched["icon_url"] = resolved["url"]
    enriched["icon_fallback_url"] = resolved["fallback_url"]
    enriched["icon_alt"] = f"{tool.get('name', 'AtlasFind')} logo"
    enriched["image_status"] = resolved["status"]
    enriched["image_is_fallback"] = resolved["is_fallback"]
    enriched["image_width"] = resolved["width"]
    enriched["image_height"] = resolved["height"]
    return enriched
