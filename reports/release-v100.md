# AtlasFind v1.0.0 Release Report

## Release contents

- Application version: `1.0.0`
- Catalog tools: 600
- Tool translations: 1,200
- Canonical categories: 18
- Production domain: `https://atlasfind.org`
- Contact: `atlasfindd@gmail.com`

## Production hardening

- trusted Render proxy handling;
- configurable Host-header allow-list;
- secure production session cookies;
- CSRF protection for admin writes;
- admin login and public API rate limiting;
- request-size limit and bounded search queries;
- per-request CSP nonces for inline scripts;
- HSTS, frame denial, MIME sniffing prevention and restrictive permissions policy;
- request IDs in logs and responses;
- SQLite backup before startup migrations;
- destructive automatic reseeding disabled for non-empty persistent databases;
- database integrity and catalog-count readiness checks;
- Gunicorn graceful shutdown and worker request recycling.

## Validation result

Static release, schema, translation, database, security, SEO and historical regression validators passed in the packaging environment. Flask was unavailable in that isolated environment, so runtime route tests were explicitly skipped there. The release gate runs real route and security-header tests by default once dependencies are installed on the target machine or CI environment.

## Required production gate

Run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py scripts\validate_release_v100.py
```

Do not switch production traffic unless this command succeeds without the runtime-skip environment variable.
