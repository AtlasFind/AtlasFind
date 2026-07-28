# Security Policy

## Supported version

AtlasFind v1.0.x is the supported public release line.

## Reporting a vulnerability

Do not publish exploitable details in a public issue. Send a clear report to **atlasfindd@gmail.com** with:

- affected URL or component;
- reproduction steps;
- expected and observed behavior;
- potential impact;
- screenshots or a minimal proof of concept when safe.

Do not access data that is not yours, disrupt the service, run destructive tests, or use automated scanning at abusive rates. AtlasFind will review good-faith reports and coordinate a fix and disclosure when appropriate.

## Production controls

The project includes CSRF protection for admin writes, secure session cookies in HTTPS production, login and API rate limiting, CSP and browser security headers, Host-header validation, request IDs, bounded request sizes, safe error pages, SQLite integrity checks and backup tooling. These controls reduce risk; they are not a claim that vulnerabilities are impossible.
