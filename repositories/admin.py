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


def get_dashboard_overview(path=DATABASE_PATH):
    """Return the actionable dataset shown on the admin landing page."""
    with connect_database(path) as connection:
        counts = dashboard_counts(path)
        taxonomy = connection.execute(
            "SELECT (SELECT COUNT(*) FROM categories) AS categories, "
            "(SELECT COUNT(*) FROM tags) AS tags"
        ).fetchone()
        images = connection.execute(
            """SELECT COUNT(*) AS missing FROM tools
               WHERE status != 'archived'
                 AND COALESCE(json_extract(payload_json, '$.branding.logo.status'), 'missing')
                     IN ('missing', 'broken', 'pending')"""
        ).fetchone()
        descriptions = connection.execute(
            """SELECT COUNT(*) AS missing FROM tools
               WHERE status != 'archived'
                 AND length(trim(COALESCE(json_extract(payload_json, '$.description'), ''))) < 80"""
        ).fetchone()
        uncategorized = connection.execute(
            """SELECT COUNT(*) AS missing FROM tools t LEFT JOIN categories c ON c.id=t.category_id
               WHERE t.status != 'archived' AND (c.id IS NULL OR c.slug='uncategorized')"""
        ).fetchone()
        audit_total = connection.execute("SELECT COUNT(*) AS total FROM admin_audit_logs").fetchone()

    todo_items = [
        {"label": "Logo or image review", "description": "Tools without a verified visual asset", "count": int(images["missing"]), "tone": "critical" if images["missing"] else "success", "url": "/admin/images"},
        {"label": "Short descriptions", "description": "Descriptions under 80 characters", "count": int(descriptions["missing"]), "tone": "warning" if descriptions["missing"] else "success", "url": "/admin/tools"},
        {"label": "Uncategorized tools", "description": "Tools that need a clear category", "count": int(uncategorized["missing"]), "tone": "warning" if uncategorized["missing"] else "success", "url": "/admin/tools"},
        {"label": "Content review due", "description": "Freshness checks that need attention", "count": int(counts["review_due"] or 0), "tone": "critical" if counts["review_due"] else "success", "url": "/admin/tools"},
        {"label": "Draft content", "description": "Tools and articles not yet published", "count": int(counts["tools"]["draft"] or 0) + int(counts["articles"]["draft"] or 0), "tone": "neutral", "url": "/admin/tools"},
    ]
    return {
        "counts": counts, "taxonomy": dict(taxonomy), "todo_items": todo_items,
        "system_status": [
            {"label": "Database", "detail": "Connected", "tone": "success"},
            {"label": "Catalog", "detail": f"{counts['tools']['total'] or 0} tools indexed", "tone": "success"},
            {"label": "Audit log", "detail": f"{audit_total['total'] or 0} events recorded", "tone": "success"},
            {"label": "Content review", "detail": f"{counts['review_due'] or 0} items due", "tone": "warning" if counts["review_due"] else "success"},
        ],
    }


def record_visit(visitor_id, ip_address, country_code, path, user_agent, database_path=DATABASE_PATH):
    """Persist one successful public page view for the lightweight admin analytics."""
    with transaction(database_path) as connection:
        connection.execute(
            """INSERT INTO visit_events(visitor_id, ip_address, country_code, path, user_agent)
               VALUES (?, ?, ?, ?, ?)""",
            (visitor_id[:80], ip_address[:120], country_code[:32], path[:500], user_agent[:500]),
        )


def get_traffic_overview(path=DATABASE_PATH):
    """Return privacy-conscious visitor aggregates and recent diagnostics."""
    with connect_database(path) as connection:
        daily = connection.execute(
            "SELECT COUNT(DISTINCT visitor_id) AS total FROM visit_events WHERE visited_at >= date('now')"
        ).fetchone()["total"]
        previous_daily = connection.execute(
            """SELECT COUNT(DISTINCT visitor_id) AS total FROM visit_events
               WHERE visited_at >= date('now', '-1 day') AND visited_at < date('now')"""
        ).fetchone()["total"]
        monthly = connection.execute(
            "SELECT COUNT(DISTINCT visitor_id) AS total FROM visit_events WHERE visited_at >= datetime('now', '-30 days')"
        ).fetchone()["total"]
        previous_monthly = connection.execute(
            """SELECT COUNT(DISTINCT visitor_id) AS total FROM visit_events
               WHERE visited_at >= datetime('now', '-60 days') AND visited_at < datetime('now', '-30 days')"""
        ).fetchone()["total"]
        active = connection.execute(
            "SELECT COUNT(DISTINCT visitor_id) AS total FROM visit_events WHERE visited_at >= datetime('now', '-5 minutes')"
        ).fetchone()["total"]
        countries = connection.execute(
            """SELECT country_code, COUNT(DISTINCT visitor_id) AS visitors
               FROM visit_events WHERE visited_at >= datetime('now', '-30 days')
               GROUP BY country_code ORDER BY visitors DESC, country_code LIMIT 5"""
        ).fetchall()
        recent_visitors = connection.execute(
            """SELECT ip_address, country_code, path, MAX(visited_at) AS visited_at
               FROM visit_events GROUP BY visitor_id
               ORDER BY visited_at DESC LIMIT 8"""
        ).fetchall()

    def change(current, previous):
        if not previous:
            return None if not current else 100
        return round(((current - previous) / previous) * 100)

    return {
        "daily": int(daily or 0), "monthly": int(monthly or 0), "active": int(active or 0),
        "daily_change": change(int(daily or 0), int(previous_daily or 0)),
        "monthly_change": change(int(monthly or 0), int(previous_monthly or 0)),
        "countries": [dict(row) for row in countries],
        "recent_visitors": [dict(row) for row in recent_visitors],
    }
