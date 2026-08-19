# AtlasFind v2.1.1 Production Release Checklist

## Before deployment

- [ ] Work from a clean release branch or the protected `main` branch.
- [ ] Set `ATLASFIND_ENV=production`.
- [ ] Generate a unique `ATLASFIND_SECRET_KEY` of at least 32 characters.
- [ ] Set `ATLASFIND_SITE_URL=https://atlasfind.org`.
- [ ] Set `ATLASFIND_CONTACT_EMAIL=atlasfindd@gmail.com`.
- [ ] Set `ATLASFIND_HTTPS=1` and `ATLASFIND_TRUST_PROXY=1` on Render.
- [ ] Set `ATLASFIND_ALLOWED_HOSTS=atlasfind.org,www.atlasfind.org,.onrender.com`.
- [ ] Confirm the persistent disk path is `/opt/render/project/src/storage/atlasfind.db`.
- [ ] Download or create a database backup.
- [ ] Run `py -m unittest discover -s tests -p "test_*.py"` with Flask dependencies installed.
- [ ] Run the active security, deployment, content, SEO and localization validators.

## Smoke tests after deployment

- [ ] `/health` returns 200 and version `2.1.1`.
- [ ] `/ready` returns 200 with 1,000 tools, at least 2,000 translations and 18 categories.
- [ ] `/tr/` and `/en/` load without console errors.
- [ ] Tool catalog, search, filters and pagination work in both languages.
- [ ] Category pages show equal counts in Turkish and English.
- [ ] Tool detail, recommendation and 2/3/4-tool comparison work.
- [ ] Admin login requires credentials; writes require CSRF tokens.
- [ ] `robots.txt`, `sitemap.xml`, canonical and hreflang use `atlasfind.org`.
- [ ] Privacy, terms, cookies and contact pages show `atlasfindd@gmail.com`.
- [ ] Chrome, Firefox, Edge and a narrow mobile viewport pass a basic smoke test.

## Rollback

- [ ] Keep the previous Render deployment available.
- [ ] Keep the pre-start SQLite backup from the persistent disk.
- [ ] If readiness fails or errors spike, roll back code first; restore the database only when the schema or data is damaged.
