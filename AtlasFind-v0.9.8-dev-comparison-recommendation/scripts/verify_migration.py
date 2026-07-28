import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database import connect_database
from repositories.tools import get_all_tools
from repositories.articles import get_all_articles


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    source_tools = load(ROOT / "data" / "tools.json")
    source_articles = load(ROOT / "data" / "articles.json")
    db_tools = get_all_tools()
    db_articles = get_all_articles()
    errors = []

    if len(source_tools) != len(db_tools): errors.append("Tool count mismatch")
    if len(source_articles) != len(db_articles): errors.append("Article count mismatch")
    if {x["slug"] for x in source_tools} != {x["slug"] for x in db_tools}: errors.append("Tool slug mismatch")
    if {x["slug"] for x in source_articles} != {x["slug"] for x in db_articles}: errors.append("Article slug mismatch")

    source_by_slug = {x["slug"]: x for x in source_tools}
    db_by_slug = {x["slug"]: x for x in db_tools}
    for slug, source in source_by_slug.items():
        target = db_by_slug.get(slug, {})
        for field in ("platforms", "tags", "pros", "cons", "freshness", "change_history", "price_history"):
            if source.get(field) != target.get(field): errors.append(f"{slug}: {field} mismatch")

    with connect_database() as connection:
        fk_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors: errors.append(f"Foreign key errors: {len(fk_errors)}")

    if errors:
        print("Migration verification failed:")
        for error in errors: print(f"- {error}")
        raise SystemExit(1)
    print(f"Migration verification successful: {len(db_tools)} tools and {len(db_articles)} articles match JSON sources.")

if __name__ == "__main__": main()
