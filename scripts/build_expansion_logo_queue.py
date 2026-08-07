"""Create an isolated logo-discovery queue for the 100 staged expansion records."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data" / "research" / "catalog-expansion-records.json"
OUTPUT = ROOT / "data" / "research" / "catalog-expansion-logo-queue.json"


def main() -> None:
    records = json.loads(RECORDS.read_text(encoding="utf-8"))
    items = [{
        "tool_id": tool["id"],
        "slug": tool["slug"],
        "name": tool["name"],
        "official_url": tool["website"],
        "status": "pending",
        "attempts": 0,
        "candidates": [],
        "last_error": None,
        "updated_at": None,
    } for tool in records]
    payload = {"version": 1, "generated_at": datetime.now(timezone.utc).isoformat(), "total": len(items), "items": items}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Expansion logo queue created: {len(items)} tools")


if __name__ == "__main__":
    main()
