"""Create a safe timestamped SQLite backup and retain a bounded history."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from database import DATABASE_PATH

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = DATABASE_PATH.parent / "backups"


def create_backup(retain: int = 7) -> Path | None:
    if not DATABASE_PATH.exists() or DATABASE_PATH.stat().st_size == 0:
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = BACKUP_DIR / f"atlasfind-{stamp}.db"
    with sqlite3.connect(DATABASE_PATH) as source, sqlite3.connect(destination) as target:
        source.backup(target)
        row = target.execute("PRAGMA integrity_check").fetchone()
        if not row or row[0] != "ok":
            destination.unlink(missing_ok=True)
            raise RuntimeError("SQLite backup integrity check failed")
    backups = sorted(BACKUP_DIR.glob("atlasfind-*.db"), reverse=True)
    for old in backups[max(1, retain):]:
        old.unlink(missing_ok=True)
    return destination


if __name__ == "__main__":
    result = create_backup()
    print(f"Backup created: {result}" if result else "No database exists yet; backup skipped.")
