import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import DATABASE_PATH, initialize_database, transaction
from tool_schema import validate_tools
from content_schema import validate_articles

TOOLS_FILE = ROOT / "data" / "tools.json"
ARTICLES_FILE = ROOT / "data" / "articles.json"
CHECKLIST_FILE = ROOT / "data" / "update_checklist.json"


def slugify(value):
    return str(value or "").strip().lower().replace("&", "and").replace(" ", "-")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def get_or_create(connection, table, key_column, value, extra_column=None, extra_value=None):
    row = connection.execute(f"SELECT id FROM {table} WHERE {key_column} = ?", (value,)).fetchone()
    if row:
        return row[0]
    if extra_column:
        cursor = connection.execute(
            f"INSERT INTO {table}({key_column}, {extra_column}) VALUES (?, ?)",
            (value, extra_value),
        )
    else:
        cursor = connection.execute(f"INSERT INTO {table}({key_column}) VALUES (?)", (value,))
    return cursor.lastrowid


def migrate(reset=True):
    tools = load_json(TOOLS_FILE)
    articles = load_json(ARTICLES_FILE)
    checklist = load_json(CHECKLIST_FILE)

    errors = validate_tools(tools)
    errors += validate_articles(articles, {tool.get("slug") for tool in tools})
    if errors:
        raise ValueError("Source validation failed:\n" + "\n".join(errors))

    if reset and DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    initialize_database()

    with transaction() as connection:
        tool_ids = {}
        article_ids = {}

        for tool in tools:
            category_name = tool.get("category") or "Uncategorized"
            category_id = get_or_create(connection, "categories", "slug", slugify(category_name), "name", category_name)
            cursor = connection.execute(
                """INSERT INTO tools(
                    id, slug, name, description, category_id, subcategory, pricing_type,
                    rating, website, open_source, offline, ai_powered, minimum_ram_gb,
                    system_level, editor_choice, popularity_score, date_added, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    tool.get("id"), tool.get("slug"), tool.get("name"), tool.get("description", ""),
                    category_id, tool.get("subcategory"), tool.get("pricing_type"), tool.get("rating"),
                    tool.get("website"), int(bool(tool.get("open_source"))), int(bool(tool.get("offline"))),
                    int(bool(tool.get("ai_powered"))), tool.get("minimum_ram_gb"), tool.get("system_level"),
                    int(bool(tool.get("editor_choice"))), tool.get("popularity_score", 0), tool.get("date_added"),
                    json.dumps(tool, ensure_ascii=False),
                ),
            )
            tool_id = tool.get("id") or cursor.lastrowid
            tool_ids[tool.get("slug")] = tool_id

            for platform in tool.get("platforms", []):
                platform_id = get_or_create(connection, "platforms", "slug", slugify(platform), "name", platform)
                connection.execute("INSERT OR IGNORE INTO tool_platforms VALUES (?, ?)", (tool_id, platform_id))
            for tag in tool.get("tags", []):
                tag_id = get_or_create(connection, "tags", "name", tag)
                connection.execute("INSERT OR IGNORE INTO tool_tags VALUES (?, ?)", (tool_id, tag_id))
            for language in tool.get("languages", []):
                language_id = get_or_create(connection, "languages", "code", language)
                connection.execute("INSERT OR IGNORE INTO tool_languages VALUES (?, ?)", (tool_id, language_id))
            for collection in tool.get("collections", []):
                collection_id = get_or_create(connection, "collections", "slug", collection)
                connection.execute("INSERT OR IGNORE INTO tool_collections VALUES (?, ?)", (tool_id, collection_id))
            for event in tool.get("change_history", []):
                connection.execute(
                    "INSERT INTO tool_change_history(tool_id,event_date,event_type,summary,payload_json) VALUES (?,?,?,?,?)",
                    (tool_id, event.get("date"), event.get("type"), event.get("summary"), json.dumps(event, ensure_ascii=False)),
                )
            for event in tool.get("price_history", []):
                connection.execute(
                    "INSERT INTO tool_price_history(tool_id,event_date,payload_json) VALUES (?,?,?)",
                    (tool_id, event.get("date"), json.dumps(event, ensure_ascii=False)),
                )

        for article in articles:
            category_name = article.get("category") or "uncategorized"
            category_id = get_or_create(connection, "categories", "slug", slugify(category_name), "name", category_name)
            cursor = connection.execute(
                """INSERT INTO articles(slug,title,description,content_type,category_id,published_at,updated_at,author,payload_json)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (article.get("slug"), article.get("title"), article.get("description", ""), article.get("content_type"),
                 category_id, article.get("published_at"), article.get("updated_at"), article.get("author"),
                 json.dumps(article, ensure_ascii=False)),
            )
            article_ids[article.get("slug")] = cursor.lastrowid

        for article in articles:
            article_id = article_ids[article.get("slug")]
            for slug in article.get("related_tool_slugs", []):
                if slug in tool_ids:
                    connection.execute("INSERT OR IGNORE INTO article_related_tools VALUES (?, ?)", (article_id, tool_ids[slug]))
            for slug in article.get("related_article_slugs", []):
                if slug in article_ids:
                    connection.execute("INSERT OR IGNORE INTO article_related_articles VALUES (?, ?)", (article_id, article_ids[slug]))

        items = checklist.get("items", checklist if isinstance(checklist, list) else [])
        for position, item in enumerate(items, start=1):
            connection.execute(
                "INSERT INTO update_checklist_items(position,payload_json) VALUES (?,?)",
                (position, json.dumps(item, ensure_ascii=False)),
            )

    print(f"{len(tools)} tools migrated")
    print(f"{len(articles)} articles migrated")
    print(f"{len({tool.get('category') for tool in tools})} tool categories migrated")
    print(f"{len(items)} checklist items migrated")
    print("Migration completed successfully")


if __name__ == "__main__":
    migrate()
