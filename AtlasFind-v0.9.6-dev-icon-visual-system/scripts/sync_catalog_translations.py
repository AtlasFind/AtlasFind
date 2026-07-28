"""Synchronize v0.9.0 Turkish catalog translations into SQLite."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database import DATABASE_PATH, apply_migrations, transaction

TRANSLATIONS_FILE = ROOT / "data" / "tool_translations_tr_v090.json"

def main() -> None:
    apply_migrations()
    rows = json.loads(TRANSLATIONS_FILE.read_text(encoding="utf-8"))
    with transaction() as connection:
        for row in rows:
            exists = connection.execute("SELECT 1 FROM tools WHERE id=?", (row["tool_id"],)).fetchone()
            if not exists:
                continue
            connection.execute(
                """INSERT INTO tool_translations(
                    tool_id, locale, name, description, subcategory,
                    pricing_summary, pricing_notes, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tool_id, locale) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    subcategory=excluded.subcategory,
                    pricing_summary=excluded.pricing_summary,
                    pricing_notes=excluded.pricing_notes,
                    payload_json=excluded.payload_json""",
                (
                    row["tool_id"], row["locale"], row.get("name"), row.get("description"),
                    row.get("subcategory"), row.get("pricing_summary"), row.get("pricing_notes"),
                    json.dumps(row.get("payload_json") or {}, ensure_ascii=False),
                ),
            )
    print(f"{len(rows)} Turkish catalog translations synchronized")

if __name__ == "__main__":
    main()
