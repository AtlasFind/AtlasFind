from database import DATABASE_PATH, connect_database, transaction


def list_tool_comments(tool_slug, viewer_user_id=None, limit=100, path=DATABASE_PATH):
    with connect_database(path) as connection:
        rows = connection.execute(
            """SELECT c.id,c.tool_slug,c.user_id,c.parent_id,c.body,c.status,c.created_at,c.updated_at,
                      u.username,u.display_name,u.profile_visibility,u.custom_rank,u.staff_badge,
                      CASE WHEN u.avatar_data IS NOT NULL THEN 1 ELSE 0 END AS has_avatar,
                      (SELECT COUNT(*) FROM tool_comment_likes l WHERE l.comment_id=c.id) AS like_count,
                      (SELECT COUNT(*) FROM tool_comments uc WHERE uc.user_id=u.id AND uc.status='visible') AS author_comment_count,
                      (SELECT COUNT(*) FROM tool_comment_likes ul JOIN tool_comments uc ON uc.id=ul.comment_id WHERE uc.user_id=u.id AND uc.status='visible') AS author_like_count,
                      EXISTS(SELECT 1 FROM tool_comment_likes l WHERE l.comment_id=c.id AND l.user_id=?) AS viewer_liked
               FROM tool_comments c
               JOIN user_accounts u ON u.id=c.user_id AND u.is_active=1
               WHERE c.tool_slug=? AND c.status IN ('visible','deleted')
               ORDER BY CASE WHEN c.parent_id IS NULL THEN c.created_at ELSE
                   (SELECT created_at FROM tool_comments p WHERE p.id=c.parent_id) END DESC,
                   c.parent_id IS NOT NULL, c.created_at ASC LIMIT ?""",
            (int(viewer_user_id or 0), tool_slug, int(limit)),
        ).fetchall()
    parents, replies = [], {}
    for row in rows:
        item = dict(row)
        item["author_name"] = item.get("display_name") or item.get("username")
        item["profile_public"] = item.get("profile_visibility") == "public"
        score = int(item.get("author_comment_count") or 0) + int(item.get("author_like_count") or 0) * 5
        item["author_rank"] = item.get("custom_rank") or ("Atlas Ustası" if score >= 400 else "Uzman" if score >= 150 else "Kaşif" if score >= 50 else "Katılımcı" if score >= 10 else "Yeni Üye")
        if item.get("parent_id") is None:
            item["replies"] = []
            parents.append(item)
        else:
            replies.setdefault(item["parent_id"], []).append(item)
    for parent in parents:
        parent["replies"] = replies.get(parent["id"], [])
    return parents


def toggle_comment_like(comment_id, user_id, path=DATABASE_PATH):
    with transaction(path) as connection:
        comment = connection.execute("SELECT id FROM tool_comments WHERE id=? AND status='visible'", (int(comment_id),)).fetchone()
        if not comment:
            return None
        existing = connection.execute("SELECT 1 FROM tool_comment_likes WHERE comment_id=? AND user_id=?", (int(comment_id), int(user_id))).fetchone()
        if existing:
            connection.execute("DELETE FROM tool_comment_likes WHERE comment_id=? AND user_id=?", (int(comment_id), int(user_id)))
            return False
        connection.execute("INSERT INTO tool_comment_likes(comment_id,user_id) VALUES (?,?)", (int(comment_id), int(user_id)))
        return True


def get_discussion_state(user_id, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            """SELECT strike_count,banned_until,last_reason,
                      CASE WHEN banned_until IS NOT NULL AND banned_until>CURRENT_TIMESTAMP THEN 1 ELSE 0 END AS is_banned
               FROM user_discussion_sanctions WHERE user_id=?""",
            (int(user_id),),
        ).fetchone()


def create_tool_comment(tool_slug, user_id, body, parent_id=None, path=DATABASE_PATH):
    with transaction(path) as connection:
        if parent_id is not None:
            parent = connection.execute(
                "SELECT id FROM tool_comments WHERE id=? AND tool_slug=? AND status='visible' AND parent_id IS NULL",
                (int(parent_id), tool_slug),
            ).fetchone()
            if not parent:
                return None
        cursor = connection.execute(
            "INSERT INTO tool_comments(tool_slug,user_id,parent_id,body) VALUES (?,?,?,?)",
            (tool_slug, int(user_id), int(parent_id) if parent_id is not None else None, body),
        )
        return cursor.lastrowid


def delete_own_comment(comment_id, user_id, tool_slug, path=DATABASE_PATH):
    with transaction(path) as connection:
        cursor = connection.execute(
            """UPDATE tool_comments SET status='deleted',body='',updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND user_id=? AND tool_slug=? AND status='visible'""",
            (int(comment_id), int(user_id), tool_slug),
        )
        return cursor.rowcount == 1


def recent_comment_count(user_id, minutes=10, path=DATABASE_PATH):
    with connect_database(path) as connection:
        row = connection.execute(
            """SELECT COUNT(*) AS total FROM tool_comments WHERE user_id=?
               AND created_at>=datetime('now', ?)""",
            (int(user_id), f"-{int(minutes)} minutes"),
        ).fetchone()
    return int(row["total"])


def apply_discussion_violation(user_id, tool_slug, reason, excerpt, path=DATABASE_PATH):
    durations = (1, 24, 168, 720)
    with transaction(path) as connection:
        row = connection.execute(
            "SELECT strike_count FROM user_discussion_sanctions WHERE user_id=?",
            (int(user_id),),
        ).fetchone()
        strikes = int(row["strike_count"] if row else 0) + 1
        hours = durations[min(strikes - 1, len(durations) - 1)]
        connection.execute(
            """INSERT INTO user_discussion_sanctions(user_id,strike_count,banned_until,last_reason)
               VALUES (?,?,datetime('now', ?),?)
               ON CONFLICT(user_id) DO UPDATE SET strike_count=excluded.strike_count,
               banned_until=excluded.banned_until,last_reason=excluded.last_reason,updated_at=CURRENT_TIMESTAMP""",
            (int(user_id), strikes, f"+{hours} hours", reason),
        )
        connection.execute(
            """INSERT INTO discussion_moderation_events(user_id,tool_slug,action,reason,content_excerpt)
               VALUES (?,?,'automatic_chat_ban',?,?)""",
            (int(user_id), tool_slug, reason, excerpt[:180]),
        )
    return {"strikes": strikes, "hours": hours}
