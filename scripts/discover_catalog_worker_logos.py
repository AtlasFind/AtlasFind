"""Discover official logo candidates for review records; never publishes them."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.catalog_worker_logo_service import discover_worker_logo_candidates

RECORDS = ROOT / "data/research/catalog-worker-records.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20, help="0 means all records")
    args = parser.parse_args()
    records = json.loads(RECORDS.read_text(encoding="utf-8"))
    completed = 0
    for index, record in enumerate(records):
        existing = record.get("research_metadata", {}).get("logo_review", {})
        if existing.get("status") == "candidates_found":
            continue
        if args.limit and completed >= args.limit:
            break
        review = discover_worker_logo_candidates(record)
        records[index].setdefault("research_metadata", {})["logo_review"] = review
        RECORDS.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        completed += 1
    print(f"Logo discovery completed for {completed} records; 0 logos published")


if __name__ == "__main__":
    main()
