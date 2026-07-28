from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []
WARNINGS: list[str] = []


def require(path: str) -> Path:
    target = ROOT / path
    if not target.exists():
        ERRORS.append(f"Missing required file: {path}")
    return target


for required in (
    "app.py", "wsgi.py", "render.yaml", "requirements.txt", ".env.example",
    "database/atlasfind.db", "templates/base.html", "templates/404.html",
    "templates/error.html", "translations/tr.json", "translations/en.json",
    "static/css/style.css", "static/js/main.js", "static/images/favicon.svg",
    "README.md", "CHANGELOG.md", "ROADMAP.md",
):
    require(required)

app_text = (ROOT / "app.py").read_text(encoding="utf-8")
if 'APP_VERSION = "1.0.0"' not in app_text:
    ERRORS.append("APP_VERSION is not 1.0.0")

required_routes = (
    "/", "/<locale>/", "/tools", "/<locale>/tools", "/categories",
    "/<locale>/categories", "/guides", "/<locale>/guides", "/recommend",
    "/<locale>/recommend", "/compare", "/<locale>/compare", "/health",
    "/ready", "/robots.txt", "/sitemap.xml", "/privacy", "/terms",
    "/cookies", "/contact",
)
for route in required_routes:
    marker = f'@app.route("{route}"'
    if marker not in app_text:
        ERRORS.append(f"Missing route declaration: {route}")

for status in (400, 413, 429, 500, 404):
    if f"@app.errorhandler({status})" not in app_text:
        ERRORS.append(f"Missing error handler: {status}")

if "ATLASFIND_CONTACT_EMAIL" not in app_text:
    ERRORS.append("Contact email environment variable is not wired")
if '"/privacy"' not in app_text or '"/contact"' not in app_text:
    ERRORS.append("Legal/contact URLs are missing from sitemap source list")
if "Disallow: /admin/" not in app_text or "Disallow: /api/" not in app_text:
    ERRORS.append("robots.txt rules are incomplete")

translations = {}
for locale in ("tr", "en"):
    path = ROOT / "translations" / f"{locale}.json"
    translations[locale] = json.loads(path.read_text(encoding="utf-8"))

if set(translations["tr"]) != set(translations["en"]):
    missing_tr = sorted(set(translations["en"]) - set(translations["tr"]))
    missing_en = sorted(set(translations["tr"]) - set(translations["en"]))
    ERRORS.append(f"Translation key mismatch; missing TR={missing_tr[:10]}, missing EN={missing_en[:10]}")

required_keys = {
    "footer.privacy", "footer.terms", "footer.cookies", "footer.contact",
    "cookie.message", "cookie.accept", "common.home", "common.page_not_found",
    "errors.400.title", "errors.413.title", "errors.429.title", "errors.500.title",
    "errors.reference", "errors.search_placeholder", "guides.seo_title",
    "recommend.seo_title",
}
for locale, data in translations.items():
    for key in required_keys:
        if not str(data.get(key, "")).strip():
            ERRORS.append(f"{locale} missing translation: {key}")

# Reject known regressions in templates.
template_text = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "templates").rglob("*.html"))
if re.search(r"\bonload\s*=", template_text, flags=re.I):
    ERRORS.append("Inline onload handler found in templates")
if "Search tools instead" in (ROOT / "templates/404.html").read_text(encoding="utf-8"):
    ERRORS.append("404 search placeholder is still hard-coded in English")

# Check local static references used by templates.
for match in re.finditer(r"filename=['\"]([^'\"]+)['\"]", template_text):
    static_path = ROOT / "static" / match.group(1)
    if not static_path.exists():
        ERRORS.append(f"Template references missing static asset: static/{match.group(1)}")

# Catalog/database integrity.
with sqlite3.connect(ROOT / "database" / "atlasfind.db") as connection:
    tool_count = connection.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
    translation_count = connection.execute("SELECT COUNT(*) FROM tool_translations").fetchone()[0]
    category_count = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    orphan_count = connection.execute(
        "SELECT COUNT(*) FROM tools t LEFT JOIN categories c ON c.id=t.category_id WHERE c.id IS NULL"
    ).fetchone()[0]
if tool_count != 600:
    ERRORS.append(f"SQLite tool count is {tool_count}, expected 600")
if translation_count < 1200:
    ERRORS.append(f"SQLite translation count is {translation_count}, expected at least 1200")
if category_count != 18:
    ERRORS.append(f"SQLite category count is {category_count}, expected 18")
if orphan_count:
    ERRORS.append(f"Tools with missing category relation: {orphan_count}")

# Optional real route test when dependencies are installed.
runtime_checked = False
try:
    sys.path.insert(0, str(ROOT))
    from app import app, load_articles, load_tools  # type: ignore

    runtime_checked = True
    sample_slugs = [tool["slug"] for tool in load_tools("en")[:10]]
    article_slugs = [article["slug"] for article in load_articles("en")[:5]]
    public_paths = [
        "/tr/", "/en/", "/tr/tools", "/en/tools", "/tr/categories", "/en/categories",
        "/tr/guides", "/en/guides", "/tr/recommend", "/en/recommend",
        "/tr/compare", "/en/compare", "/health", "/ready", "/robots.txt",
        "/sitemap.xml", "/tr/privacy", "/en/privacy", "/tr/terms", "/en/terms",
        "/tr/cookies", "/en/cookies", "/tr/contact", "/en/contact",
        "/tr/this-page-does-not-exist",
    ]
    public_paths += [f"/tr/tools/{slug}" for slug in sample_slugs]
    public_paths += [f"/en/tools/{slug}" for slug in sample_slugs]
    public_paths += [f"/tr/guides/{slug}" for slug in article_slugs]
    expected = {"/tr/this-page-does-not-exist": 404}
    with app.test_client() as client:
        for path in public_paths:
            response = client.get(path)
            wanted = expected.get(path, 200)
            if response.status_code != wanted:
                ERRORS.append(f"Runtime route failed: {path} returned {response.status_code}, expected {wanted}")
        compare = client.get("/tr/compare?tools=chatgpt&tools=chatgpt&tools=blender")
        if compare.status_code != 200:
            ERRORS.append(f"Duplicate compare runtime test returned {compare.status_code}")
except ModuleNotFoundError as exc:
    WARNINGS.append(f"Runtime route test skipped because dependency is unavailable: {exc}")
except Exception as exc:
    ERRORS.append(f"Runtime route test crashed: {type(exc).__name__}: {exc}")

if ERRORS:
    print("v1.0.0 release validation failed:")
    for error in ERRORS:
        print(f"- {error}")
    for warning in WARNINGS:
        print(f"Warning: {warning}")
    raise SystemExit(1)

print("v1.0.0 release validation successful.")
print(f"- SQLite tools: {tool_count}")
print(f"- SQLite translations: {translation_count}")
print(f"- Categories: {category_count}")
print(f"- Runtime route test: {'completed' if runtime_checked else 'skipped'}")
for warning in WARNINGS:
    print(f"Warning: {warning}")
