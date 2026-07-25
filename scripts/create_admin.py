import getpass
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from werkzeug.security import generate_password_hash
from database import apply_migrations
from repositories.admin import create_admin

if __name__ == '__main__':
    apply_migrations()
    username = input('Admin username: ').strip()
    password = getpass.getpass('Admin password: ')
    confirm = getpass.getpass('Confirm password: ')
    if not username or len(password) < 10 or password != confirm:
        raise SystemExit('Username is required, passwords must match, and password must be at least 10 characters.')
    try:
        admin_id = create_admin(username, generate_password_hash(password))
    except Exception as exc:
        raise SystemExit(f'Could not create admin: {exc}')
    print(f'Admin created with id {admin_id}.')
