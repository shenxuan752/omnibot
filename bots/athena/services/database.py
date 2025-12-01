import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class DatabaseService:
    def __init__(self):
        if SUPABASE_URL and SUPABASE_KEY:
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        else:
            self.supabase = None
            print("Warning: Supabase credentials not found. Database disabled.")

    async def save_message(self, user_id: str, role: str, content: str, platform: str, bot_name: str = "athena", emotion_tag: str = None, chat_id: str = None):
        """Save a message to the appropriate chat log table."""
        if not self.supabase:
            return

        # If chat_id is not provided, use user_id (for private chats)
        target_chat_id = str(chat_id) if chat_id else str(user_id)
        created_at = datetime.utcnow().isoformat()

        try:
            if platform == 'telegram_private':
                data = {
                    "user_id": str(user_id),
                    "role": role,
                    "content": content,
                    "platform": platform,
                    "emotion_tag": emotion_tag,
                    "created_at": created_at
                }
                self.supabase.table("athena_chat_log").insert(data).execute()
            else:
                # For group chats, check if this exact user message was already saved (deduplication)
                if role == "user":
                    # Check if message exists in the last 10 seconds
                    from datetime import timedelta
                    ten_seconds_ago = (datetime.utcnow() - timedelta(seconds=10)).isoformat()
                    
                    existing = self.supabase.table("family_chat_logs") \
                        .select("id") \
                        .eq("user_id", str(user_id)) \
                        .eq("role", "user") \
                        .eq("content", content) \
                        .eq("platform", platform) \
                        .gte("created_at", ten_seconds_ago) \
                        .execute()
                    
                    if existing.data and len(existing.data) > 0:
                        print(f"Skipping duplicate user message: {content[:50]}...")
                        # return  # Skip saving duplicate
                        pass
                
                # Default to family_chat_logs for group or other platforms
                data = {
                    "user_id": str(user_id),
                    "chat_id": target_chat_id,
                    "bot_name": bot_name if role == "assistant" else None,
                    "role": role,
                    "content": content,
                    "platform": platform,
                    "emotion_tag": emotion_tag,
                    "created_at": created_at
                }
                self.supabase.table("family_chat_logs").insert(data).execute()
        except Exception as e:
            print(f"Failed to save message: {e}")

    async def get_recent_context(self, user_id: str, limit: int = 500):
        """Deprecated: Use get_combined_context instead."""
        return await self.get_combined_context(user_id, limit)

    async def get_combined_context(self, user_id: str, limit: int = 200):
        """Fetch and combine context from both private and group chats."""
        if not self.supabase:
            return []

        try:
            # Fetch private chats
            private_response = self.supabase.table("athena_chat_log") \
                .select("*") \
                .eq("user_id", str(user_id)) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            # Fetch group chats
            group_response = self.supabase.table("family_chat_logs") \
                .select("*") \
                .eq("user_id", str(user_id)) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

            combined = []
            
            # Process private chats
            for msg in private_response.data:
                msg['is_group'] = False
                combined.append(msg)
                
            # Process group chats
            for msg in group_response.data:
                msg['is_group'] = True
                combined.append(msg)
            
            # Sort by created_at ascending (oldest first) for context window
            # But first we need to sort descending to get the absolute latest across both, then reverse
            combined.sort(key=lambda x: x['created_at'], reverse=True)
            combined = combined[:limit]
            combined.sort(key=lambda x: x['created_at'])
            
            return combined
        except Exception as e:
            print(f"Failed to fetch combined context: {e}")
            return []

    async def add_reminder(self, user_id: str, chat_id: str, content: str, event_time: datetime, reminder_time: datetime):
        """Add a new reminder."""
        if not self.supabase: return
        
        data = {
            "user_id": str(user_id),
            "chat_id": str(chat_id),
            "content": content,
            "event_time": event_time.isoformat(),
            "reminder_time": reminder_time.isoformat(),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        try:
            self.supabase.table("athena_reminders").insert(data).execute()
            print(f"Reminder added for {user_id}: {content} at {reminder_time}")
        except Exception as e:
            print(f"Failed to add reminder: {e}")

    async def get_due_reminders(self):
        """Get reminders that are due."""
        if not self.supabase: return []
        
        now = datetime.utcnow().isoformat()
        try:
            response = self.supabase.table("athena_reminders") \
                .select("*") \
                .eq("status", "pending") \
                .lte("reminder_time", now) \
                .execute()
            return response.data
        except Exception as e:
            print(f"Failed to get due reminders: {e}")
            return []

    async def mark_reminder_sent(self, reminder_id: int):
        """Mark a reminder as sent."""
        if not self.supabase: return
        
        try:
            self.supabase.table("athena_reminders") \
                .update({"status": "sent"}) \
                .eq("id", reminder_id) \
                .execute()
        except Exception as e:
            print(f"Failed to mark reminder sent: {e}")

    async def get_family_group_id(self):
        """Find the most recent group chat ID."""
        if not self.supabase:
            return None
            
        try:
            response = self.supabase.table("family_chat_logs") \
                .select("chat_id") \
                .eq("platform", "telegram_group") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['chat_id']
            return None
        except Exception as e:
            print(f"Failed to get group ID: {e}")
            return None
