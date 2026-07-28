import json
from database import DATABASE_PATH, connect_database, transaction


def list_admin_articles(path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute("SELECT id,slug,title,status,updated_at FROM articles ORDER BY updated_at DESC,title").fetchall()


def get_article_for_admin(article_id, path=DATABASE_PATH):
    with connect_database(path) as connection:
        row = connection.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
    if not row:
        return None
    result = dict(row)
    result["payload"] = json.loads(row["payload_json"])
    return result


def save_article(payload, status="draft", article_id=None, path=DATABASE_PATH):
    payload = dict(payload)
    payload["slug"] = str(payload.get("slug") or payload.get("title", "")).strip().lower().replace(" ", "-")
    payload.setdefault("title", payload["slug"].replace("-", " ").title())
    payload.setdefault("description", "")
    payload.setdefault("sections", [])
    payload.setdefault("faq", [])
    payload.setdefault("related_tool_slugs", [])
    payload.setdefault("related_article_slugs", [])
    with transaction(path) as connection:
        category = payload.get("category") or "uncategorized"
        row = connection.execute("SELECT id FROM categories WHERE slug=?", (category,)).fetchone()
        if row:
            category_id = row["id"]
        else:
            category_id = connection.execute("INSERT INTO categories(slug,name) VALUES (?,?)", (category, category.title())).lastrowid
        values = (
            payload["slug"], payload["title"], payload.get("description", ""), payload.get("content_type"),
            category_id, payload.get("published_at"), payload.get("updated_at"), payload.get("author"),
            json.dumps(payload, ensure_ascii=False), status,
        )
        if article_id is None:
            article_id = connection.execute(
                """INSERT INTO articles(slug,title,description,content_type,category_id,published_at,updated_at,author,payload_json,status)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""", values
            ).lastrowid
        else:
            connection.execute(
                """UPDATE articles SET slug=?,title=?,description=?,content_type=?,category_id=?,published_at=?,updated_at=?,author=?,
                   payload_json=?,status=?,archived_at=CASE WHEN ?='archived' THEN CURRENT_TIMESTAMP ELSE NULL END WHERE id=?""",
                values + (status, article_id),
            )
    return article_id
