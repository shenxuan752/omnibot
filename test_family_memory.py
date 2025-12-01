import os
from supabase import create_client
from dotenv import load_dotenv
import json

# Load env from Athena (it has the keys)
load_dotenv("/Users/a90362/Documents/D/AI_Project/gemini/athena/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def test_memory():
    print("🔍 Connecting to Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n📊 Fetching last 5 messages from family_chat_logs...")
    try:
        response = supabase.table("family_chat_logs") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(5) \
            .execute()
            
        messages = response.data
        
        if not messages:
            print("❌ No messages found! Something is wrong.")
            return

        print(f"✅ Found {len(messages)} messages.\n")
        
        for msg in messages:
            role = msg.get('role')
            bot_name = msg.get('bot_name') or "N/A"
            content = msg.get('content')[:50] + "..."
            platform = msg.get('platform')
            chat_id = msg.get('chat_id')
            
            print(f"[{role.upper()}] Bot: {bot_name} | Platform: {platform} | ChatID: {chat_id}")
            print(f"   Content: {content}")
            print("-" * 50)
            
        # Verify we have both bots
        bots_found = set(m['bot_name'] for m in messages if m['role'] == 'assistant')
        print(f"\n🤖 Bots detected in logs: {bots_found}")
        
        if 'athena' in bots_found and 'zeus' in bots_found:
            print("✅ SUCCESS: Both Athena and Zeus are saving to memory!")
        elif len(bots_found) > 0:
            print("⚠️ PARTIAL SUCCESS: Only some bots are saving.")
        else:
            print("❌ FAILURE: No bot responses found.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_memory()
