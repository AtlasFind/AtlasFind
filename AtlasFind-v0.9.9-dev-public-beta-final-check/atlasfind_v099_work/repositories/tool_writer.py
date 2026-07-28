import json
from datetime import datetime, timezone

from database import DATABASE_PATH, connect_database, transaction
from .common import decode_payload, normalize_tool_payload


def _slugify(value):
    return str(value or "").strip().lower().replace("&", "and").replace(" ", "-")


def list_admin_tools(path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT id,slug,name,status,updated_at FROM tools ORDER BY updated_at DESC,name"
        ).fetchall()


def get_tool_for_admin(tool_id, path=DATABASE_PATH):
    with connect_database(path) as connection:
        row = connection.execute("SELECT * FROM tools WHERE id=?", (tool_id,)).fetchone()
    if not row:
        return None
    result = dict(row)
    result["payload"] = json.loads(row["payload_json"])
    return result


def _category_id(connection, category):
    slug = _slugify(category or "Uncategorized")
    row = connection.execute("SELECT id FROM categories WHERE slug=?", (slug,)).fetchone()
    if row:
        return row["id"]
    cursor = connection.execute("INSERT INTO categories(slug,name) VALUES (?,?)", (slug, category or "Uncategorized"))
    return cursor.lastrowid


def save_tool(payload, status="draft", tool_id=None, path=DATABASE_PATH):
    payload = normalize_tool_payload(payload)
    payload["slug"] = _slugify(payload.get("slug") or payload.get("name"))
    payload.setdefault("name", payload["slug"].replace("-", " ").title())
    payload.setdefault("description", "")
    payload.setdefault("category", "Uncategorized")
    payload.setdefault("platforms", [])
    payload.setdefault("tags", [])
    payload.setdefault("languages", ["en"])
    payload.setdefault("collections", [])
    payload.setdefault("pros", [])
    payload.setdefault("cons", [])
    payload.setdefault("target_users", [])
    payload.setdefault("system_requirements", [])
    payload.setdefault("change_history", [])
    payload.setdefault("price_history", [])
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with transaction(path) as connection:
        category_id = _category_id(connection, payload.get("category"))
        values = (
            payload["slug"], payload["name"], payload.get("description", ""), category_id,
            payload.get("subcategory"), payload.get("pricing_type") or payload.get("pricing"),
            payload.get("rating"), payload.get("website"), int(bool(payload.get("open_source"))),
            int(bool(payload.get("offline"))), int(bool(payload.get("ai_powered"))),
            payload.get("minimum_ram_gb"), payload.get("system_level"),
            int(bool(payload.get("editor_choice"))), int(payload.get("popularity_score") or 0),
            payload.get("date_added"), json.dumps(payload, ensure_ascii=False), status,
        )
        if tool_id is None:
            next_id = connection.execute("SELECT COALESCE(MAX(id),0)+1 AS id FROM tools").fetchone()["id"]
            cursor = connection.execute(
                """INSERT INTO tools(id,slug,name,description,category_id,subcategory,pricing_type,rating,website,
                   open_source,offline,ai_powered,minimum_ram_gb,system_level,editor_choice,popularity_score,
                   date_added,payload_json,status,published_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,CASE WHEN ?='published' THEN CURRENT_TIMESTAMP END,CURRENT_TIMESTAMP)""",
                (next_id,) + values + (status,),
            )
            tool_id = next_id
        else:
            connection.execute(
                """UPDATE tools SET slug=?,name=?,description=?,category_id=?,subcategory=?,pricing_type=?,rating=?,website=?,
                   open_source=?,offline=?,ai_powered=?,minimum_ram_gb=?,system_level=?,editor_choice=?,popularity_score=?,
                   date_added=?,payload_json=?,status=?,published_at=CASE WHEN ?='published' THEN COALESCE(published_at,CURRENT_TIMESTAMP) ELSE published_at END,
                   archived_at=CASE WHEN ?='archived' THEN CURRENT_TIMESTAMP ELSE NULL END,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                values + (status, status, tool_id),
            )
        _sync_relations(connection, tool_id, payload)
    return tool_id


def _sync_relations(connection, tool_id, payload):
    mapping = [
        ("tool_platforms", "platforms", "platforms", "slug", "name"),
        ("tool_tags", "tags", "tags", "name", None),
        ("tool_languages", "languages", "languages", "code", None),
        ("tool_collections", "collections", "collections", "slug", None),
    ]
    for relation, key, table, unique_column, display_column in mapping:
        foreign_column = relation.split("_")[1][:-1] + "_id" if relation != "tool_collections" else "collection_id"
        connection.execute(f"DELETE FROM {relation} WHERE tool_id=?", (tool_id,))
        for value in payload.get(key, []) or []:
            lookup = _slugify(value) if unique_column == "slug" else value
            row = connection.execute(f"SELECT id FROM {table} WHERE {unique_column}=?", (lookup,)).fetchone()
            if row:
                relation_id = row["id"]
            else:
                if display_column:
                    cursor = connection.execute(
                        f"INSERT INTO {table}({unique_column},{display_column}) VALUES (?,?)", (lookup, value)
                    )
                else:
                    cursor = connection.execute(f"INSERT INTO {table}({unique_column}) VALUES (?)", (lookup,))
                relation_id = cursor.lastrowid
            connection.execute(
                f"INSERT OR IGNORE INTO {relation}(tool_id,{foreign_column}) VALUES (?,?)", (tool_id, relation_id)
            )


def archive_tool(tool_id, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute("UPDATE tools SET status='archived',archived_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE id=?", (tool_id,))
