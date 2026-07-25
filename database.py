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
