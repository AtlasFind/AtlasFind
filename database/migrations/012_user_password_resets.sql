ALTER TABLE user_accounts ADD COLUMN password_reset_token_hash TEXT;
ALTER TABLE user_accounts ADD COLUMN password_reset_expires_at TEXT;
ALTER TABLE user_accounts ADD COLUMN password_reset_sent_at TEXT;
CREATE INDEX IF NOT EXISTS idx_user_password_reset_token ON user_accounts(password_reset_token_hash);
