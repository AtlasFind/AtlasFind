ALTER TABLE user_accounts ADD COLUMN display_name TEXT;
ALTER TABLE user_accounts ADD COLUMN bio TEXT;
ALTER TABLE user_accounts ADD COLUMN country TEXT;
ALTER TABLE user_accounts ADD COLUMN website_url TEXT;
ALTER TABLE user_accounts ADD COLUMN profile_visibility TEXT NOT NULL DEFAULT 'private';
ALTER TABLE user_accounts ADD COLUMN profile_updated_at TEXT;
