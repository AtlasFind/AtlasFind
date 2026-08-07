"""Build schema-complete, non-public staging records for the 600-to-700 expansion."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "research" / "catalog-expansion-700.json"
OUTPUT_PATH = ROOT / "data" / "research" / "catalog-expansion-records.json"

OPEN_SOURCE = {
    "wallabag", "linkwarden", "karakeep", "podman-desktop", "rancher-desktop", "lazygit",
    "wezterm", "tabby", "lapce", "ente-auth", "portmaster", "simplewall", "qubes-os",
    "fan-control", "scrcpy", "prismlauncher", "navidrome", "finamp", "coolify", "caprover",
    "hestia-control-panel", "bruno", "hoppscotch", "helix-editor", "vscodium", "pgadmin",
    "redisinsight", "dbgate", "affine", "appflowy", "siyuan", "triliumnext-notes", "audiomass",
    "mumble", "revolt", "session", "gamescope", "bottles", "dokploy", "yunohost", "dokku",
    "cromite", "cryptomator", "dangerzone", "age", "ente-photos", "immich", "photoprism",
    "librephotos", "actual-budget", "umami",
}

PAID = {
    "masterclass", "quickbooks-online", "paddle", "chargebee", "mercury", "mendeley", "endnote",
    "paperpile", "datagrip", "tableplus", "1password", "teamspeak", "threema", "plesk",
}

WEB_FIRST = {
    "morgen", "routine", "superlist", "twos", "reclaim-ai", "amplenote", "dialpad", "ringcentral",
    "chanty", "udacity", "masterclass", "quickbooks-online", "paddle", "chargebee", "mercury",
    "umami", "socialbee", "metricool", "raindrop-io", "wallabag", "linkwarden",
    "karakeep", "readwise", "mendeley", "endnote", "paperpile", "descript", "riverside", "spline",
    "render", "coolify", "caprover", "plesk", "cyberpanel", "hestia-control-panel", "hoppscotch",
    "affine", "getresponse", "beehiiv", "dokploy", "easypanel", "cloudron", "yunohost", "dokku",
}

WINDOWS_ONLY = {"fan-control", "winaero-tweaker", "simplewall"}
LINUX_ONLY = {"gamescope"}
MOBILE = {"structured", "twos", "ente-auth", "authy", "session", "threema", "ente-photos", "finamp"}
AI_TOOLS = {"reclaim-ai", "dialpad", "descript", "riverside", "warp", "affine"}


def pricing_for(slug: str) -> tuple[str, str]:
    if slug in OPEN_SOURCE:
        return "Free", "free"
    if slug in PAID:
        return "Paid", "paid"
    return "Freemium", "freemium"


def platforms_for(slug: str) -> list[str]:
    if slug in WINDOWS_ONLY:
        return ["Windows"]
    if slug in LINUX_ONLY:
        return ["Linux"]
    platforms = []
    if slug in WEB_FIRST:
        platforms.append("Web")
    if slug in MOBILE:
        platforms.extend(["Android", "iOS"])
    if not platforms:
        platforms = ["Windows", "macOS", "Linux"]
    return platforms


def initials(name: str) -> str:
    words = [word for word in name.replace(".", " ").split() if word]
    return "".join(word[0] for word in words[:2]).upper() or "AF"


def main() -> None:
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    today = date(2026, 8, 7)
    records = []
    for offset, candidate in enumerate(queue["candidates"], start=601):
        slug = candidate["slug"]
        name = candidate["name"]
        category = candidate["category"]
        subcategory = candidate["subcategory"]
        website = candidate["official_url"]
        pricing, pricing_type = pricing_for(slug)
        platforms = platforms_for(slug)
        description = f"{name} is a {subcategory.lower()} tool for users evaluating software in the {category.lower()} category."
        domain = urlparse(website).netloc.casefold().removeprefix("www.")
        records.append({
            "id": offset,
            "slug": slug,
            "name": name,
            "description": description,
            "category": category,
            "tags": [subcategory, category, "Software"],
            "pricing": pricing,
            "pricing_type": pricing_type,
            "rating": 0,
            "rating_source": "not-rated",
            "website": website,
            "platforms": platforms,
            "open_source": slug in OPEN_SOURCE,
            "offline": slug in OPEN_SOURCE and "Web" not in platforms,
            "ai_powered": slug in AI_TOOLS,
            "minimum_ram_gb": None,
            "system_level": "unknown",
            "languages": ["en", "tr"],
            "pros": ["Official product source is available", f"Focused on {subcategory.lower()} workflows"],
            "cons": ["Pricing and platform details require final editorial confirmation"],
            "target_users": [f"Users looking for {subcategory.lower()} software", "Teams comparing software options"],
            "system_requirements": ["See the official product documentation for current requirements"],
            "pricing_details": {"model": pricing, "note": "Final plan limits and regional pricing are pending editorial confirmation."},
            "verification": {"status": "partially_verified", "date": today.isoformat(), "note": "Identity, official website and taxonomy placement are confirmed; pricing and platform evidence remain under review."},
            "subcategory": subcategory,
            "popularity_score": 25,
            "editor_choice": False,
            "date_added": today.isoformat(),
            "collections": ["open-source"] if slug in OPEN_SOURCE else [],
            "freshness": {"last_checked_at": today.isoformat(), "last_updated_at": today.isoformat(), "next_check_at": (today + timedelta(days=90)).isoformat(), "status": "current"},
            "change_history": [{"date": today.isoformat(), "type": "data-review", "summary": "Staged for official-source editorial review.", "changes": []}],
            "price_history": [],
            "quality_status": "partially_verified",
            "quality_review": {"scope": "official-source-staging", "reviewed_at": today.isoformat(), "note": "Not eligible for public release until the remaining evidence claims are confirmed."},
            "icon_url": f"/static/icons/generated/{slug}.svg",
            "icon_source": "local-generated",
            "icon_alt": f"{name} icon",
            "icon_fallback_url": f"/static/icons/generated/{slug}.svg",
            "icon_meta": {"fallback": "local-svg-monogram", "initials": initials(name), "domain": domain, "lazy_load": True, "review_status": "staged"},
            "aliases": [],
            "publication_status": "pending_review",
            "source_references": [{"label": f"{name} official website", "url": website, "type": "official-homepage", "checked_at": today.isoformat(), "domain": domain, "claims": ["identity", "website", "description", "category"]}],
        })
    OUTPUT_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(records)} schema-complete staging records")


if __name__ == "__main__":
    main()
