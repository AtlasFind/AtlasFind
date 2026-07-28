from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from search_engine import normalize_text, rank_tools


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"v0.9.3 validation failed: {message}")


def main() -> None:
    tools = json.loads((ROOT / "data" / "tools.json").read_text(encoding="utf-8"))
    require(len(tools) == 600, "catalog must contain 600 tools")
    require(normalize_text("Ücretsiz tarayıcı") == "ucretsiz tarayici", "Turkish normalization failed")

    samples = tools[:10]
    ranked_sample, sample_meta = rank_tools(samples, samples[0]["name"])
    require(ranked_sample, "10-tool sample search returned no results")
    require(sample_meta["duration_ms"] >= 0, "search duration was not measured")

    for query in ("photoshop", "photosop", "ucretsiz video editoru", "tarayici", "microsft copliot", "open source code editor"):
        ranked, meta = rank_tools(tools, query)
        require(isinstance(ranked, list), f"invalid search result for {query}")
        identities = [str(item["tool"].get("slug") or item["tool"].get("id")) for item in ranked]
        require(len(identities) == len(set(identities)), f"duplicate search results for {query}")
        require(meta["duration_ms"] >= 0, f"duration missing for {query}")

    app_text = (ROOT / "app.py").read_text(encoding="utf-8")
    template = (ROOT / "templates" / "discovery.html").read_text(encoding="utf-8")
    require('APP_VERSION = "' in app_text, "version marker missing")
    require("per_page=24" in app_text, "24-item pagination missing")
    require("pagination_window" in app_text, "numbered pagination window missing")
    require('request.args.get("q"' in app_text, "catalog query parameter missing")
    require('name="q"' in template, "catalog search input missing")
    require("page_links" in template, "numbered pagination template missing")
    require("onload=" not in template.lower(), "inline onload must not be used")

    for locale in ("tr", "en"):
        messages = json.loads((ROOT / "translations" / f"{locale}.json").read_text(encoding="utf-8"))
        for key in ("catalog.search_placeholder", "catalog.sort_relevance", "catalog.did_you_mean", "catalog.show_all_tools"):
            require(messages.get(key), f"{locale} translation missing: {key}")

    print("v0.9.3 search, filtering and pagination validation successful.")


if __name__ == "__main__":
    main()
