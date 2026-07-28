from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []

def require(condition, message):
    if not condition:
        errors.append(message)

app = (ROOT / "app.py").read_text(encoding="utf-8")
template = (ROOT / "templates" / "compare.html").read_text(encoding="utf-8")
js = (ROOT / "static" / "js" / "main.js").read_text(encoding="utf-8")
engine = (ROOT / "recommendation_engine.py").read_text(encoding="utf-8")

require('APP_VERSION = "0.9.8-dev"' in app, "v0.9.8-dev version marker missing")
require('duplicate_removed' in app and 'invalid_slugs' in app, "safe duplicate/invalid selection handling missing")
require('unique_slugs = unique_slugs[:4]' in app, "four-tool comparison limit missing")
require('build_comparison_rows(selected_tools)' in app, "comparison rows are not generated")
require('localized_path(\'/compare\')' in template or 'localized_path("/compare")' in template, "localized comparison form action missing")
require('data-compare-tool-select' in template and 'syncCompareToolOptions' in js, "duplicate select prevention missing")
require('comparison-table-dynamic' in template, "responsive comparison table missing")
require('winner' in template and 'scored_tools' in template, "recommendation ranking output missing")
require('design and graphics' in engine and 'cybersecurity' in engine and 'browsers and internet' in engine, "v0.9.4 taxonomy not reflected in recommendation engine")
require('onload=' not in template.lower(), "inline onload is forbidden")

for locale in ("tr", "en"):
    data = json.loads((ROOT / "translations" / f"{locale}.json").read_text(encoding="utf-8"))
    for key in (
        "compare.seo_title", "compare.intro", "compare.duplicate_removed", "compare.invalid_removed",
        "compare.summary", "compare.table_label", "compare.fit_description", "compare.empty_title",
        "compare.row.category", "compare.row.pricing", "compare.row.platforms", "compare.row.target_users",
        "recommend.purpose", "recommend.platform", "recommend.hardware", "recommend.experience",
        "recommend.privacy", "recommend.offline_required", "actions.view_details", "actions.visit_tool",
    ):
        require(bool(data.get(key)), f"{locale}: missing translation {key}")

# Make sure all direct t() keys in the template exist in both locales.
keys = sorted(set(re.findall(r't\(["\']([^"\']+)["\']', template)))
for locale in ("tr", "en"):
    data = json.loads((ROOT / "translations" / f"{locale}.json").read_text(encoding="utf-8"))
    for key in keys:
        if "~" not in key and not key.endswith("_"):
            require(key in data, f"{locale}: template translation missing: {key}")

if errors:
    print("v0.9.8 comparison validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)
print("v0.9.8 comparison and recommendation validation successful.")
