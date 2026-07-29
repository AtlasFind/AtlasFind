from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "branding" / "logo-queue.json"


def _load_items(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit("Queue not found. Run build_logo_queue_v104.py first.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise SystemExit("Invalid queue format: items must be a list.")
    return [item for item in items if isinstance(item, dict)]


def main() -> int:
    items = _load_items(QUEUE_PATH)
    statuses = Counter(item.get("status", "unknown") for item in items)
    candidate_statuses: Counter[str] = Counter()
    tools_with_candidates = 0
    approved_waiting = 0
    approved_error = 0

    for item in items:
        candidates = [c for c in (item.get("candidates") or []) if isinstance(c, dict)]
        if candidates:
            tools_with_candidates += 1
        has_approved = False
        for candidate in candidates:
            state = candidate.get("review_status", "unknown")
            candidate_statuses[state] += 1
            has_approved = has_approved or state == "approved"
        if has_approved and item.get("status") == "approved":
            approved_waiting += 1
        if has_approved and item.get("status") == "error":
            approved_error += 1

    print("Total queue:", len(items))
    print("Tools with candidates:", tools_with_candidates)
    for key, value in sorted(statuses.items()):
        print(f"{key}: {value}")
    for key, value in sorted(candidate_statuses.items()):
        print(f"candidate_{key}: {value}")
    print("Imported tools:", statuses.get("imported", 0))
    print("Approved tools waiting import:", approved_waiting)
    print("Approved tools with import error:", approved_error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
