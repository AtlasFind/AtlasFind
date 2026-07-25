from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from content_schema import validate_articles


def main() -> int:
    articles = json.loads((BASE_DIR / "data" / "articles.json").read_text(encoding="utf-8"))
    tools = json.loads((BASE_DIR / "data" / "tools.json").read_text(encoding="utf-8"))
    errors = validate_articles(articles, {tool.get("slug") for tool in tools})
    if errors:
        print("Content validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Validation successful: {len(articles)} articles satisfy the v0.5.0 content schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
