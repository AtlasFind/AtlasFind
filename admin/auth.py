import hmac
import secrets
from functools import wraps

from flask import abort, redirect, request, session, url_for

from repositories.admin import get_admin_by_id


def current_admin():
    admin_id = session.get("admin_user_id")
    return get_admin_by_id(admin_id) if admin_id else None


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
