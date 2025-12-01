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
            self.supabase.table("elena_chat_logs").insert(data).execute()
        except Exception as e:
            print(f"Failed to save message: {e}")

    async def get_recent_context(self, user_id: str, limit: int = 5):
        """Fetch recent chat context."""
        if not self.supabase:
            return []

        try:
            response = self.supabase.table("elena_chat_logs") \
                .select("*") \
                .eq("user_id", str(user_id)) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            # Return in chronological order
            return sorted(response.data, key=lambda x: x['created_at'])
        except Exception as e:
            print(f"Failed to fetch context: {e}")
            return []
