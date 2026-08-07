"""Promote the reviewed 100-tool expansion into the modular public catalog."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalog.loader import iter_catalog_files, load_catalog
from catalog.validator import validate_catalog

RECORDS = ROOT / "data/research/catalog-expansion-records.json"
MANIFEST = ROOT / "data/catalog/manifest.json"


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_for_public_beta(tool: dict) -> dict:
    tool = dict(tool)
    tool["publication_status"] = "published"
    tool["quality_status"] = "partially_verified"
    tool["quality_review"] = {
        "scope": "official-source-public-beta",
        "reviewed_at": "2026-08-08",
        "note": "Identity, official website, category and logo were reviewed. Plan limits, regional pricing and platform availability remain subject to official provider changes.",
    }
    tool["verification"]["status"] = "partially_verified"
    tool["verification"]["date"] = "2026-08-08"
    for source in tool.get("source_references", []):
        if source.get("type") == "official-announcement":
            source["type"] = "official-company"
    history = tool.get("change_history", [])
    for event in history:
        if event.get("type") == "identity-update":
            event["type"] = "status-change"
    history.sort(key=lambda event: event.get("date", ""), reverse=True)
    return tool


def main() -> None:
    existing = load_catalog(validate=True)
    expansion = [normalize_for_public_beta(tool) for tool in json.loads(RECORDS.read_text(encoding="utf-8"))]
    existing_slugs = {tool["slug"] for tool in existing}
    existing_ids = {tool["id"] for tool in existing}
    collisions = [tool["slug"] for tool in expansion if tool["slug"] in existing_slugs or tool["id"] in existing_ids]
    if collisions:
        raise SystemExit("Expansion collides with existing catalog: " + ", ".join(collisions))

    file_by_category: dict[str, Path] = {}
    payload_by_path: dict[Path, list[dict]] = {}
    for path in iter_catalog_files():
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload_by_path[path] = payload
        categories = {tool["category"] for tool in payload}
        if len(categories) != 1:
            raise SystemExit(f"Catalog file does not map to one category: {path.name}")
        file_by_category[next(iter(categories))] = path

    additions: dict[Path, list[dict]] = defaultdict(list)
    for tool in expansion:
        path = file_by_category.get(tool["category"])
        if path is None:
            raise SystemExit(f"No modular catalog file for category: {tool['category']}")
        additions[path].append(tool)

    combined = existing + expansion
    errors = validate_catalog(combined)
    if errors:
        raise SystemExit("Combined catalog validation failed:\n" + "\n".join(errors))

    for path, tools in additions.items():
        merged = payload_by_path[path] + sorted(tools, key=lambda item: item["id"])
        dump(path, merged)
        print(f"{path.name}: +{len(tools)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["record_count"] = len(combined)
    dump(MANIFEST, manifest)
    dump(RECORDS, expansion)
    print(f"Public catalog promoted: {len(existing)} -> {len(combined)} tools")


if __name__ == "__main__":
    main()
