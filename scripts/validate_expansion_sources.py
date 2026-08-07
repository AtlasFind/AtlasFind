"""Check official-source coverage and optionally test every expansion URL."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data" / "research" / "catalog-expansion-700.json"
SOURCES = ROOT / "data" / "research" / "catalog-expansion-official-urls.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def probe(item: tuple[str, str]) -> tuple[str, int | None, str]:
    slug, url = item
    request = urllib.request.Request(url, headers={"User-Agent": "AtlasFindCatalogVerifier/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=18) as response:
            return slug, response.status, response.geturl()
    except urllib.error.HTTPError as exc:
        return slug, exc.code, exc.geturl()
    except Exception as exc:
        return slug, None, type(exc).__name__


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", action="store_true")
    args = parser.parse_args()
    candidates = read_json(QUEUE)["candidates"]
    sources = read_json(SOURCES)
    slugs = {item["slug"] for item in candidates}
    missing = sorted(slugs - set(sources))
    extra = sorted(set(sources) - slugs)
    invalid = sorted(slug for slug, url in sources.items() if urlparse(url).scheme != "https" or not urlparse(url).netloc)
    if missing or extra or invalid:
        raise SystemExit(f"Source map invalid: missing={missing}, extra={extra}, invalid={invalid}")
    print(f"Official-source coverage valid: {len(sources)}/{len(candidates)}")
    if not args.network:
        return

    failures = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(probe, item) for item in sources.items()]
        for future in as_completed(futures):
            slug, status, final = future.result()
            if status is None or status >= 500 or status == 404:
                failures.append((slug, status, final))
    if failures:
        for failure in sorted(failures):
            print("FAILED", *failure)
        raise SystemExit(f"Network verification failed for {len(failures)} source(s)")
    print(f"Network verification passed: {len(sources)} official URLs responded")


if __name__ == "__main__":
    main()
