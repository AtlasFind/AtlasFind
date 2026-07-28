import json
from datetime import datetime, timezone

from database import DATABASE_PATH, connect_database, transaction


def get_admin_by_username(username, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT * FROM admin_users WHERE lower(username)=lower(?) AND is_active=1",
            (username,),
        ).fetchone()


def get_admin_by_id(admin_id, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT * FROM admin_users WHERE id=? AND is_active=1", (admin_id,)
        ).fetchone()


def create_admin(username, password_hash, path=DATABASE_PATH):
    with transaction(path) as connection:
        cursor = connection.execute(
            "INSERT INTO admin_users(username,password_hash) VALUES (?,?)",
            (username.strip(), password_hash),
        )
        return cursor.lastrowid


def record_login_attempt(username, ip_address, successful, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute(
            "INSERT INTO admin_login_attempts(username,ip_address,successful) VALUES (?,?,?)",
            (username, ip_address, int(bool(successful))),
        )
        if successful:
            connection.execute(
                "UPDATE admin_users SET last_login_at=CURRENT_TIMESTAMP WHERE lower(username)=lower(?)",
                (username,),
            )


def recent_failed_attempts(username, minutes=15, path=DATABASE_PATH):
    with connect_database(path) as connection:
        row = connection.execute(
            """SELECT COUNT(*) AS count FROM admin_login_attempts
               WHERE lower(username)=lower(?) AND successful=0
               AND attempted_at >= datetime('now', ?)""",
            (username, f"-{int(minutes)} minutes"),
        ).fetchone()
    return int(row["count"])


def log_action(admin_user_id, action, entity_type=None, entity_id=None, summary=None,
               before=None, after=None, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute(
            """INSERT INTO admin_audit_logs(
                   admin_user_id,action,entity_type,entity_id,summary,before_json,after_json
               ) VALUES (?,?,?,?,?,?,?)""",
            (
                admin_user_id, action, entity_type, str(entity_id) if entity_id is not None else None,
                summary,
                json.dumps(before, ensure_ascii=False) if before is not None else None,
                json.dumps(after, ensure_ascii=False) if after is not None else None,
            ),
        )


def get_recent_audit_logs(limit=50, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            """SELECT l.*, u.username FROM admin_audit_logs l
               LEFT JOIN admin_users u ON u.id=l.admin_user_id
               ORDER BY l.id DESC LIMIT ?""",
            (int(limit),),
        ).fetchall()


def dashboard_counts(path=DATABASE_PATH):
    with connect_database(path) as connection:
        tool_counts = connection.execute(
            "SELECT COUNT(*) total, SUM(status='published') published, SUM(status='draft') draft, SUM(status='archived') archived FROM tools"
        ).fetchone()
        article_counts = connection.execute(
            "SELECT COUNT(*) total, SUM(status='published') published, SUM(status='draft') draft, SUM(status='archived') archived FROM articles"
        ).fetchone()
        due = connection.execute(
            "SELECT COUNT(*) count FROM tools WHERE json_extract(payload_json, '$.freshness.status') IN ('review-due','outdated')"
        ).fetchone()["count"]
    return {"tools": dict(tool_counts), "articles": dict(article_counts), "review_due": due}
