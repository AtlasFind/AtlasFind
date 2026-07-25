"""Validate every current and future AtlasFind tool entry."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from tool_schema import validate_tools  # noqa: E402

DATA_FILE = BASE_DIR / "data" / "tools.json"


def main() -> int:
    try:
        tools = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Dataset could not be read: {error}")
        return 1

    errors = validate_tools(tools)
    if errors:
        print("AtlasFind dataset validation failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation successful: {len(tools)} tool entries satisfy the v0.2.2 schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
