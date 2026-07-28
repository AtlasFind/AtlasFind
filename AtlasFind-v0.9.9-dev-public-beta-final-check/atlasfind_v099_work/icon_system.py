"""Shared icon helpers for AtlasFind v0.9.6."""
from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path
from urllib.parse import urlparse

ICON_DIR = Path(__file__).resolve().parent / "static" / "icons" / "generated"


def icon_initials(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9ÇĞİÖŞÜçğıöşü]+", name or "")
    if not words:
        return "AF"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def icon_palette(slug: str) -> tuple[str, str]:
    digest = hashlib.sha256((slug or "atlasfind").encode("utf-8")).hexdigest()
    hue = int(digest[:4], 16) % 360
    hue2 = (hue + 42 + int(digest[4:6], 16) % 55) % 360
    return f"hsl({hue} 72% 52%)", f"hsl({hue2} 70% 39%)"


def render_monogram_svg(name: str, slug: str) -> str:
    initials = html.escape(icon_initials(name))
    first, second = icon_palette(slug)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="{html.escape(name)} icon fallback">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{first}"/><stop offset="1" stop-color="{second}"/></linearGradient></defs>
  <rect width="128" height="128" rx="30" fill="url(#g)"/>
  <circle cx="102" cy="24" r="30" fill="#fff" opacity=".10"/>
  <text x="64" y="71" text-anchor="middle" dominant-baseline="middle" fill="#fff" font-family="Arial,Helvetica,sans-serif" font-size="46" font-weight="800" letter-spacing="-2">{initials}</text>
</svg>'''


def ensure_local_icon(name: str, slug: str, directory: Path = ICON_DIR) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    safe_slug = re.sub(r"[^a-z0-9-]+", "-", (slug or "tool").lower()).strip("-") or "tool"
    path = directory / f"{safe_slug}.svg"
    path.write_text(render_monogram_svg(name, safe_slug), encoding="utf-8")
    return f"/static/icons/generated/{path.name}"


def website_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""
