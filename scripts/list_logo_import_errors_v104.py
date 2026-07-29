from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="List current AtlasFind logo import failures.")
    parser.add_argument("--queue", default="data/branding/logo-queue.json")
    args = parser.parse_args()

    payload = json.loads((ROOT / args.queue).read_text(encoding="utf-8"))
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    failures = [item for item in items if isinstance(item, dict) and item.get("status") == "error"]

    print(f"Import/discovery error tools: {len(failures)}")
    for item in failures:
        print(f"{item.get('slug')} -> {item.get('last_error') or item.get('error') or 'No error message'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
