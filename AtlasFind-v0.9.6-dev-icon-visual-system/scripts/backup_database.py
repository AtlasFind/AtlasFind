import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database import DATABASE_PATH


def main():
    if not DATABASE_PATH.exists():
        raise SystemExit("Database not found. Run the migration first.")
    backup_dir = ROOT / "backups"
    backup_dir.mkdir(exist_ok=True)
    target = backup_dir / f"atlasfind-{datetime.now():%Y-%m-%d-%H%M%S}.db"
    with sqlite3.connect(DATABASE_PATH) as source, sqlite3.connect(target) as destination:
        source.backup(destination)
    print(f"Backup created: {target}")

if __name__ == "__main__": main()
