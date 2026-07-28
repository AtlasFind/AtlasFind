"""Security and production helpers for AtlasFind.

Uses only the Python standard library so v0.7.1 does not add a dependency merely
for fashionable middleware-shaped comfort.
"""
from __future__ import annotations

import logging
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import abort, current_app, request

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
PRODUCTION_ENVIRONMENTS = {"production", "prod"}


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def configure_security(app) -> None:
    environment = os.environ.get("ATLASFIND_ENV", "development").strip().lower()
    production = environment in PRODUCTION_ENVIRONMENTS
    secret = os.environ.get("ATLASFIND_SECRET_KEY", "").strip()

    if production and (len(secret) < 32 or secret == "development-only-change-me"):
        raise RuntimeError(
            "ATLASFIND_SECRET_KEY must be a unique value of at least 32 characters in production."
        )
    if not secret:
        secret = "development-only-change-me"

    https_enabled = env_bool("ATLASFIND_HTTPS", production)
    app.config.update(
        ENVIRONMENT=environment,
        PRODUCTION=production,
        SECRET_KEY=secret,
        SESSION_COOKIE_NAME="atlasfind_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=https_enabled,
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        TRUST_PROXY_HEADERS=env_bool("ATLASFIND_TRUST_PROXY", False),
        ADMIN_LOGIN_LIMIT=int(os.environ.get("ATLASFIND_LOGIN_LIMIT", "5")),
        ADMIN_LOGIN_WINDOW=int(os.environ.get("ATLASFIND_LOGIN_WINDOW", "900")),
    )


def configure_logging(app) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        LOG_DIR / "atlasfind.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def client_ip() -> str:
    """Return a client address without blindly trusting spoofable proxy headers."""
    if current_app.config.get("TRUST_PROXY_HEADERS"):
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()[:120]
    return (request.remote_addr or "unknown")[:120]


class SlidingWindowLimiter:
    def __init__(self):
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            if not events:
                self._events.pop(key, None)
            return True


login_limiter = SlidingWindowLimiter()


def enforce_admin_login_rate_limit(username: str) -> None:
    limit = current_app.config["ADMIN_LOGIN_LIMIT"]
    window = current_app.config["ADMIN_LOGIN_WINDOW"]
    identity = username.strip().lower() or "<empty>"
    ip = client_ip()
    if not login_limiter.allow(f"login-ip:{ip}", limit * 2, window):
        current_app.logger.warning("admin_login_rate_limited ip=%s", ip)
        abort(429)
    if not login_limiter.allow(f"login-user:{identity}:{ip}", limit, window):
        current_app.logger.warning("admin_login_rate_limited username=%r ip=%s", identity, ip)
        abort(429)


def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    # Inline styles/scripts still exist in current templates. v0.7.1 keeps a compatible
    # CSP rather than breaking rendering and pretending the breakage is security.
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
        "object-src 'none'; img-src 'self' data: https:; font-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; "
        "connect-src 'self'",
    )
    if current_app.config.get("SESSION_COOKIE_SECURE"):
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    if request.path.startswith("/admin"):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Pragma"] = "no-cache"
    return response


def new_request_id() -> str:
    return secrets.token_hex(8)
