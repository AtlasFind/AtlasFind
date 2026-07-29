CREATE TABLE IF NOT EXISTS rating_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_slug TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unreviewed',
    methodology_version TEXT NOT NULL,
    category_profile TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    reviewed_by INTEGER,
    approved_by INTEGER,
    reviewed_at TEXT,
    next_review_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_slug, methodology_version),
    FOREIGN KEY(reviewed_by) REFERENCES admins(id),
    FOREIGN KEY(approved_by) REFERENCES admins(id)
);
CREATE TABLE IF NOT EXISTS rating_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_slug TEXT NOT NULL,
    old_score REAL,
    new_score REAL,
    criterion TEXT,
    reason TEXT NOT NULL,
    changed_by INTEGER,
    approved_by INTEGER,
    methodology_version TEXT NOT NULL,
    sources_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_slug TEXT NOT NULL,
    user_key_hash TEXT NOT NULL,
    score REAL NOT NULL CHECK(score >= 0 AND score <= 10),
    criteria_json TEXT NOT NULL DEFAULT '{}',
    comment TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    risk_score INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_slug, user_key_hash)
);
CREATE INDEX IF NOT EXISTS idx_rating_reviews_status ON rating_reviews(status);
CREATE INDEX IF NOT EXISTS idx_rating_reviews_tool ON rating_reviews(tool_slug);
CREATE INDEX IF NOT EXISTS idx_user_reviews_tool_status ON user_reviews(tool_slug, status);
