"""Static and data-level checks for the v0.9.2 catalog experience."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Catalog v0.9.2 validation failed: {message}")


def main() -> None:
    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    template = (ROOT / "templates" / "discovery.html").read_text(encoding="utf-8")
    css = (ROOT / "static" / "css" / "style.css").read_text(encoding="utf-8")
    js = (ROOT / "static" / "js" / "main.js").read_text(encoding="utf-8")
    tools = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))

    require('APP_VERSION = "' in app_text, "application version marker is missing")
    require('@app.route("/<locale>/tools")' in app_text, "localized catalog route is missing")
    require("min_rating" in app_text and '"category"' in app_text, "category or rating filters are missing")
    require("previous_page_url" in template and "next_page_url" in template, "filter-safe pagination is missing")
    require("data-catalog-view" in template and "data-catalog-grid" in template, "grid/list controls are missing")
    require("filterPanel" in template and "filterToggle" in template, "mobile filter panel hooks are missing")
    require("onload=" not in template.lower(), "inline image onload handler returned")
    require(".catalog-grid.is-list" in css, "list view styles are missing")
    require("atlas-catalog-view" in js, "catalog view preference is not persisted")
    require(len(tools) == 600, f"expected 600 tools, found {len(tools)}")

    translation_keys = set(re.findall(r"t\([\"']([^\"']+)", template))
    translation_keys.discard("catalog.price_")
    translation_keys.discard("quality.")
    for locale in ("tr", "en"):
        translations = json.loads((ROOT / "translations" / f"{locale}.json").read_text(encoding="utf-8"))
        missing = sorted(translation_keys - set(translations))
        require(not missing, f"{locale} translations missing: {', '.join(missing)}")

    print("Catalog v0.9.2 static validation successful: filters, views, translations and 600-tool data are present.")


if __name__ == "__main__":
    main()
