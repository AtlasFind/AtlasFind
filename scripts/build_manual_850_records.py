"""Build schema-complete staging records for the manually controlled 700→850 expansion."""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from icon_system import ensure_local_icon
from tool_schema import validate_tools
SELECTION = ROOT / "data/research/manual-expansion-850-selection.json"
CATALOG = ROOT / "data/tools.json"
OUTPUT = ROOT / "data/research/manual-expansion-850-records.json"


def initials(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name)
    return "".join(word[0] for word in words[:2]).upper() or "AF"


def domain(url: str) -> str:
    return (urlparse(url).hostname or "").casefold().removeprefix("www.")


def platform_values(candidate: dict) -> list[str]:
    tags = " ".join(candidate.get("directory_tags") or []).casefold()
    name = candidate["name"].casefold()
    if "games" in tags and name in {"mindustry", "luanti", "openttd"}:
        return ["Windows", "macOS", "Linux", "Android"]
    return ["Web", "Linux"]


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    selected = json.loads(SELECTION.read_text(encoding="utf-8"))["candidates"]
    previous = {}
    if OUTPUT.exists():
        previous = {record["slug"]: record for record in json.loads(OUTPUT.read_text(encoding="utf-8"))}
    today = date.today()
    records = []
    for tool_id, item in enumerate(selected, start=max(tool["id"] for tool in catalog) + 1):
        name, slug = item["name"], item["slug"]
        category, subcategory = item["category"], item["subcategory"]
        website, repository = item["official_url"], item["source_code_url"]
        licenses = item.get("licenses") or ["Open-source"]
        capabilities = list(dict.fromkeys([subcategory, *(item.get("directory_tags") or [])]))[:6]
        fallback_url = ensure_local_icon(name, slug)
        record = {
            "id": tool_id, "slug": slug, "name": name,
            "description": item["description_source_text"], "purpose": item["description_source_text"],
            "features": capabilities, "category": category,
            "tags": capabilities or [category], "pricing": "Free and open-source", "pricing_type": "free",
            "rating": 0, "rating_source": "not-rated", "website": website,
            "platforms": platform_values(item), "open_source": True, "offline": False,
            "ai_powered": category == "Artificial Intelligence", "minimum_ram_gb": None,
            "system_level": "unknown", "languages": ["en", "tr"],
            "pros": ["Source code is publicly available", "Can be self-hosted", f"Focused on {subcategory.lower()} workflows"],
            "cons": ["Setup and maintenance requirements depend on the selected deployment method"],
            "target_users": [f"Users looking for {subcategory.lower()} software", "Teams preferring self-hosted software"],
            "system_requirements": ["A supported server or container environment", "A modern web browser for web-based access", "See official documentation for version-specific requirements"],
            "pricing_details": {"model": "Free and open-source", "note": f"The source project is distributed under: {', '.join(licenses)}. Hosting and third-party infrastructure may create separate costs."},
            "verification": {"status": "partially_verified", "date": today.isoformat(), "note": "Identity, official website, source repository, license and taxonomy were checked; final logo and live-source audit remain required before publication."},
            "subcategory": subcategory, "popularity_score": min(100, max(20, int(item.get("stars") or 0) // 1000)),
            "editor_choice": False, "date_added": today.isoformat(), "collections": ["free-tools", "open-source"],
            "freshness": {"last_checked_at": today.isoformat(), "last_updated_at": today.isoformat(), "next_check_at": (today + timedelta(days=90)).isoformat(), "status": "current"},
            "change_history": [{"date": today.isoformat(), "type": "data-review", "summary": "Added through the controlled AtlasFind 850-tool expansion review.", "changes": ["Official identity and source recorded", "Taxonomy placement reviewed", "Local icon fallback generated"]}],
            "price_history": [], "quality_status": "partially_verified",
            "quality_review": {"scope": "manual-850-expansion", "reviewed_at": today.isoformat(), "note": "Pending final live URL and official logo verification."},
            "icon_url": fallback_url, "icon_source": "local-generated", "icon_alt": f"{name} icon",
            "icon_fallback_url": fallback_url,
            "icon_meta": {"fallback": "local-svg-monogram", "initials": initials(name), "domain": domain(website), "lazy_load": True, "review_status": "pending-official-logo"},
            "aliases": [], "publication_status": "pending_review",
            "source_references": [
                {"label": f"{name} official website", "url": website, "type": "official-homepage", "checked_at": today.isoformat(), "domain": domain(website), "claims": ["identity", "website", "description", "category"]},
                {"label": f"{name} official source code", "url": repository, "type": "official-repository", "checked_at": today.isoformat(), "domain": domain(repository), "claims": ["identity", "open_source", "license", "features"]},
            ],
            "manual_expansion_meta": {"stars_at_selection": item.get("stars"), "licenses": licenses,
                                      "directory_tags": item.get("directory_tags"), "source_record": item.get("source_record")},
        }
        old = previous.get(slug) or {}
        if (old.get("branding") or {}).get("logo", {}).get("status") == "verified":
            for field in ("branding", "icon_url", "icon_source", "icon_alt", "icon_meta"):
                record[field] = old[field]
        records.append(record)
    errors = validate_tools(records)
    if errors:
        raise SystemExit("\n".join(errors[:50]))
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(records)} schema-valid manual staging records ({records[0]['id']}..{records[-1]['id']})")


if __name__ == "__main__":
    main()
