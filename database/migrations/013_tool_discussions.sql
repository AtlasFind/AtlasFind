PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tool_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_slug TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    parent_id INTEGER,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'visible' CHECK(status IN ('visible','deleted','moderated')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT,
    FOREIGN KEY(user_id) REFERENCES user_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY(parent_id) REFERENCES tool_comments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tool_comments_tool_created
ON tool_comments(tool_slug, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tool_comments_parent
ON tool_comments(parent_id, created_at ASC);

CREATE TABLE IF NOT EXISTS user_discussion_sanctions (
    user_id INTEGER PRIMARY KEY,
    strike_count INTEGER NOT NULL DEFAULT 0,
    banned_until TEXT,
    last_reason TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES user_accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS discussion_moderation_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tool_slug TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    content_excerpt TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES user_accounts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_discussion_events_user_created
ON discussion_moderation_events(user_id, created_at DESC);
