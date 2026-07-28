# AtlasFind

**Find the right software. Faster.**

AtlasFind is a Flask-based software discovery, recommendation, comparison and editorial guide platform.

## Current Version

v0.9.9-dev

## Current Features

- Typo-tolerant smart search and transparent recommendations
- Advanced filters, categories, collections and comparisons
- Data-driven guides with freshness and change history
- SQLite repository layer with migration and backup scripts
- Secure administrator login, drafts, publishing, archiving and audit logs
- Tool/article editing, taxonomy management and validated bulk import

## Run Locally

```powershell
pip install -r requirements.txt
py scripts/migrate_database.py
py app.py
```

Open `http://127.0.0.1:5000`.

## Create the first administrator

Set a strong application secret before running the site:

```powershell
$env:ATLASFIND_SECRET_KEY = "replace-this-with-a-long-random-secret"
py scripts/create_admin.py
```

Then open `http://127.0.0.1:5000/admin/login`.

For HTTPS deployment set `ATLASFIND_HTTPS=1` so the session cookie is marked secure.

## Validation

```powershell
py scripts/validate_tools.py
py scripts/validate_content.py
py scripts/validate_freshness.py
py scripts/verify_migration.py
py scripts/test_search.py
py scripts/test_recommendations.py
py scripts/test_admin.py
py scripts/validate_public_beta_v099.py
```

## SQLite and backups

JSON files remain migration and rollback sources. The application reads published tools and guides from SQLite.

```powershell
py scripts/migrate_json_to_sqlite.py
py scripts/migrate_database.py
py scripts/verify_migration.py
py scripts/backup_database.py
```

Draft and archived records are excluded from public routes. Administrator changes are recorded in the audit log.


## Technical SEO checks

```powershell
py scripts/validate_seo.py
py scripts/check_links.py
```

Set `ATLASFIND_SITE_URL` to the production origin before deployment.


## Multilingual URLs

AtlasFind supports English and Turkish public routes:

```text
/en/
/tr/
/en/tools/gimp
/tr/tools/gimp
```

Interface translations live in `translations/en.json` and `translations/tr.json`. Missing Turkish content safely falls back to English. Validate translations with:

```powershell
py scripts/validate_translations.py
```


### v0.7.0 Turkish content completion
- Added complete Turkish content records for all 100 published tools, including descriptions, categories, tags, pros, cons, target users, requirements, pricing notes, verification notes and history labels.


## Performance checks

```powershell
py scripts/migrate_database.py
py scripts/benchmark_performance.py
```

The benchmark requires the project virtual environment and Flask dependencies.


## Production security

Copy `.env.example` values into the environment used by the server. AtlasFind does not automatically read `.env`, which avoids silently depending on an extra package.

Generate a strong secret locally:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Production example:

```powershell
$env:ATLASFIND_ENV = "production"
$env:ATLASFIND_SECRET_KEY = "paste-the-generated-secret-here"
$env:ATLASFIND_HTTPS = "1"
$env:ATLASFIND_SITE_URL = "https://atlasfind.com"
$env:ATLASFIND_DEBUG = "0"
py app.py
```

Only set `ATLASFIND_TRUST_PROXY=1` when AtlasFind is behind a trusted reverse proxy that overwrites forwarding headers. Validate the security wiring with:

```powershell
py scripts/validate_security.py
```

The built-in Flask server remains suitable for local testing. A production deployment should run behind a production WSGI server and HTTPS reverse proxy.

## Production deployment (v0.9.0)

AtlasFind includes a WSGI entry point, Gunicorn startup, Dockerfile, Render Blueprint, persistent SQLite path support, automatic first-deploy seeding, and health checks.

```powershell
py scripts\validate_deployment.py
py scripts\bootstrap_database.py
```

Production starts with:

```text
python scripts/start_production.py
```

See `docs/DEPLOYMENT.md` for environment variables, domain setup, HTTPS, persistent storage, and backup steps.


## Public beta pages
`/<locale>/privacy`, `terms`, `cookies` and `contact` provide bilingual launch information.


## v0.9.0 catalog

The bundled catalog contains 600 tools. Validate it with `py scripts/validate_catalog_v090.py`. Contact email is configured with `ATLASFIND_CONTACT_EMAIL` and defaults to `atlasfindd@gmail.com`.


## v0.9.2 Professional Catalog Experience

The current development version upgrades `/tr/tools` and `/en/tools` into a professional directory experience without replacing the existing Flask, SQLite or localization architecture.

Included in this development package:

- collapsible category, subcategory, pricing, platform, rating and feature filters
- active filter chips and a clear-all action
- filter-safe previous/next pagination URLs
- grid and list views with a saved browser preference
- mobile filter panel and narrow-screen layout protections
- improved card hierarchy, platform summaries and RAM fallback text
- complete Turkish and English catalog interface strings

Validation command:

```powershell
py scripts\validate_catalog_v092.py
```

Real route checks must also be performed with Flask running locally before release approval.


## v0.9.3 Development Status

The catalog now supports integrated search, typo-tolerant ranking, Turkish character normalization, 24-item pages, numbered pagination, preserved query parameters, stable sorting and duplicate-result protection. This remains a development build until browser and live Flask tests are approved.

## v0.9.4 category system

AtlasFind uses 18 canonical bilingual categories defined in `taxonomy.py`. Legacy category names are migrated through `scripts/migrate_taxonomy_v094.py`. Category routes include `/tr/categories`, `/en/categories`, category landing pages and subcategory pages. Run `py scripts/validate_taxonomy_v094.py` after taxonomy changes.

## v0.9.5 data-quality workflow

AtlasFind now distinguishes between `verified`, `partially_verified`, `unverified` and `review_due` listings. The automated migration never promotes a listing to fully verified. Use the audit before editorial work:

```powershell
py scripts\audit_tool_data_v095.py
py scripts\validate_tool_quality_v095.py
```

Audit reports are written to `reports/data-quality-v095.json` and `reports/data-quality-v095.md`. Live pricing, platform availability and feature claims must still be checked against each tool's official website before using the `verified` status.

### v0.9.6 icon system

Tool images use a three-stage approach: configured primary icon, generated local SVG fallback, and an in-page text monogram as the final runtime fallback. Run `py scripts/audit_icons_v096.py` and `py scripts/validate_icons_v096.py` after icon-data changes.


## v0.9.7-dev
Professional bilingual tool detail pages with clearer pricing, platforms, target users, requirements, pros/cons, verification, history and alternatives.

## Current development version: v0.9.8-dev

The comparison system supports two, three or four unique tools, localized Turkish and English labels, mobile horizontal tables, common-row hiding and a transparent local recommendation score. No external AI API is used.

Validation:

```powershell
py scripts\validate_compare_recommendations_v098.py
```
