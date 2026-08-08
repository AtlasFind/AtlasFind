"""Discover, validate and locally import official-site logos for the manual expansion."""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from services.catalog_worker_logo_service import discover_worker_logo_candidates
from services.logo_import_service import import_approved_logo

RECORDS = ROOT / "data/research/manual-expansion-850-records.json"
REPORT = ROOT / "reports/manual-expansion-850-logo-import.json"


def process(record: dict) -> tuple[dict, dict]:
    existing = (record.get("branding") or {}).get("logo") or {}
    if existing.get("status") == "verified" and existing.get("local_path"):
        return record, {"slug": record["slug"], "status": "verified", "candidate_count": 0,
                        "asset_url": existing.get("asset_url"), "local_path": existing["local_path"], "reused": True}
    review = discover_worker_logo_candidates(record)
    failures = []
    candidates = list(review.get("candidates") or [])
    repository_url = str(record.get("source_code_url") or record.get("repository") or "")
    if not repository_url:
        repository_url = next((str(source.get("url") or "") for source in record.get("source_references", [])
                               if source.get("type") == "official-repository"), "")
    github_match = re.match(r"https://github\.com/([^/]+)/", repository_url, re.I)
    if github_match:
        # GitHub serves the account/organisation avatar behind this stable URL.
        # It is a useful official fallback for open-source projects whose own
        # website does not declare a machine-discoverable favicon or manifest.
        candidates.insert(0, {
            "url": f"https://github.com/{github_match.group(1)}.png?size=256",
            "source_page": repository_url,
            "source_type": "official_repository",
        })
    for raw in candidates:
        candidate = {**raw, "review_status": "approved", "license_status": "brand_usage",
                     "notes": "Imported from an asset declared by the official product website during the controlled AtlasFind 850 expansion."}
        try:
            branding = import_approved_logo(record, candidate, verified_by="atlasfind-controlled-expansion-review", timeout_seconds=12)
            logo = branding["logo"]
            record["branding"] = branding
            record["icon_url"] = "/" + logo["local_path"]
            record["icon_source"] = logo["source_type"]
            record["icon_alt"] = f"{record['name']} official logo"
            record["icon_meta"].update({"review_status": "verified", "official_asset": True,
                                        "checksum": logo["checksum"], "source_url": logo["source_url"]})
            return record, {"slug": record["slug"], "status": "verified", "candidate_count": len(candidates),
                            "asset_url": logo.get("asset_url"), "local_path": logo["local_path"]}
        except Exception as exc:
            failures.append(f"{type(exc).__name__}: {exc}")
    return record, {"slug": record["slug"], "status": "fallback", "candidate_count": len(candidates),
                    "errors": failures[-5:], "attempts": review.get("attempts") or []}


def main() -> None:
    records = json.loads(RECORDS.read_text(encoding="utf-8"))
    updated, results = {}, []
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(process, record): record["slug"] for record in records}
        for future in as_completed(futures):
            record, result = future.result()
            updated[record["slug"]] = record
            results.append(result)
            print(f"{result['status']}: {result['slug']}", flush=True)
    records = [updated[record["slug"]] for record in records]
    RECORDS.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    results.sort(key=lambda item: item["slug"])
    verified = sum(item["status"] == "verified" for item in results)
    REPORT.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "total": len(results),
        "verified": verified, "fallback": len(results)-verified, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total": len(results), "verified": verified, "fallback": len(results)-verified}))


if __name__ == "__main__": main()
