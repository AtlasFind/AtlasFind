# AtlasFind v1.0.4 Final Consolidated Patch

This package consolidates the extended discovery, safe auto-review, product-marker guard, import recovery, timeout/checkpoint handling, and fast local queue report.

Important fixes:
- The queue report performs local JSON counting only and never opens the network.
- `--limit` counts processed tools, not only successful imports.
- `--approved-errors-only` now excludes review/no-candidate items correctly.
- Import retries are bounded by per-candidate timeout and per-tool candidate limits.
- Progress is checkpointed after each processed tool by default.
- Expanded discovery continues across official URL variants and standard assets.
- Generic multi-product company icons are not auto-approved as product logos.
- Duplicate URL/checksum collisions are blocked from automatic approval.
- Legacy and new v1.0.4 tests pass together.

Recommended final retry command:

    py scripts/import_tool_logos_v104.py --verified-by admin --retry-errors --try-alternates --approved-errors-only --limit 20 --timeout 4 --max-candidates-per-tool 2

Then run:

    py scripts/build_catalog.py
    py scripts/sync_branding_v104_to_sqlite.py
    py scripts/validate_tool_images_v104.py --require-verified 1
    py scripts/logo_queue_report_v104.py
