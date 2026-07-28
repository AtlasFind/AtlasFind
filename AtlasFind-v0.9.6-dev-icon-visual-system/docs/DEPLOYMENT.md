# AtlasFind v0.8.0 Deployment

## Production commands

Build:

```text
pip install -r requirements.txt
```

Start:

```text
python scripts/start_production.py
```

The startup command creates/migrates the SQLite database, seeds it from the JSON catalog only when it is empty, and starts Gunicorn.

## Required environment variables

```text
ATLASFIND_ENV=production
ATLASFIND_SECRET_KEY=<unique random value, minimum 32 characters>
ATLASFIND_HTTPS=1
ATLASFIND_TRUST_PROXY=1
ATLASFIND_SITE_URL=https://atlasfind.com
ATLASFIND_DATABASE_PATH=/absolute/persistent/path/atlasfind.db
```

The database path must point to persistent storage. A normal container filesystem can be replaced during deployment, which would erase runtime changes.

## Health checks

- `/health`: process liveness
- `/ready`: database access and catalog readiness

## Domain checklist

1. Deploy and verify the provider URL.
2. Add `atlasfind.com` and `www.atlasfind.com` in the hosting dashboard.
3. Copy the DNS records supplied by the host into the domain registrar.
4. Wait for DNS verification and HTTPS issuance.
5. Set `ATLASFIND_SITE_URL=https://atlasfind.com`.
6. Redirect `www` to the canonical root domain at the hosting layer.
7. Verify `/robots.txt`, `/sitemap.xml`, `/health`, `/ready`, `/en/`, and `/tr/`.

## Backups

Run regularly against the persistent database:

```text
python scripts/backup_database.py
```

Copy backups to storage outside the running service. A backup sitting beside the database is merely another file waiting to disappear with it.

## Docker

```text
docker build -t atlasfind:0.8.0 .
docker run --rm -p 8000:8000 \
  -e ATLASFIND_ENV=production \
  -e ATLASFIND_SECRET_KEY=<secret> \
  -e ATLASFIND_SITE_URL=http://localhost:8000 \
  -e ATLASFIND_DATABASE_PATH=/app/storage/atlasfind.db \
  -v atlasfind-data:/app/storage \
  atlasfind:0.8.0
```
