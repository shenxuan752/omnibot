-- Create table for private Zeus chat logs
CREATE TABLE zeus_chat_log (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    platform TEXT NOT NULL, -- 'telegram_private'
    emotion_tag TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_zeus_chat_created 
ON zeus_chat_log(created_at DESC);

CREATE INDEX idx_zeus_chat_user 
ON zeus_chat_log(user_id, created_at DESC);

-- Create table for reminders/events (Renamed to zeus_reminders)
CREATE TABLE zeus_reminders (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    content TEXT NOT NULL, -- The event description (e.g., "Interview with Google")
    event_time TIMESTAMPTZ NOT NULL, -- When the event is happening
    reminder_time TIMESTAMPTZ NOT NULL, -- When to send the check-in (e.g., 1 hour after event)
    status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'cancelled'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_zeus_reminders_status_time 
ON zeus_reminders(status, reminder_time);
