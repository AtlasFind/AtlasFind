PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS admin_login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    ip_address TEXT,
    successful INTEGER NOT NULL DEFAULT 0,
    attempted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user_id INTEGER REFERENCES admin_users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    summary TEXT,
    before_json TEXT,
    after_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE tools ADD COLUMN status TEXT NOT NULL DEFAULT 'published';
ALTER TABLE tools ADD COLUMN archived_at TEXT;
ALTER TABLE tools ADD COLUMN published_at TEXT;
ALTER TABLE tools ADD COLUMN image_path TEXT;

ALTER TABLE articles ADD COLUMN status TEXT NOT NULL DEFAULT 'published';
ALTER TABLE articles ADD COLUMN archived_at TEXT;
ALTER TABLE articles ADD COLUMN image_path TEXT;

UPDATE tools SET status = 'published', published_at = COALESCE(published_at, date_added, CURRENT_TIMESTAMP) WHERE status IS NULL OR status = '';
UPDATE articles SET status = 'published' WHERE status IS NULL OR status = '';

CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_admin_audit_created ON admin_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_attempts_username ON admin_login_attempts(username, attempted_at DESC);
