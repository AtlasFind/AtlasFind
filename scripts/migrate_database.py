import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database import apply_migrations

if __name__ == '__main__':
    applied = apply_migrations()
    if applied:
        print('Applied migrations: ' + ', '.join(applied))
    else:
        print('Database is already up to date.')
