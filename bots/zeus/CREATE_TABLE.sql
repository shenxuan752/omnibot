-- Family Chat Logs Table (Shared by Athena and Zeus)
CREATE TABLE family_chat_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT,           -- Group Chat ID or User ID
    bot_name TEXT,          -- 'athena' or 'zeus'
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    platform TEXT NOT NULL, -- 'telegram' or 'telegram_group'
    emotion_tag TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_family_chat_created 
ON family_chat_logs(created_at DESC);

CREATE INDEX idx_family_chat_bot 
ON family_chat_logs(bot_name, created_at DESC);
