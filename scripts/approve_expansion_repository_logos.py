"""Approve product-specific application icons from official upstream repositories."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data" / "research" / "catalog-expansion-logo-queue.json"

ASSETS = {
    "bruno": ("usebruno/bruno", "main", "packages/bruno-electron/resources/icons/png/1024x1024.png"),
    "lapce": ("lapce/lapce", "master", "extra/images/logo_app.svg"),
    "immich": ("immich-app/immich", "main", "design/immich-logo.png"),
    "appflowy": ("appflowy-io/appflowy", "main", "frontend/appflowy_flutter/ios/Runner/Assets.xcassets/AppIcon.appiconset/1024.png"),
    "triliumnext-notes": ("TriliumNext/Notes", "develop", "apps/desktop/electron-forge/app-icon/png/1024x1024.png"),
    "cryptomator": ("cryptomator/cryptomator", "develop", "src/main/resources/img/logo128@2x.png"),
    "dangerzone": ("freedomofpress/dangerzone", "main", "share/icon.png"),
    "actual-budget": ("actualbudget/actual", "master", "packages/component-library/src/icons/logo/logo.svg"),
    "redisinsight": ("RedisInsight/RedisInsight", "main", "redisinsight/ui/public/favicon-180x180.png"),
    "mumble": ("mumble-voip/mumble", "master", "icons/mumble_256x256.png"),
    "age": ("FiloSottile/age", "main", "logo/logo.svg"),
}

OFFICIAL_SITE_ASSETS = {
    "superlist": "https://framerusercontent.com/images/bI0E6AOBvqILIpkzDCXQ2HSjAFQ.png",
    "riverside": "https://cdn.prod.website-files.com/685be7dcd32275d3830651d3/685be7dcd32275d383065e48_RS_favicon.png",
    "beehiiv": "https://beehiiv-marketing-images.s3.amazonaws.com/Redesign2023/favicon.png",
}


def main() -> None:
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    by_slug = {item["slug"]: item for item in payload["items"]}
    for slug, (repo, branch, path) in ASSETS.items():
        item = by_slug[slug]
        if item.get("status") == "imported":
            continue
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
        candidate = next((value for value in item.get("candidates", []) if value.get("url") == url), None)
        if candidate is None:
            candidate = {"url": url}
            item.setdefault("candidates", []).insert(0, candidate)
        candidate.update(
            {
                "source_page": f"https://github.com/{repo}/blob/{branch}/{path}",
                "source_type": "official_source_repository",
                "relation": "official-application-icon",
                "score": 200,
                "requires_review": False,
                "review_status": "approved",
                "license_status": "brand_usage",
                "product_relevance": "product_match",
                "discovery_method": "manual-official-repository-audit",
                "notes": "Product-specific application icon stored in the project's official upstream repository.",
            }
        )
        item["status"] = "approved"
        print(f"Approved official repository icon: {slug}")
    for slug, url in OFFICIAL_SITE_ASSETS.items():
        item = by_slug[slug]
        if item.get("status") == "imported":
            continue
        candidate = next((value for value in item.get("candidates", []) if value.get("url") == url), None)
        if candidate is None:
            candidate = {"url": url}
            item.setdefault("candidates", []).insert(0, candidate)
        candidate.update(
            {
                "source_page": item["official_url"],
                "source_type": "official_product_site",
                "relation": "official-site-icon",
                "score": 190,
                "requires_review": False,
                "review_status": "approved",
                "license_status": "brand_usage",
                "product_relevance": "product_match",
                "discovery_method": "manual-official-site-markup-audit",
                "notes": "Product-specific icon explicitly published by the official product site.",
            }
        )
        item["status"] = "approved"
        print(f"Approved official site icon: {slug}")
    QUEUE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
