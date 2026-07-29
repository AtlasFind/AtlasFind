# AtlasFind v1.0.4 Brand Guard Patch

This patch strengthens automatic logo approval without modifying the existing queue or imported images.

## Added safeguards

- Rejects generic root favicons/touch icons from multi-product companies.
- Requires product-specific evidence for Apple, Microsoft, Google, Adobe, AWS and similar domains.
- Detects duplicate candidate URLs across different tools.
- Detects duplicate image checksums across different tools.
- Tries the next eligible product-specific candidate when a collision is found.
- Writes `data/branding/logo-auto-review-diagnostics.json`.
- Keeps dry-run mode as the default.
- Creates a timestamped queue backup before `--apply`.

## Commands

```powershell
py -m unittest tests.test_brand_guard_auto_review_v104
py scripts\auto_review_logo_candidates_v104.py
py scripts\auto_review_logo_candidates_v104.py --apply
```
