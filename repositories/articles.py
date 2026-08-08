from database import DATABASE_PATH, connect_database
from .common import decode_payload


def get_all_articles(path=DATABASE_PATH):
    if not path.exists():
        return []
    with connect_database(path) as connection:
        rows = connection.execute("SELECT id,payload_json FROM articles WHERE COALESCE(status,'published')='published' ORDER BY published_at DESC, id").fetchall()
    articles = []
    for row in rows:
        article = decode_payload(row)
        article["id"] = row["id"]
        articles.append(article)
    return articles


def get_article_by_slug(slug, path=DATABASE_PATH):
    if not path.exists():
        return None
    with connect_database(path) as connection:
        row = connection.execute("SELECT id,payload_json FROM articles WHERE slug = ? AND COALESCE(status,'published')='published'", (slug,)).fetchone()
    if not row:
        return None
    article = decode_payload(row)
    article["id"] = row["id"]
    return article
