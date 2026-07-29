from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalog.loader import load_catalog
from services.logo_discovery_service import discover_logo_candidates


def _official_sources(tool: dict) -> list[dict]:
    sources: list[dict] = []
    type_map = {
        "official-documentation": "official_documentation",
        "official-support": "official_support",
        "official-repository": "official_repository",
        "official-app-store": "official_app_store",
        "official-brand-kit": "official_brand_kit",
        "official-company": "official_company_site",
    }
    for ref in tool.get("source_references") or []:
        if not isinstance(ref, dict):
            continue
        source_type = type_map.get(str(ref.get("type") or ""))
        url = str(ref.get("url") or "")
        if source_type and url:
            sources.append({"url": url, "source_type": source_type, "label": ref.get("label")})
    links = tool.get("official_links") or {}
    for key, source_type in {
        "documentation": "official_documentation",
        "github": "official_repository",
        "support": "official_support",
        "app_store": "official_app_store",
        "google_play": "official_app_store",
        "brand": "official_brand_kit",
    }.items():
        url = links.get(key) if isinstance(links, dict) else None
        if url:
            sources.append({"url": url, "source_type": source_type, "label": key})
    unique = {}
    for source in sources:
        unique[source["url"]] = source
    return list(unique.values())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover logo candidates from all official URLs stored in the catalog."
    )
    parser.add_argument("--queue", default="data/branding/logo-queue.json")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--retry-review", action="store_true", help="Extend discovery for tools already in review.")
    args = parser.parse_args()

    path = (ROOT / args.queue).resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    tools = {tool.get("slug"): tool for tool in load_catalog()}
    allowed = {"pending"}
    if args.retry_errors:
        allowed.add("error")
    if args.retry_review:
        allowed.update({"review", "no_candidate"})

    processed = found = failed = improved = 0
    for item in payload.get("items", []):
        if processed >= max(0, args.limit):
            break
        if item.get("status") not in allowed:
            continue
        processed += 1
        item["attempts"] = int(item.get("attempts", 0)) + 1
        item["updated_at"] = datetime.now(timezone.utc).isoformat()
        tool = tools.get(item.get("slug")) or {}
        old_urls = {candidate.get("url") for candidate in item.get("candidates", [])}
        try:
            candidates, attempt_log = discover_logo_candidates(
                item["official_url"],
                _official_sources(tool),
            )
            existing = {candidate.get("url"): candidate for candidate in item.get("candidates", [])}
            for candidate in candidates:
                previous = existing.get(candidate.get("url"), {})
                candidate["review_status"] = previous.get("review_status", "pending")
                candidate["license_status"] = previous.get("license_status", "unknown")
                candidate["supports_light_theme"] = previous.get("supports_light_theme")
                candidate["supports_dark_theme"] = previous.get("supports_dark_theme")
                candidate["last_import_error"] = previous.get("last_import_error")
            merged = {candidate.get("url"): candidate for candidate in item.get("candidates", [])}
            merged.update({candidate.get("url"): candidate for candidate in candidates})
            item["candidates"] = sorted(merged.values(), key=lambda c: (-int(c.get("score") or 0), str(c.get("url") or "")))
            item["discovery_attempt_log"] = attempt_log[-40:]
            item["official_source_count"] = 1 + len(_official_sources(tool))
            item["status"] = "review" if item["candidates"] else "no_candidate"
            errors = [entry for entry in attempt_log if entry.get("status") == "error"]
            item["last_error"] = errors[-1].get("error") if errors and not item["candidates"] else None
            found += bool(item["candidates"])
            new_count = len({c.get("url") for c in item["candidates"]} - old_urls)
            improved += bool(new_count)
            print(
                f"[{processed}] {item['slug']}: {len(item['candidates'])} candidate(s), "
                f"new={new_count}, sources={item['official_source_count']}, attempts={len(attempt_log)}"
            )
        except Exception as exc:
            item["status"] = "error"
            item["last_error"] = str(exc)
            failed += 1
            print(f"[{processed}] {item['slug']}: ERROR {exc}")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.delay > 0:
            time.sleep(args.delay)

    print(
        f"Extended discovery complete: processed={processed}, with_candidates={found}, "
        f"improved={improved}, errors={failed}"
    )
    return 1 if failed and processed == failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
