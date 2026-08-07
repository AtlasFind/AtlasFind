"""Validate the staged AtlasFind 600-to-700 catalog expansion queue."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "research" / "catalog-expansion-700.json"
CATALOG_PATH = ROOT / "data" / "tools.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    queue = load_json(QUEUE_PATH)
    candidates = queue.get("candidates", [])
    catalog = load_json(CATALOG_PATH)
    errors: list[str] = []

    slugs = [item.get("slug") for item in candidates]
    existing_slugs = {item.get("slug") for item in catalog}
    duplicate_candidates = sorted(slug for slug, count in Counter(slugs).items() if count > 1)
    catalog_collisions = sorted(set(slugs).intersection(existing_slugs))

    if len(candidates) != queue.get("target_total", 0) - queue.get("baseline_total", 0):
        errors.append("Candidate count does not match the declared expansion target")
    if duplicate_candidates:
        errors.append(f"Duplicate candidate slugs: {duplicate_candidates}")
    if catalog_collisions:
        errors.append(f"Candidates already present in the catalog: {catalog_collisions}")

    for position, item in enumerate(candidates, start=1):
        for field in ("slug", "name", "category", "subcategory"):
            if not str(item.get(field, "")).strip():
                errors.append(f"Candidate {position} is missing {field}")
        if item.get("verification_status") == "official_source_confirmed":
            official_url = str(item.get("official_url", ""))
            if not official_url.startswith("https://"):
                errors.append(f"Confirmed candidate {item.get('slug')} lacks an HTTPS official URL")

    if errors:
        raise SystemExit("Expansion queue validation failed:\n- " + "\n- ".join(errors))

    confirmed = sum(item.get("verification_status") == "official_source_confirmed" for item in candidates)
    print(f"Expansion queue valid: {len(candidates)} unique candidates, {confirmed} official sources confirmed")


if __name__ == "__main__":
    main()
