"""Build a fixed, reviewable 150-tool shortlist from a human-curated directory."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "work/manual-source-awesome-selfhosted/software"
CATALOG = ROOT / "data/tools.json"
OUTPUT = ROOT / "data/research/manual-expansion-850-selection.json"
LOGO_REPORT = ROOT / "reports/manual-expansion-850-logo-import.json"
LOGO_BLOCKLIST = ROOT / "data/research/manual-expansion-850-logo-blocklist.json"

CATEGORY_RULES = (
    (("generative artificial intelligence",), "Artificial Intelligence", "AI Applications"),
    (("audio", "music"), "Audio and Music", "Audio and Music Tools"),
    (("search engines", "feed readers", "bookmarks"), "Browsers and Internet", "Internet Tools"),
    (("file transfer", "archiving", "backup", "object storage"), "Cloud and Storage", "Storage and Sync"),
    (("communication", "social networks", "video conferencing", "email"), "Communication", "Communication Platforms"),
    (("password", "authentication", "proxy", "dns", "network utilities"), "Cybersecurity", "Security and Network Tools"),
    (("analytics", "database management", "maps and global"), "Data and Analytics", "Data Tools"),
    (("photo galleries", "design", "diagram"), "Design and Graphics", "Visual Tools"),
    (("software development", "pastebins", "api management"), "Development", "Developer Tools"),
    (("learning and courses", "conference management"), "Education", "Learning Platforms"),
    (("money", "e-commerce", "inventory", "resource planning", "customer relationship", "human resources"), "Finance and Business", "Business Tools"),
    (("games",), "Gaming and Entertainment", "Games and Entertainment"),
    (("newsletter", "marketing", "url shorteners"), "Marketing and SEO", "Marketing Tools"),
    (("document", "wikis", "note-taking", "office suites", "knowledge management"), "Office and Documents", "Documents and Knowledge"),
    (("task management", "time tracking", "calendar", "booking", "automation", "personal dashboards"), "Productivity", "Productivity Tools"),
    (("internet of things", "remote access", "video surveillance"), "System Utilities", "System and Device Tools"),
    (("media streaming - video",), "Video and Animation", "Video Tools"),
    (("self-hosting", "web servers", "content management", "blogging platforms"), "Web and Hosting", "Web Platforms"),
)


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def domain(url: str) -> str:
    return (urlparse(url).hostname or "").casefold().removeprefix("www.")


def classify(tags: list[str]) -> tuple[str, str]:
    joined = " | ".join(tags).casefold()
    for needles, category, subcategory in CATEGORY_RULES:
        if any(needle in joined for needle in needles):
            return category, subcategory
    return "Web and Hosting", "Self-Hosted Applications"


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    known_slugs = {slugify(tool["slug"]) for tool in catalog}
    known_names = {str(tool["name"]).casefold() for tool in catalog}
    known_domains = {domain(tool["website"]) for tool in catalog}
    blocked_slugs = set()
    if LOGO_BLOCKLIST.exists():
        blocked_slugs.update(json.loads(LOGO_BLOCKLIST.read_text(encoding="utf-8")))
    if OUTPUT.exists():
        previous_selection = json.loads(OUTPUT.read_text(encoding="utf-8"))
        blocked_slugs.update(previous_selection.get("replaced_logo_failures") or [])
    if LOGO_REPORT.exists():
        report = json.loads(LOGO_REPORT.read_text(encoding="utf-8"))
        blocked_slugs.update(item["slug"] for item in report.get("results", []) if item.get("status") == "fallback")
    pool = []
    for path in SOURCE.glob("*.yml"):
        item = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        name = str(item.get("name") or "").strip()
        website = str(item.get("website_url") or "").strip()
        source = str(item.get("source_code_url") or "").strip()
        slug = slugify(name)
        if item.get("archived") is True or not name or not website.startswith("https://") or not source.startswith("https://"):
            continue
        if slug in blocked_slugs or slug in known_slugs or name.casefold() in known_names or domain(website) in known_domains:
            continue
        stars = int(item.get("stargazers_count") or 0)
        if stars < 250:
            continue
        tags = [str(tag) for tag in item.get("tags") or []]
        category, subcategory = classify(tags)
        pool.append({
            "slug": slug, "name": name, "description_source_text": str(item["description"]).strip(),
            "official_url": website, "source_code_url": source,
            "licenses": [str(value) for value in item.get("licenses") or []],
            "technology_platforms": [str(value) for value in item.get("platforms") or []],
            "directory_tags": tags, "category": category, "subcategory": subcategory,
            "stars": stars, "updated_at": item.get("updated_at"), "source_record": path.name,
        })
    pool.sort(key=lambda item: (-item["stars"], item["name"].casefold()))
    selected, category_counts = [], Counter()
    for item in pool:
        if category_counts[item["category"]] >= 14:
            continue
        selected.append(item)
        category_counts[item["category"]] += 1
        if len(selected) == 150:
            break
    if len(selected) < 150:
        chosen = {item["slug"] for item in selected}
        for item in pool:
            if item["slug"] in chosen:
                continue
            selected.append(item)
            chosen.add(item["slug"])
            category_counts[item["category"]] += 1
            if len(selected) == 150:
                break
    if len(selected) != 150:
        raise SystemExit(f"Expected 150 candidates, found {len(selected)}")
    payload = {
        "version": 1, "status": "manual_shortlist_pending_official_review",
        "created_at": datetime.now(timezone.utc).isoformat(), "count": len(selected), "replaced_logo_failures": sorted(blocked_slugs),
        "category_counts": dict(sorted(category_counts.items())), "candidates": selected,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(selected), "categories": payload["category_counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
