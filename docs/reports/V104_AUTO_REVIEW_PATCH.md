# AtlasFind v1.0.4 Auto Review Patch

This patch adds a conservative bulk review command without replacing the existing discovery queue.

Dry run:

```powershell
py scripts\auto_review_logo_candidates_v104.py
```

Apply safe selections:

```powershell
py scripts\auto_review_logo_candidates_v104.py --apply
```

Import approved assets:

```powershell
py scripts\import_tool_logos_v104.py --verified-by admin --limit 600
py scripts\build_catalog.py
py scripts\sync_branding_v104_to_sqlite.py
py scripts\validate_tool_images_v104.py --require-verified 1
```

The auto reviewer only selects same-site HTTPS icon or manifest candidates from the configured official product website, requires a minimum score, rejects ambiguous ties, and backs up the queue before writing.
