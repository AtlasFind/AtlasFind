"""Apply officially confirmed product rebrands to isolated expansion data."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-08-08"
REBRANDS = {
    "timeular": {
        "name": "EARLY",
        "website": "https://early.app/",
        "old_name": "Timeular",
        "evidence": "https://early.app/blog/timeular-is-now-early/",
        "summary": "Timeular officially became EARLY on 18 March 2025.",
    },
    "revolt": {
        "name": "Stoat",
        "website": "https://stoat.chat/",
        "old_name": "Revolt",
        "evidence": "https://stoat.chat/updates/policies-30-jun-2026",
        "summary": "Revolt officially changed its product name to Stoat in 2026.",
    },
}


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    candidates_path = ROOT / "data/research/catalog-expansion-700.json"
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    for item in candidates["candidates"]:
        if item["slug"] in REBRANDS:
            change = REBRANDS[item["slug"]]
            item["name"] = change["name"]
            item["official_url"] = change["website"]
    write(candidates_path, candidates)

    urls_path = ROOT / "data/research/catalog-expansion-official-urls.json"
    urls = json.loads(urls_path.read_text(encoding="utf-8"))
    for slug, change in REBRANDS.items():
        urls[slug] = change["website"]
    write(urls_path, urls)

    records_path = ROOT / "data/research/catalog-expansion-records.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))
    for item in records:
        if item["slug"] not in REBRANDS:
            continue
        change = REBRANDS[item["slug"]]
        item["name"] = change["name"]
        item["website"] = change["website"]
        item["aliases"] = sorted(set(item.get("aliases", [])) | {change["old_name"]})
        item["description"] = item["description"].replace(change["old_name"], change["name"], 1)
        item["icon_alt"] = f'{change["name"]} icon'
        item["verification"]["note"] = change["summary"] + " Pricing and platform evidence remain under review."
        item["change_history"].append(
            {"date": TODAY, "type": "identity-update", "summary": change["summary"], "changes": ["name", "website", "aliases"]}
        )
        item["source_references"] = [
            {
                "label": f'{change["name"]} official rebrand announcement',
                "url": change["evidence"],
                "type": "official-announcement",
                "checked_at": TODAY,
                "domain": change["evidence"].split("/")[2],
                "claims": ["identity", "name-change", "website"],
            }
        ]
    write(records_path, records)

    queue_path = ROOT / "data/research/catalog-expansion-logo-queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    for item in queue["items"]:
        if item["slug"] in REBRANDS:
            change = REBRANDS[item["slug"]]
            item["name"] = change["name"]
            item["official_url"] = change["website"]
            item["candidates"] = []
            item["status"] = "review"
    write(queue_path, queue)
    print("Applied official EARLY and Stoat rebrands to expansion staging data")


if __name__ == "__main__":
    main()
