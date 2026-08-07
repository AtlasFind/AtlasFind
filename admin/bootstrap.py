"""One-time production admin bootstrap for hosts without shell access."""
import os

from werkzeug.security import generate_password_hash

from database import DATABASE_PATH
from repositories.admin import admin_user_count, create_admin, reset_admin_password


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


def reset_admin_password_from_environment(production, environ=None, database_path=DATABASE_PATH):
    """Create or recover one named admin when explicitly enabled for recovery."""
    environ = os.environ if environ is None else environ
    if not production or environ.get("ATLASFIND_ADMIN_RESET_ENABLED") != "1":
        return "disabled"
    username = environ.get("ATLASFIND_ADMIN_RESET_USERNAME", "").strip()
    password = environ.get("ATLASFIND_ADMIN_RESET_PASSWORD", "")
    if not username or len(username) > 120:
        return "invalid_username"
    if len(password) < 12:
        return "invalid_password"
    password_hash = generate_password_hash(password)
    if reset_admin_password(username, password_hash, path=database_path):
        return "reset"
    create_admin(username, password_hash, path=database_path)
    return "created"
