-- Add reminder_type column to zeus_reminders table
ALTER TABLE zeus_reminders 
ADD COLUMN reminder_type TEXT DEFAULT 'post_event';

-- Update index comment for clarity
COMMENT ON COLUMN zeus_reminders.reminder_type IS 'Type of reminder: pre_event or post_event';
