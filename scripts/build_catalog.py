"""Build compatibility files and deterministic indexes from modular catalog sources."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog.loader import load_catalog


def main() -> None:
    tools = load_catalog(validate=True)
    compatibility_path = ROOT / "data" / "tools.json"
    index_path = ROOT / "data" / "indexes" / "tools.index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    compatibility_path.write_text(
        json.dumps(tools, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    index = {
        "schema_version": "1.0.2",
        "record_count": len(tools),
        "by_slug": {tool["slug"]: tool["id"] for tool in tools},
        "by_id": {str(tool["id"]): tool["slug"] for tool in tools},
        "published_slugs": [
            tool["slug"] for tool in tools
            if tool.get("publication_status", "published") == "published"
        ],
    }
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Catalog build successful: {len(tools)} records")
    print(f"Compatibility JSON: {compatibility_path}")
    print(f"Search index: {index_path}")


if __name__ == "__main__":
    main()
