"""AtlasFind v1.0.0 release gate: static, database, security and route checks."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        ERRORS.append(message)


app_text = (ROOT / "app.py").read_text(encoding="utf-8")
security_text = (ROOT / "security.py").read_text(encoding="utf-8")
base_text = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
render_text = (ROOT / "render.yaml").read_text(encoding="utf-8")

check('APP_VERSION = "1.0.0"' in app_text, "APP_VERSION must be 1.0.0")
check("https://atlasfind.org" in render_text, "Render site URL must use atlasfind.org")
check("atlasfindd@gmail.com" in render_text, "Render contact email is missing")
check("ATLASFIND_ALLOWED_HOSTS" in render_text, "Production host allow-list is missing")
check("validate_request_host" in security_text, "Host-header validation is missing")
check("ProxyFix" in security_text, "Trusted proxy handling is missing")
check("Content-Security-Policy" in security_text, "CSP header is missing")
check("'unsafe-inline'; script-src" not in security_text, "CSP still allows unsafe inline scripts")
check('nonce="{{ csp_nonce }}"' in base_text, "CSP nonce is not wired into base template")
check("enforce_api_rate_limit" in security_text, "API rate limiting is missing")
check("@app.errorhandler(405)" in app_text, "405 error handler is missing")
check("PRAGMA quick_check" in app_text, "Readiness endpoint lacks database integrity check")
check((ROOT / "scripts" / "backup_database.py").exists(), "Database backup script is missing")

for locale in ("tr", "en"):
    data = json.loads((ROOT / "translations" / f"{locale}.json").read_text(encoding="utf-8"))
    check(bool(data.get("errors.405.title")), f"{locale} 405 title translation missing")
    check(bool(data.get("errors.405.text")), f"{locale} 405 text translation missing")

with sqlite3.connect(ROOT / "database" / "atlasfind.db") as connection:
    integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
    tools = connection.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
    translations = connection.execute("SELECT COUNT(*) FROM tool_translations").fetchone()[0]
    categories = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
check(integrity == "ok", f"SQLite quick_check failed: {integrity}")
check(tools == 600, f"Expected 600 tools, found {tools}")
check(translations >= 1200, f"Expected at least 1200 translations, found {translations}")
check(categories == 18, f"Expected 18 categories, found {categories}")

# Run the existing static validators in isolated subprocesses.
validators = [
    "validate_tools.py", "validate_translations.py", "validate_security.py",
    "validate_public_beta.py", "validate_catalog_v092.py",
    "validate_search_pagination_v093.py", "validate_taxonomy_v094.py",
    "validate_tool_quality_v095.py", "validate_icons_v096.py",
    "validate_tool_detail_v097.py", "validate_compare_recommendations_v098.py",
    "validate_public_beta_v099.py",
]
for validator in validators:
    path = ROOT / "scripts" / validator
    if not path.exists():
        ERRORS.append(f"Missing validator: {validator}")
        continue
    result = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        ERRORS.append(f"{validator} failed: {(result.stdout + result.stderr).strip()[-1200:]}")

# Real Flask route and header tests. Packaging environments may explicitly skip them; production candidates must not.
skip_runtime = os.environ.get("ATLASFIND_SKIP_RUNTIME_TESTS", "0") == "1"
try:
    if skip_runtime:
        raise ModuleNotFoundError("runtime tests explicitly skipped by ATLASFIND_SKIP_RUNTIME_TESTS=1")
    os.environ.setdefault("ATLASFIND_ENV", "development")
    os.environ.setdefault("ATLASFIND_ALLOWED_HOSTS", "localhost")
    sys.path.insert(0, str(ROOT))
    from app import app  # type: ignore

    with app.test_client() as client:
        public = [
            "/tr/", "/en/", "/tr/tools", "/en/tools", "/tr/categories",
            "/en/categories", "/tr/compare", "/en/compare", "/tr/recommend",
            "/en/recommend", "/tr/guides", "/en/guides", "/robots.txt",
            "/sitemap.xml", "/health", "/ready", "/tr/privacy", "/en/contact",
            "/tr/tools/chatgpt", "/en/tools/steam",
        ]
        for path in public:
            response = client.get(path, headers={"Host": "localhost"})
            check(response.status_code == 200, f"Route {path} returned {response.status_code}")
            check("Content-Security-Policy" in response.headers, f"CSP missing on {path}")
            check("X-Request-ID" in response.headers, f"Request ID missing on {path}")
        duplicate = client.get(
            "/tr/compare?tools=chatgpt&tools=chatgpt&tools=blender",
            headers={"Host": "localhost"},
        )
        check(duplicate.status_code == 200, "Duplicate comparison request failed")
        missing = client.get("/tr/not-a-real-page", headers={"Host": "localhost"})
        check(missing.status_code == 404, "Localized 404 route failed")
        rejected = client.get("/health", headers={"Host": "evil.example"})
        check(rejected.status_code == 400, "Unexpected Host header was not rejected")
        trace = client.open("/health", method="TRACE", headers={"Host": "localhost"})
        check(trace.status_code == 405, "TRACE method was not rejected")
except ModuleNotFoundError as exc:
    if skip_runtime:
        print(f"Warning: Flask runtime tests skipped: {exc}")
    else:
        ERRORS.append(f"Flask runtime tests could not run: {exc}")
except Exception as exc:
    ERRORS.append(f"Flask runtime tests crashed: {type(exc).__name__}: {exc}")

if ERRORS:
    print("AtlasFind v1.0.0 release validation failed:")
    for error in ERRORS:
        print(f"- {error}")
    raise SystemExit(1)

print("AtlasFind v1.0.0 release validation successful.")
print(f"- SQLite tools: {tools}")
print(f"- SQLite translations: {translations}")
print(f"- Categories: {categories}")
print(f"- Runtime routes and security headers: {'skipped' if skip_runtime else 'successful'}")
