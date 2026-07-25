from database import DATABASE_PATH, connect_database
from .common import decode_payload


def get_all_articles(path=DATABASE_PATH):
    if not path.exists():
        return []
    with connect_database(path) as connection:
        rows = connection.execute("SELECT payload_json FROM articles ORDER BY published_at DESC, id").fetchall()
    return [decode_payload(row) for row in rows]


def get_article_by_slug(slug, path=DATABASE_PATH):
    if not path.exists():
        return None
    with connect_database(path) as connection:
        row = connection.execute("SELECT payload_json FROM articles WHERE slug = ?", (slug,)).fetchone()
    return decode_payload(row) if row else None
