"""Create a deterministic editorial work queue without inventing product facts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog.loader import load_catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=25)
    parser.add_argument("--output", default="data/review/verification-batch.json")
    args = parser.parse_args()
    if args.size < 1 or args.size > 500:
        raise SystemExit("--size must be between 1 and 500")

    tools = load_catalog(validate=True)
    pending = [
        tool for tool in tools
        if tool.get("verification", {}).get("status") != "verified" or not tool.get("source_references")
    ]
    pending.sort(key=lambda item: (-int(item.get("popularity_score", 0)), str(item.get("name", "")).casefold()))
    selected = pending[: args.size]
    queue = []
    for tool in selected:
        queue.append({
            "id": tool.get("id"),
            "slug": tool.get("slug"),
            "name": tool.get("name"),
            "official_website": tool.get("website"),
            "required_checks": [
                "identity",
                "company",
                "description",
                "category",
                "platforms",
                "pricing",
                "privacy-security",
                "official-links",
                "logo-rights-and-source",
            ],
            "status": "not-started",
            "reviewer_notes": "",
        })

    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created verification queue with {len(queue)} records: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
