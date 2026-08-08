PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS collaboration_inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    channel_url TEXT NOT NULL DEFAULT '',
    inquiry_type TEXT NOT NULL DEFAULT 'feedback',
    message TEXT NOT NULL,
    locale TEXT NOT NULL DEFAULT 'tr',
    ip_address TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collaboration_inquiries_status_created
ON collaboration_inquiries(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_collaboration_inquiries_ip_created
ON collaboration_inquiries(ip_address, created_at DESC);
