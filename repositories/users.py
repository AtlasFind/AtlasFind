from database import DATABASE_PATH, connect_database, transaction


def get_user_by_id(user_id, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            """SELECT id,username,email,locale,email_verified,display_name,bio,country,website_url,
               profile_visibility,profile_updated_at,created_at,last_login_at
               FROM user_accounts WHERE id=? AND is_active=1""",
            (int(user_id),),
        ).fetchone()


def get_user_for_login(identity, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT * FROM user_accounts WHERE is_active=1 AND (lower(email)=lower(?) OR lower(username)=lower(?))",
            (identity, identity),
        ).fetchone()


def get_user_by_email(email, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT * FROM user_accounts WHERE is_active=1 AND lower(email)=lower(?)",
            (email,),
        ).fetchone()


def get_public_user(username, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            """SELECT id,username,display_name,bio,country,website_url,created_at
               FROM user_accounts WHERE lower(username)=lower(?) AND is_active=1
               AND email_verified=1 AND profile_visibility='public'""",
            (username,),
        ).fetchone()


def create_user(username, email, password_hash, locale, path=DATABASE_PATH):
    with transaction(path) as connection:
        cursor = connection.execute(
            "INSERT INTO user_accounts(username,email,password_hash,locale) VALUES (?,?,?,?)",
            (username, email, password_hash, locale),
        )
        return cursor.lastrowid


def user_exists(username, email, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT 1 FROM user_accounts WHERE lower(username)=lower(?) OR lower(email)=lower(?)",
            (username, email),
        ).fetchone() is not None


