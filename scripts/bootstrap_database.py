"""Create, migrate and seed the AtlasFind database when deployment storage is empty."""
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import DATABASE_PATH, apply_migrations
import json


def tool_count() -> int:
    if not DATABASE_PATH.exists():
        return 0
    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            row = connection.execute("SELECT COUNT(*) FROM tools").fetchone()
            return int(row[0]) if row else 0
    except sqlite3.Error:
        return 0


def expected_tool_count() -> int:
    source = ROOT / "data" / "tools.json"
    try:
        return len(json.loads(source.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return 0


def main() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    expected = expected_tool_count()

    if tool_count() < expected:
        from scripts.migrate_json_to_sqlite import migrate
        print(f"Catalog is missing or outdated; rebuilding {DATABASE_PATH} from JSON sources.")
        migrate(reset=True)

    apply_migrations()
    from scripts.sync_catalog_translations import main as sync_catalog_translations
    sync_catalog_translations()
    count = tool_count()
    if count == 0:
        raise RuntimeError("Database bootstrap completed without any tools.")
    print(f"Database ready: {DATABASE_PATH} ({count} tools)")


if __name__ == "__main__":
    main()
