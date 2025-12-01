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

-- Private Athena Chat Logs
CREATE TABLE athena_chat_log (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    platform TEXT NOT NULL, -- 'telegram_private'
    emotion_tag TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Athena Reminders
CREATE TABLE athena_reminders (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    content TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    reminder_time TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_family_chat_created ON family_chat_logs(created_at DESC);
CREATE INDEX idx_family_chat_bot ON family_chat_logs(bot_name, created_at DESC);
CREATE INDEX idx_athena_chat_created ON athena_chat_log(created_at DESC);
CREATE INDEX idx_athena_chat_user ON athena_chat_log(user_id, created_at DESC);
CREATE INDEX idx_athena_reminders_status_time ON athena_reminders(status, reminder_time);
