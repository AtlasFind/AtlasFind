"""Apply the reviewed official-source map to the staged expansion queue."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "research" / "catalog-expansion-700.json"
SOURCES_PATH = ROOT / "data" / "research" / "catalog-expansion-official-urls.json"


def main() -> None:
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    candidates = queue["candidates"]
    for candidate in candidates:
        slug = candidate["slug"]
        candidate["official_url"] = sources[slug]
        candidate["verification_status"] = "official_source_confirmed"
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Applied official sources to {len(candidates)} candidates")


if __name__ == "__main__":
    main()
