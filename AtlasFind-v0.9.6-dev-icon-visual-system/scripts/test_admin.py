import sqlite3
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database import apply_migrations, connect_database

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as temp:
        db = Path(temp) / 'admin-test.db'
        apply_migrations(db)
        with connect_database(db) as connection:
            tables = {row['name'] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required = {'admin_users','admin_login_attempts','admin_audit_logs'}
            missing = required - tables
            if missing:
                raise SystemExit('Missing admin tables: ' + ', '.join(sorted(missing)))
            tool_columns = {row['name'] for row in connection.execute('PRAGMA table_info(tools)')}
            if not {'status','archived_at','published_at','image_path'} <= tool_columns:
                raise SystemExit('Admin tool columns are incomplete.')
        print('Admin database tests successful.')
