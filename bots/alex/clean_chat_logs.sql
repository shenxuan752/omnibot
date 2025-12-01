-- SQL to clean up 'telegram_elena' records from chat_logs

-- 1. First, verify the records you want to delete (Optional but recommended)
-- Run this to see what will be deleted:
SELECT * FROM chat_logs WHERE user_id = 'telegram_elena';

-- 2. Delete the records
DELETE FROM chat_logs WHERE user_id = 'telegram_elena';

-- 3. Verify they are gone
SELECT COUNT(*) FROM chat_logs WHERE user_id = 'telegram_elena';
