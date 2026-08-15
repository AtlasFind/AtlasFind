# Script inventory

AtlasFind keeps production commands, repeatable maintenance tools and historical
catalog builders in this directory. A version suffix describes the data format
that a historical tool was created for; it does not describe the current app
version.

## Production-critical

- `start_production.py`: prepares storage, then starts Gunicorn.
- `bootstrap_database.py`: seeds, migrates and synchronizes persistent data.
- `migrate_json_to_sqlite.py`, `sync_missing_catalog_tools.py`: create or expand the catalog.
- `sync_catalog_translations.py`, `sync_expansion_translations.py`,
  `sync_complete_turkish_translations.py`, `sync_complete_turkish_articles.py`:
  translation bootstrap chain. The final tool preserves editorial translations
  and replaces only missing or recognized legacy-generated copy.
- `backup_database.py`: pre-start database backup.

## Routine validation

- `check_links.py`, `test_search.py`, `test_recommendations.py`
- `validate_security.py`, `validate_deployment.py`, `validate_content.py`
- `validate_tools.py`, `validate_translations.py`, `validate_freshness.py`

These checks also run in `.github/workflows/quality.yml` where appropriate.

## Catalog-worker tools

Files containing `catalog_worker`, logo discovery/review commands and catalog
evidence audits support the offline editorial pipeline. They are not called by
the public web request path.

## Historical one-time tools

Files containing old release suffixes (`v090` through `v105`), `manual_850`,
`manual_1000`, `expansion`, `migrate_`, `finalize_` or `patch` are retained for
reproducibility of the catalog history. Do not add them to production startup
without updating this inventory and adding an automated test. Historical
release reports live in `docs/reports/`.
