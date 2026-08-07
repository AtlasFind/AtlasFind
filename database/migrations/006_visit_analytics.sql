CREATE TABLE IF NOT EXISTS visit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    country_code TEXT NOT NULL DEFAULT 'Unknown',
    path TEXT NOT NULL,
    user_agent TEXT NOT NULL DEFAULT '',
    visited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_visit_events_visited_at ON visit_events(visited_at DESC);
CREATE INDEX IF NOT EXISTS idx_visit_events_visitor_time ON visit_events(visitor_id, visited_at DESC);
CREATE INDEX IF NOT EXISTS idx_visit_events_country_time ON visit_events(country_code, visited_at DESC);
