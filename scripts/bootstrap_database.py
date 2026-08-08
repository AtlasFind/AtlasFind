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
    try:
        from catalog.loader import load_catalog
        return len(load_catalog(validate=True))
    except (OSError, ValueError, TypeError):
        return 0


def main() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    expected = expected_tool_count()
    existing = tool_count()

    if existing:
        from scripts.backup_database import create_backup
        backup = create_backup()
        if backup:
            print(f"Pre-start backup created: {backup}")

    if existing == 0:
        from scripts.migrate_json_to_sqlite import migrate
        print(f"Catalog is empty; seeding {DATABASE_PATH} from JSON sources.")
        migrate(reset=True)
    elif expected and existing < expected:
        from scripts.sync_missing_catalog_tools import main as sync_missing_catalog_tools
        print(f"Catalog upgrade detected: {existing} -> {expected}; appending missing published tools.")
        sync_missing_catalog_tools()

    apply_migrations()
    from scripts.sync_catalog_translations import main as sync_catalog_translations
    sync_catalog_translations()
    from scripts.sync_expansion_translations import main as sync_expansion_translations
    sync_expansion_translations()
    from scripts.sync_complete_turkish_translations import main as sync_complete_turkish_translations
    sync_complete_turkish_translations()
    from scripts.sync_complete_turkish_articles import main as sync_complete_turkish_articles
    sync_complete_turkish_articles()
    count = tool_count()
    if count == 0:
        raise RuntimeError("Database bootstrap completed without any tools.")
    print(f"Database ready: {DATABASE_PATH} ({count} tools)")


if __name__ == "__main__":
    main()
