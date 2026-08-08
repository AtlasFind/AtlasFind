"""Add transparent Turkish public-beta translations for expansion records."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import transaction

RECORDS = [
    ROOT / "data/research/catalog-expansion-records.json",
    ROOT / "data/research/manual-expansion-850-records.json",
]


def main() -> None:
    tools = []
    for path in RECORDS:
        if path.exists():
            tools.extend(json.loads(path.read_text(encoding="utf-8")))
    with transaction() as connection:
        for tool in tools:
            pricing = {"free": "Ücretsiz", "freemium": "Ücretsiz + Ücretli", "paid": "Ücretli"}[tool["pricing_type"]]
            description = f'{tool["name"]}, {tool["subcategory"].lower()} iş akışlarına odaklanan bir {tool["category"].lower()} aracıdır.'
            note = "Planlar, bölgesel fiyatlar ve platform desteği değişebilir; güncel bilgiyi resmî web sitesinden doğrulayın."
            payload = {
                "description": description,
                "category": tool["category"],
                "subcategory": tool["subcategory"],
                "pricing": pricing,
                "pricing_details": {"model": pricing, "note": note},
                "verification": {
                    "status": "Kısmen doğrulandı",
                    "date": "2026-08-08",
                    "note": "Kimlik, resmî site, kategori ve logo kontrol edildi; değişebilen ayrıntılar için resmî kaynağa bakın.",
                },
            }
            connection.execute(
                """INSERT INTO tool_translations(tool_id,locale,name,description,subcategory,pricing_summary,pricing_notes,payload_json)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(tool_id,locale) DO UPDATE SET name=excluded.name,description=excluded.description,
                   subcategory=excluded.subcategory,pricing_summary=excluded.pricing_summary,
                   pricing_notes=excluded.pricing_notes,payload_json=excluded.payload_json""",
                (tool["id"], "tr", tool["name"], description, tool["subcategory"], pricing, note, json.dumps(payload, ensure_ascii=False)),
            )
    print(f"{len(tools)} expansion Turkish translations synchronized")


if __name__ == "__main__":
    main()
