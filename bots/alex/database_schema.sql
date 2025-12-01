-- Create alex_scheduled_messages table for Alex's time-based reminders
CREATE TABLE IF NOT EXISTS alex_scheduled_messages (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    message_content TEXT NOT NULL,
    context TEXT,
    is_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for efficient querying of pending messages
CREATE INDEX IF NOT EXISTS idx_alex_scheduled_messages_pending 
ON alex_scheduled_messages (is_sent, scheduled_time) 
WHERE is_sent = FALSE;

-- Create index for user lookups
CREATE INDEX IF NOT EXISTS idx_alex_scheduled_messages_user 
ON alex_scheduled_messages (user_id);
