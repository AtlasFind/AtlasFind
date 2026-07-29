# AtlasFind v1.0.4 Extended Discovery Patch

This patch extends official-source logo discovery without bypassing bot protection.

- Retries transient HTTP failures with bounded backoff.
- Tries root and www/non-www variants.
- Probes standard manifest, Apple touch icon, favicon and SVG endpoints.
- Continues with official documentation, support, repository, app-store and brand URLs already stored in the catalog.
- Records every attempt in `discovery_attempt_log`.
- Preserves existing candidates, approvals and imported logos.
- Preflights image bytes, MIME type, SVG safety and raster resolution before automatic approval.
- Allows more safe official-source candidates to be approved while rejecting low-resolution or unsafe assets.
