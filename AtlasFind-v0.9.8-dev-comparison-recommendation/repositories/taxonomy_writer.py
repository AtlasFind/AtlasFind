from database import DATABASE_PATH, connect_database, transaction


def list_taxonomies(path=DATABASE_PATH):
    with connect_database(path) as connection:
        categories = connection.execute("SELECT c.*, COUNT(t.id) usage_count FROM categories c LEFT JOIN tools t ON t.category_id=c.id GROUP BY c.id ORDER BY c.name").fetchall()
        tags = connection.execute("SELECT g.*, COUNT(tt.tool_id) usage_count FROM tags g LEFT JOIN tool_tags tt ON tt.tag_id=g.id GROUP BY g.id ORDER BY g.name").fetchall()
    return categories, tags


def add_category(name, path=DATABASE_PATH):
    slug = name.strip().lower().replace("&", "and").replace(" ", "-")
    with transaction(path) as connection:
        connection.execute("INSERT OR IGNORE INTO categories(slug,name) VALUES (?,?)", (slug, name.strip()))


def add_tag(name, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (name.strip(),))
