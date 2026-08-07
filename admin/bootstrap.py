"""One-time production admin bootstrap for hosts without shell access."""
import os

from werkzeug.security import generate_password_hash

from database import DATABASE_PATH
from repositories.admin import admin_user_count, create_admin


def bootstrap_admin_from_environment(production, environ=None, database_path=DATABASE_PATH):
    """Create the first admin only when explicitly enabled and none exists.

    The host must delete the password environment variable after the account is
    created. The routine intentionally never updates or resets existing users.
    """
    environ = os.environ if environ is None else environ
    if not production or environ.get("ATLASFIND_BOOTSTRAP_ADMIN_ENABLED") != "1":
        return "disabled"
    if admin_user_count(database_path):
        return "already_exists"

    username = environ.get("ATLASFIND_BOOTSTRAP_ADMIN_USERNAME", "").strip()
    password = environ.get("ATLASFIND_BOOTSTRAP_ADMIN_PASSWORD", "")
    if not username or len(username) > 120:
        return "invalid_username"
    if len(password) < 12:
        return "invalid_password"

    create_admin(username, generate_password_hash(password), path=database_path)
    return "created"
