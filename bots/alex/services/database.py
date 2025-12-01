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

    async def save_message(self, user_id: str, role: str, content: str, platform: str, media_type: str = "text", media_url: str = None):
        """Save a message to the chat logs."""
        if not self.supabase:
            return

        data = {
            "user_id": str(user_id),
            "role": role,
            "content": content,
            "platform": platform,
            "created_at": datetime.utcnow().isoformat()
        }
        try:
            self.supabase.table("chat_logs").insert(data).execute()
        except Exception as e:
            print(f"Failed to save message: {e}")

    async def get_recent_context(self, user_id: str, limit: int = 5):
        """Fetch recent chat context."""
        if not self.supabase:
            return []

        try:
            response = self.supabase.table("chat_logs")                .select("*")                .eq("user_id", str(user_id))                .order("created_at", desc=True)                .limit(limit)                .execute()
            
            # Return in chronological order
            return sorted(response.data, key=lambda x: x['created_at'])
        except Exception as e:
            print(f"Failed to fetch context: {e}")
            return []

    async def save_scheduled_message(self, user_id: str, scheduled_time: datetime, message_content: str, context: str):
        """Save a scheduled message/reminder."""
        if not self.supabase:
            return

        data = {
            "user_id": str(user_id),
            "scheduled_time": scheduled_time.isoformat(),
            "message_content": message_content,
            "context": context,
            "is_sent": False,
            "created_at": datetime.utcnow().isoformat()
        }
        try:
            result = self.supabase.table("alex_scheduled_messages").insert(data).execute()
            print(f"Saved scheduled message for {scheduled_time}: {message_content[:50]}...")
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Failed to save scheduled message: {e}")
            return None

    async def get_pending_scheduled_messages(self, current_time: datetime):
        """Fetch pending scheduled messages that are due."""
        if not self.supabase:
            return []

        try:
            response = self.supabase.table("alex_scheduled_messages")                .select("*")                .eq("is_sent", False)                .lte("scheduled_time", current_time.isoformat())                .execute()
            
            return response.data
        except Exception as e:
            print(f"Failed to fetch scheduled messages: {e}")
            return []

    async def mark_message_sent(self, message_id: int):
        """Mark a scheduled message as sent."""
        if not self.supabase:
            return

        try:
            self.supabase.table("alex_scheduled_messages")                .update({"is_sent": True})                .eq("id", message_id)                .execute()
            print(f"Marked message {message_id} as sent")
        except Exception as e:
            print(f"Failed to mark message as sent: {e}")

    async def cancel_scheduled_message(self, message_id: int):
        """Cancel a scheduled message by deleting it."""
        if not self.supabase:
            return

        try:
            self.supabase.table("alex_scheduled_messages")                .delete()                .eq("id", message_id)                .execute()
            print(f"Cancelled scheduled message {message_id}")
        except Exception as e:
            print(f"Failed to cancel message: {e}")

    async def get_user_scheduled_messages(self, user_id: str, include_sent: bool = False):
        """Get all scheduled messages for a user."""
        if not self.supabase:
            return []

        try:
            query = self.supabase.table("alex_scheduled_messages")                .select("*")                .eq("user_id", str(user_id))
            
            if not include_sent:
                query = query.eq("is_sent", False)
            
            response = query.order("scheduled_time", desc=False).execute()
            return response.data
        except Exception as e:
            print(f"Failed to fetch user scheduled messages: {e}")
            return []

