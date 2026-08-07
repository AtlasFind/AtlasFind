"""Materialize discovery candidates as AtlasFind-compatible review records."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.catalog_worker_record_service import build_review_records
from tool_schema import validate_tools

CATALOG = ROOT / "data/tools.json"
QUEUE = ROOT / "data/research/overnight-tool-candidates.json"
OUTPUT = ROOT / "data/research/catalog-worker-records.json"


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    records = build_review_records(queue.get("items", []), catalog)
    errors = validate_tools(records)
    if errors:
        raise SystemExit("Review record validation failed:\n" + "\n".join(errors[:30]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(records)} non-public AtlasFind review records at {OUTPUT}")


if __name__ == "__main__":
    main()
