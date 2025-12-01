# Database Setup Instructions

## Create the alex_scheduled_messages Table in Supabase

1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Run the following SQL:

```sql
CREATE TABLE IF NOT EXISTS alex_scheduled_messages (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    message_content TEXT NOT NULL,
    context TEXT,
    is_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alex_scheduled_messages_pending 
ON alex_scheduled_messages (is_sent, scheduled_time) 
WHERE is_sent = FALSE;

CREATE INDEX IF NOT EXISTS idx_alex_scheduled_messages_user 
ON alex_scheduled_messages (user_id);
```

## Verify Table Creation

Run this query to verify:
```sql
SELECT * FROM alex_scheduled_messages LIMIT 1;
```

You should see an empty table with the correct columns.
