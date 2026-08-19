ALTER TABLE tools ADD COLUMN is_featured INTEGER NOT NULL DEFAULT 0;
ALTER TABLE tools ADD COLUMN is_sponsored INTEGER NOT NULL DEFAULT 0;
ALTER TABLE tools ADD COLUMN featured_until TEXT;
ALTER TABLE tools ADD COLUMN sponsor_plan TEXT;
ALTER TABLE tools ADD COLUMN affiliate_url TEXT;
CREATE INDEX IF NOT EXISTS idx_tools_featured_until ON tools(is_featured, featured_until);
