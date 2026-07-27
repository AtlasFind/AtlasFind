# AtlasFind

**Find the right software. Faster.**

AtlasFind is a Flask-based software discovery, recommendation, comparison and editorial guide platform.

## Current Version

v0.7.0

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
