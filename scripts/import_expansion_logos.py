"""Import approved expansion logos and update isolated staging records."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.logo_import_service import import_approved_logo

QUEUE = ROOT / "data" / "research" / "catalog-expansion-logo-queue.json"
RECORDS = ROOT / "data" / "research" / "catalog-expansion-records.json"


def main() -> None:
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    records = json.loads(RECORDS.read_text(encoding="utf-8"))
    by_slug = {tool["slug"]: tool for tool in records}
    imported = failures = 0
    for item in payload["items"]:
        if item.get("status") == "imported":
            continue
        approved = [candidate for candidate in item.get("candidates", []) if candidate.get("review_status") == "approved"]
        if not approved:
            continue
        tool = by_slug[item["slug"]]
        try:
            tool["branding"] = import_approved_logo(tool, approved[0], verified_by="atlasfind-logo-review", timeout_seconds=12)
            item["status"] = "imported"
            item["last_error"] = None
            item["imported_candidate_url"] = approved[0].get("url")
            imported += 1
            print(f"Imported {item['slug']}")
        except Exception as exc:
            item["status"] = "error"
            item["last_error"] = str(exc)
            failures += 1
            print(f"FAILED {item['slug']}: {exc}")
        RECORDS.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        QUEUE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Expansion logo import complete: imported={imported}, failures={failures}")


if __name__ == "__main__":
    main()
