from database import DATABASE_PATH, connect_database, transaction


def recent_inquiry_count(ip_address, hours=1, path=DATABASE_PATH):
    with connect_database(path) as connection:
        row = connection.execute(
            """SELECT COUNT(*) AS total FROM collaboration_inquiries
               WHERE ip_address=? AND created_at >= datetime('now', ?)""",
            (ip_address, f"-{int(hours)} hours"),
        ).fetchone()
    return int(row["total"])


def create_inquiry(name, email, channel_url, inquiry_type, message, locale, ip_address, path=DATABASE_PATH):
    with transaction(path) as connection:
        cursor = connection.execute(
            """INSERT INTO collaboration_inquiries
               (name,email,channel_url,inquiry_type,message,locale,ip_address)
               VALUES (?,?,?,?,?,?,?)""",
            (name, email, channel_url, inquiry_type, message, locale, ip_address),
        )
        return cursor.lastrowid


def list_inquiries(limit=250, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT * FROM collaboration_inquiries ORDER BY created_at DESC LIMIT ?",
            (int(limit),),
        ).fetchall()


def set_inquiry_status(inquiry_id, status, path=DATABASE_PATH):
    if status not in {"new", "reviewed", "closed"}:
        return False
    with transaction(path) as connection:
        cursor = connection.execute(
            "UPDATE collaboration_inquiries SET status=? WHERE id=?",
            (status, int(inquiry_id)),
        )
        return cursor.rowcount == 1
