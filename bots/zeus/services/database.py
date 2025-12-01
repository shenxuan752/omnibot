import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

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

    async def save_message(self, user_id: str, role: str, content: str, platform: str, bot_name: str = "zeus", emotion_tag: str = None, chat_id: str = None):
        """Save a message to the appropriate table based on platform."""
        if not self.supabase:
            return

        target_chat_id = str(chat_id) if chat_id else str(user_id)
        
        # Determine table based on platform
        table_name = "zeus_chat_log" if platform == "telegram_private" else "family_chat_logs"

        # Deduplication: Check if this user message already exists in group chat
        if table_name == "family_chat_logs" and role == "user":
            try:
                # Check for duplicate within last 10 seconds
                ten_seconds_ago = (datetime.utcnow() - timedelta(seconds=10)).isoformat()
                existing = self.supabase.table("family_chat_logs") \
                    .select("id") \
                    .eq("user_id", str(user_id)) \
                    .eq("role", "user") \
                    .eq("content", content) \
                    .gte("created_at", ten_seconds_ago) \
                    .execute()
                
                if existing.data and len(existing.data) > 0:
                    print(f"Skipping duplicate user message in group chat: {content[:50]}...")
                    # Relaxing deduplication for now to ensure responsiveness
                    # return False
                    pass
            except Exception as e:
                print(f"Deduplication check failed: {e}")

        data = {
            "user_id": str(user_id),
            "role": role,
            "content": content,
            "platform": platform,
            "emotion_tag": emotion_tag,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add table-specific fields
        if table_name == "family_chat_logs":
            data["chat_id"] = target_chat_id
            data["bot_name"] = bot_name if role == "assistant" else None
        
        try:
            self.supabase.table(table_name).insert(data).execute()
            return True
        except Exception as e:
            print(f"Failed to save message to {table_name}: {e}")
            return False

    async def get_combined_context(self, user_id: str, limit: int = 500):
        """Fetch and merge recent chat context from both private and family logs."""
        if not self.supabase:
            return []

        try:
            # Fetch from family logs
            family_response = self.supabase.table("family_chat_logs") \
                .select("*") \
                .eq("user_id", str(user_id)) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            # Fetch from private logs
            private_response = self.supabase.table("zeus_chat_log") \
                .select("*") \
                .eq("user_id", str(user_id)) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            # Combine and sort
            combined = family_response.data + private_response.data
            # Sort by created_at ascending (oldest first) for context window
            sorted_msgs = sorted(combined, key=lambda x: x['created_at'])
            
            # Return only the last 'limit' messages
            return sorted_msgs[-limit:]
            
        except Exception as e:
            print(f"Failed to fetch combined context: {e}")
            return []

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

    # --- Reminder System ---

    async def add_reminder(self, user_id: str, chat_id: str, content: str, event_time: datetime, reminder_time: datetime, reminder_type: str = "post_event"):
        """Add a new reminder."""
        if not self.supabase: return
        
        data = {
            "user_id": str(user_id),
            "chat_id": str(chat_id),
            "content": content,
            "event_time": event_time.isoformat(),
            "reminder_time": reminder_time.isoformat(),
            "reminder_type": reminder_type,
            "status": "pending"
        }
        
        try:
            self.supabase.table("zeus_reminders").insert(data).execute()
            print(f"Reminder added ({reminder_type}): {content} at {reminder_time}")
        except Exception as e:
            print(f"Failed to add reminder: {e}")

    async def get_due_reminders(self):
        """Get all pending reminders that are due."""
        if not self.supabase: return []
        
        now = datetime.utcnow().isoformat()
        
        try:
            response = self.supabase.table("zeus_reminders") \
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
            self.supabase.table("zeus_reminders") \
                .update({"status": "sent"}) \
                .eq("id", reminder_id) \
                .execute()
        except Exception as e:
            print(f"Failed to mark reminder sent: {e}")
