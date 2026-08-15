PRAGMA foreign_keys = ON;

ALTER TABLE user_accounts ADD COLUMN avatar_data BLOB;
ALTER TABLE user_accounts ADD COLUMN avatar_mime TEXT;
ALTER TABLE user_accounts ADD COLUMN custom_rank TEXT;
ALTER TABLE user_accounts ADD COLUMN staff_badge TEXT;

CREATE TABLE IF NOT EXISTS tool_comment_likes (
    comment_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(comment_id,user_id),
    FOREIGN KEY(comment_id) REFERENCES tool_comments(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES user_accounts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_comment_likes_user ON tool_comment_likes(user_id);
