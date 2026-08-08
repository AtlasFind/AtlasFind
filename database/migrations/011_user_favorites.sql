CREATE TABLE IF NOT EXISTS user_favorites (
    user_id INTEGER NOT NULL,
    tool_slug TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, tool_slug),
    FOREIGN KEY(user_id) REFERENCES user_accounts(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_user_favorites_user ON user_favorites(user_id, created_at DESC);
