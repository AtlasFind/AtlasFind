"""Create honest local fallbacks for tools whose upstream publishes no logo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from icon_system import ensure_local_icon, icon_initials

QUEUE = ROOT / "data/research/catalog-expansion-logo-queue.json"
RECORDS = ROOT / "data/research/catalog-expansion-records.json"
NO_UPSTREAM_ARTWORK = {
    "lazygit": "The official source repository and release artifacts publish no project or application logo.",
    "gamescope": "The official Valve source repository publishes no standalone project or application logo.",
    "cromite": "The official source repository publishes no reusable standalone application logo asset.",
}


def main() -> None:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    records = json.loads(RECORDS.read_text(encoding="utf-8"))
    by_slug = {item["slug"]: item for item in records}
    for item in queue["items"]:
        slug = item["slug"]
        if slug not in NO_UPSTREAM_ARTWORK:
            continue
        tool = by_slug[slug]
        local_url = ensure_local_icon(tool["name"], slug)
        tool["icon_url"] = local_url
        tool["icon_source"] = "local-generated-no-upstream-artwork"
        tool["icon_fallback_url"] = local_url
        tool["icon_meta"] = {
            "fallback": "local-svg-monogram",
            "initials": icon_initials(tool["name"]),
            "domain": item["official_url"].split("/")[2],
            "lazy_load": True,
            "review_status": "verified-fallback",
            "reason": NO_UPSTREAM_ARTWORK[slug],
        }
        tool["branding"] = {
            "logo": {
                "local_path": local_url,
                "source_url": item["official_url"],
                "asset_url": None,
                "source_type": "official-source-no-artwork",
                "original_format": "none",
                "served_format": "svg",
                "verified_at": "2026-08-08",
                "verified_by": "atlasfind-manual-source-audit",
                "license_status": "generated-fallback",
                "attribution_required": False,
                "notes": NO_UPSTREAM_ARTWORK[slug],
            }
        }
        item["status"] = "verified_fallback"
        item["fallback_url"] = local_url
        item["fallback_reason"] = NO_UPSTREAM_ARTWORK[slug]
        item["last_error"] = None
        print(f"Created verified fallback: {slug}")
    QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    RECORDS.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
