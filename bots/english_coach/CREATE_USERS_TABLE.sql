-- Create users table for English Coach Bot
CREATE TABLE IF NOT EXISTS english_coach_users (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_english_coach_users_user_id ON english_coach_users(user_id);
