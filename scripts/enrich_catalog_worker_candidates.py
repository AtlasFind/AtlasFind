"""Enrich queued candidates from official repository evidence, without publishing."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.catalog_worker_enrichment_service import enrich_candidate, utc_now

QUEUE = ROOT / "data/research/overnight-tool-candidates.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=25, help="0 means all queued candidates")
    parser.add_argument("--pause", type=float, default=1.5)
    args = parser.parse_args()
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    completed = 0
    for index, candidate in enumerate(queue.get("items", [])):
        if candidate.get("enrichment_status") == "evidence_collected":
            continue
        if args.limit and completed >= args.limit:
            break
        queue["items"][index] = enrich_candidate(candidate)
        queue["updated_at"] = utc_now()
        QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        completed += 1
        time.sleep(max(0, args.pause))
    print(f"Enriched {completed} candidates; nothing was published")


if __name__ == "__main__":
    main()