def record_user_login(identity, ip_address, successful, user_id=None, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute(
            "INSERT INTO user_login_attempts(identity,ip_address,successful) VALUES (?,?,?)",
            (identity[:180], ip_address[:120], int(bool(successful))),
        )
        if successful and user_id:
            connection.execute(
                "UPDATE user_accounts SET last_login_at=CURRENT_TIMESTAMP WHERE id=?",
                (int(user_id),),
            )


def recent_failed_user_logins(identity, ip_address, minutes=15, path=DATABASE_PATH):
    with connect_database(path) as connection:
        row = connection.execute(
            """SELECT COUNT(*) AS total FROM user_login_attempts
               WHERE lower(identity)=lower(?) AND ip_address=? AND successful=0
               AND attempted_at >= datetime('now', ?)""",
            (identity, ip_address, f"-{int(minutes)} minutes"),
        ).fetchone()
    return int(row["total"])


def set_verification_token(user_id, token_hash, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute(
            """UPDATE user_accounts SET verification_token_hash=?,
               verification_expires_at=datetime('now', '+24 hours'),
               verification_sent_at=CURRENT_TIMESTAMP WHERE id=?""",
            (token_hash, int(user_id)),
        )


def verify_user_email(token_hash, path=DATABASE_PATH):
    with transaction(path) as connection:
        user = connection.execute(
            """SELECT id FROM user_accounts WHERE verification_token_hash=?
               AND verification_expires_at >= CURRENT_TIMESTAMP AND is_active=1""",
            (token_hash,),
        ).fetchone()
        if not user:
            return None
        connection.execute(
            """UPDATE user_accounts SET email_verified=1, verification_token_hash=NULL,
               verification_expires_at=NULL WHERE id=?""",
            (user["id"],),
        )
        return user["id"]


def list_users(search="", status="all", path=DATABASE_PATH):
    clauses, params = [], []
    if search:
        clauses.append("(lower(username) LIKE lower(?) OR lower(email) LIKE lower(?))")
        term = f"%{search[:120]}%"
        params.extend((term, term))
    if status == "verified":
        clauses.append("email_verified=1 AND is_active=1")
    elif status == "unverified":
        clauses.append("email_verified=0 AND is_active=1")
    elif status == "disabled":
        clauses.append("is_active=0")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect_database(path) as connection:
        return connection.execute(
            f"""SELECT id,username,email,locale,email_verified,is_active,created_at,last_login_at,
                verification_sent_at FROM user_accounts {where} ORDER BY created_at DESC LIMIT 500""",
            params,
        ).fetchall()


def user_account_counts(path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            """SELECT COUNT(*) total,
               SUM(CASE WHEN email_verified=1 AND is_active=1 THEN 1 ELSE 0 END) verified,
               SUM(CASE WHEN email_verified=0 AND is_active=1 THEN 1 ELSE 0 END) unverified,
               SUM(CASE WHEN is_active=0 THEN 1 ELSE 0 END) disabled
               FROM user_accounts"""
        ).fetchone()


def set_user_active(user_id, active, path=DATABASE_PATH):
    with transaction(path) as connection:
        cursor = connection.execute(
            "UPDATE user_accounts SET is_active=? WHERE id=?",
            (int(bool(active)), int(user_id)),
        )
        return cursor.rowcount == 1


def update_user_profile(user_id, display_name, bio, country, website_url, visibility, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute(
            """UPDATE user_accounts SET display_name=?,bio=?,country=?,website_url=?,
               profile_visibility=?,profile_updated_at=CURRENT_TIMESTAMP WHERE id=? AND is_active=1""",
            (display_name or None, bio or None, country or None, website_url or None, visibility, int(user_id)),
        )


def update_user_password(user_id, password_hash, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute(
            "UPDATE user_accounts SET password_hash=? WHERE id=? AND is_active=1",
            (password_hash, int(user_id)),
        )


def set_password_reset_token(user_id, token_hash, path=DATABASE_PATH):
    with transaction(path) as connection:
        connection.execute(
            """UPDATE user_accounts SET password_reset_token_hash=?,
               password_reset_expires_at=datetime('now', '+1 hour'),
               password_reset_sent_at=CURRENT_TIMESTAMP WHERE id=? AND is_active=1""",
            (token_hash, int(user_id)),
        )


def consume_password_reset_token(token_hash, password_hash, path=DATABASE_PATH):
    with transaction(path) as connection:
        user = connection.execute(
            """SELECT id FROM user_accounts WHERE password_reset_token_hash=?
               AND password_reset_expires_at >= CURRENT_TIMESTAMP AND is_active=1""",
            (token_hash,),
        ).fetchone()
        if not user:
            return None
        connection.execute(
            """UPDATE user_accounts SET password_hash=?,password_reset_token_hash=NULL,
               password_reset_expires_at=NULL,password_reset_sent_at=NULL WHERE id=?""",
            (password_hash, user["id"]),
        )
        return user["id"]


def list_user_favorites(user_id, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT tool_slug,created_at FROM user_favorites WHERE user_id=? ORDER BY created_at DESC",
            (int(user_id),),
        ).fetchall()


def is_user_favorite(user_id, tool_slug, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT 1 FROM user_favorites WHERE user_id=? AND tool_slug=?",
            (int(user_id), tool_slug),
        ).fetchone() is not None


def set_user_favorite(user_id, tool_slug, saved, path=DATABASE_PATH):
    with transaction(path) as connection:
        if saved:
            connection.execute(
                "INSERT OR IGNORE INTO user_favorites(user_id,tool_slug) VALUES (?,?)",
                (int(user_id), tool_slug),
            )
        else:
            connection.execute(
                "DELETE FROM user_favorites WHERE user_id=? AND tool_slug=?",
                (int(user_id), tool_slug),
            )


def anonymize_user_account(user_id, replacement_password_hash, path=DATABASE_PATH):
    with transaction(path) as connection:
        user = connection.execute("SELECT username,email FROM user_accounts WHERE id=? AND is_active=1", (int(user_id),)).fetchone()
        if not user:
            return False
        connection.execute("DELETE FROM user_favorites WHERE user_id=?", (int(user_id),))
        connection.execute("DELETE FROM user_login_attempts WHERE lower(identity) IN (lower(?),lower(?))", (user["username"], user["email"]))
        connection.execute(
            """UPDATE user_accounts SET username=?,email=?,password_hash=?,locale='tr',is_active=0,
               email_verified=0,verification_token_hash=NULL,verification_expires_at=NULL,
               verification_sent_at=NULL,password_reset_token_hash=NULL,password_reset_expires_at=NULL,
               password_reset_sent_at=NULL,display_name=NULL,bio=NULL,country=NULL,website_url=NULL,
               profile_visibility='private',profile_updated_at=CURRENT_TIMESTAMP,last_login_at=NULL WHERE id=?""",
            (f"deleted_{int(user_id)}", f"deleted_{int(user_id)}@invalid.local", replacement_password_hash, int(user_id)),
        )
        return True
