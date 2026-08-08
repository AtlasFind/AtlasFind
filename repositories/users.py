from database import DATABASE_PATH, connect_database, transaction


def get_user_by_id(user_id, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT id,username,email,locale,email_verified,created_at,last_login_at FROM user_accounts WHERE id=? AND is_active=1",
            (int(user_id),),
        ).fetchone()


def get_user_for_login(identity, path=DATABASE_PATH):
    with connect_database(path) as connection:
        return connection.execute(
            "SELECT * FROM user_accounts WHERE is_active=1 AND (lower(email)=lower(?) OR lower(username)=lower(?))",
            (identity, identity),
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
