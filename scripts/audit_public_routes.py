"""Render every sitemap URL and verify basic indexability requirements."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app


def main() -> int:
    app.config.update(TESTING=True)
    client = app.test_client()
    sitemap_response = client.get("/sitemap.xml")
    if sitemap_response.status_code != 200:
        print(f"Public route audit failed: sitemap returned {sitemap_response.status_code}.")
        return 1

    root = ElementTree.fromstring(sitemap_response.data)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    paths = [urlsplit(node.text or "").path for node in root.findall("sm:url/sm:loc", namespace)]
    status_counts: Counter[int] = Counter()
    failures: list[tuple[str, int]] = []
    missing_title: list[str] = []
    missing_description: list[str] = []
    missing_canonical: list[str] = []

    for path in paths:
        response = client.get(path, headers={"User-Agent": "AtlasFindAuditBot/1.0"})
        status_counts[response.status_code] += 1
        if response.status_code != 200:
            failures.append((path, response.status_code))
            continue
        if response.mimetype != "text/html":
            continue
        html = response.get_data(as_text=True)
        if not re.search(r"<title>.+?</title>", html, re.DOTALL):
            missing_title.append(path)
        if 'name="description" content="' not in html:
            missing_description.append(path)
        if 'rel="canonical" href="' not in html:
            missing_canonical.append(path)

    errors = failures or missing_title or missing_description or missing_canonical
    print(f"Public route audit: {len(paths)} sitemap URLs; statuses={dict(sorted(status_counts.items()))}.")
    if failures:
        print(f"Non-200 routes: {failures[:30]}")
    if missing_title:
        print(f"Missing titles: {missing_title[:20]}")
    if missing_description:
        print(f"Missing descriptions: {missing_description[:20]}")
    if missing_canonical:
        print(f"Missing canonicals: {missing_canonical[:20]}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
