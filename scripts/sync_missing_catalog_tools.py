"""Non-destructively append missing published catalog records to SQLite."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalog.loader import load_published_catalog
from database import DATABASE_PATH, apply_migrations, connect_database
from repositories.tool_writer import save_tool


def main() -> None:
    apply_migrations()
    catalog = load_published_catalog(validate=True)
    with connect_database(DATABASE_PATH) as connection:
        existing = {row["slug"] for row in connection.execute("SELECT slug FROM tools").fetchall()}
    missing = [tool for tool in catalog if tool["slug"] not in existing]
    for tool in sorted(missing, key=lambda item: item["id"]):
        save_tool(tool, status="published")
    print(f"SQLite catalog sync complete: added={len(missing)}, total_expected={len(catalog)}")


if __name__ == "__main__":
    main()
