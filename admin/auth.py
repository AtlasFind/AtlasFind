import hmac
import secrets
import time
from functools import wraps

from flask import abort, current_app, redirect, request, session, url_for

from repositories.admin import get_admin_by_id

SESSION_IDLE_SECONDS = 30 * 60


def current_admin():
    admin_id = session.get("admin_user_id")
    if not admin_id:
        return None
    now = int(time.time())
    last_activity = int(session.get("last_admin_activity", now))
    if now - last_activity > SESSION_IDLE_SECONDS:
        session.clear()
        return None
    session["last_admin_activity"] = now
    return get_admin_by_id(admin_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_admin():
            return redirect(url_for("admin.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def validate_csrf():
    supplied = request.form.get("csrf_token", "")
    expected = session.get("csrf_token", "")
    if not supplied or not expected or not hmac.compare_digest(supplied, expected):
        abort(400, "Invalid CSRF token")
