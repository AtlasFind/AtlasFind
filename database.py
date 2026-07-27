import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "atlasfind.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
MIGRATIONS_DIR = DATABASE_DIR / "migrations"


def connect_database(path=DATABASE_PATH):
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA cache_size = -20000")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


@contextmanager
def transaction(path=DATABASE_PATH):
    connection = connect_database(path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT OR IGNORE INTO schema_migrations(name) VALUES (?)",
            ("001_initial_schema",),
        )


def _applied_migrations(connection):
    rows = connection.execute("SELECT name FROM schema_migrations").fetchall()
    return {row["name"] for row in rows}


def apply_migrations(path=DATABASE_PATH):
    initialize_database(path)
    applied = []
    with transaction(path) as connection:
        completed = _applied_migrations(connection)
        for migration_path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            name = migration_path.stem
            if name in completed:
                continue
            connection.executescript(migration_path.read_text(encoding="utf-8"))
            connection.execute("INSERT INTO schema_migrations(name) VALUES (?)", (name,))
            applied.append(name)
    return applied
