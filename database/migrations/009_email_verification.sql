ALTER TABLE user_accounts ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0;
ALTER TABLE user_accounts ADD COLUMN verification_token_hash TEXT;
ALTER TABLE user_accounts ADD COLUMN verification_expires_at TEXT;
ALTER TABLE user_accounts ADD COLUMN verification_sent_at TEXT;

CREATE INDEX IF NOT EXISTS idx_user_accounts_verification_token
ON user_accounts(verification_token_hash);
