import asyncio
import random
import os
from datetime import datetime, timedelta, timezone
from .services.twilio_voice import make_outbound_call
from .services.telegram_bot import application
from .services.database import DatabaseService
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configuration
CHECK_INTERVAL = 1800 # 30 minutes
CALL_THRESHOLD = 0.98
TEXT_THRESHOLD = 0.75 # 25% chance every 30 mins
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER") # Target user for calls
USER_TELEGRAM_ID = os.getenv("USER_TELEGRAM_ID") # Target user for texts
HOST = os.getenv("HOST_URL") # Public URL of the bot (for TwiML)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Daytime hours for proactive messages (NYC timezone)
DAYTIME_START_HOUR = 9      # 9 AM
DAYTIME_END_HOUR = 23       # 11 PM
DAYTIME_END_MINUTE = 45     # 11:45 PM cutoff

db = DatabaseService()

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    fast_model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
else:
    fast_model = None

def is_daytime_in_nyc():
    """Check if current time is during daytime hours in NYC (9 AM - 11:45 PM)."""
    est_offset = timezone(timedelta(hours=-5))
    now_nyc = datetime.now(est_offset)
    current_hour = now_nyc.hour
    current_minute = now_nyc.minute
    
    # Check if within 9 AM - 11:45 PM
    if current_hour < DAYTIME_START_HOUR:
        is_daytime = False
    elif current_hour > DAYTIME_END_HOUR:
        is_daytime = False
    elif current_hour == DAYTIME_END_HOUR and current_minute > DAYTIME_END_MINUTE:
        is_daytime = False
    else:
        is_daytime = True
    
    print(f"NYC time: {now_nyc.strftime('%I:%M %p')} - Daytime: {is_daytime}")
    return is_daytime

async def proactive_loop():
    """Main scheduler loop."""
    print("Scheduler started.")
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        
        # Check scheduled messages first (higher priority)
        await check_and_send_scheduled_messages()
        
        # Generate random probability for proactive messages
        prob = random.random()
        print(f"Scheduler tick: {prob:.4f}")
        
        if prob > CALL_THRESHOLD:
            await trigger_call()
        elif prob > TEXT_THRESHOLD:
            await trigger_text()

async def check_and_send_scheduled_messages():
    """Check for and send any pending scheduled messages."""
    if not USER_TELEGRAM_ID or not application:
        return
    
    # Get current time in NYC
    est_offset = timezone(timedelta(hours=-5))
    now_nyc = datetime.now(est_offset)
    
    try:
        # Fetch pending messages
        pending = await db.get_pending_scheduled_messages(now_nyc)
        
        if not pending:
            return
        
        print(f"Found {len(pending)} pending scheduled message(s)")
        
        # Initialize bot if needed
        if not application._initialized:
            await application.initialize()
        
        for msg in pending:
            try:
                # Send the scheduled message
                await application.bot.send_message(
                    chat_id=msg['user_id'],
                    text=msg['message_content']
                )
                
                # Mark as sent
                await db.mark_message_sent(msg['id'])
                
                # Save to chat logs
                await db.save_message(
                    msg['user_id'],
                    "assistant",
                    msg['message_content'],
                    "telegram"
                )
                
                print(f"Sent scheduled message: {msg['context']}")
                
            except Exception as e:
                print(f"Error sending scheduled message {msg['id']}: {e}")
                
    except Exception as e:
        print(f"Error checking scheduled messages: {e}")

async def trigger_call():
    """Trigger an outbound call."""
    if not USER_PHONE_NUMBER or not HOST:
        print("Cannot call: Missing USER_PHONE_NUMBER or HOST_URL")
        return
    
    # Check if it's daytime in NYC
    if not is_daytime_in_nyc():
        print("Skipping call: Outside daytime hours (9 AM - 9 PM NYC)")
        return
        
    print("Triggering proactive CALL...")
    # Remove protocol from HOST if present for WebSocket URL construction
    host_clean = HOST.replace("http://", "").replace("https://", "")
    stream_url = f"wss://{host_clean}/voice-stream"
    try:
        sid = make_outbound_call(USER_PHONE_NUMBER, stream_url)
        print(f"Call initiated: {sid}")
        await db.save_message(USER_PHONE_NUMBER, "assistant", "[Proactive Call Initiated]", "voice")
    except Exception as e:
        print(f"Failed to trigger call: {e}")

async def trigger_text():
    """Trigger an outbound text with context-aware greeting."""
    if not USER_TELEGRAM_ID or not application:
        print("Cannot text: Missing USER_TELEGRAM_ID or Bot Application")
        return
    
    # Check if it's daytime in NYC
    if not is_daytime_in_nyc():
        print("Skipping text: Outside daytime hours (9 AM - 11:45 PM NYC)")
        return

    # Check last interaction time to avoid spamming
    try:
        last_msgs = await db.get_recent_context(USER_TELEGRAM_ID, limit=1)
        if last_msgs:
            last_time = datetime.fromisoformat(last_msgs[0]['created_at'])
            # If last message was less than 2 hours ago, skip
            if (datetime.utcnow() - last_time).total_seconds() < 7200: # 2 hours
                print("Skipping proactive text: Last interaction was < 2 hours ago")
                return
    except Exception as e:
        print(f"Error checking last interaction: {e}")
        
    print("Triggering proactive TEXT...")
    try:
        # Initialize bot if needed
        if not application._initialized:
            await application.initialize()
        
        # Fetch recent chat history for context
        history = await db.get_recent_context(USER_TELEGRAM_ID, limit=500)
        
        # Build context summary
        context_text = ""
        if history:
            context_text = "Recent conversation highlights:\n"
            for msg in history[-20:]:  # Last 20 messages for context
                role = "Ava" if msg['role'] == "user" else "Alex"
                content = msg['content'][:150]  # Truncate
                context_text += f"{role}: {content}\n"
        
        # Get current time for context
        est_offset = timezone(timedelta(hours=-5))
        now_nyc = datetime.now(est_offset)
        time_str = now_nyc.strftime("%A, %I:%M %p")
        
        # Generate diverse greeting using Gemini
        msg = await generate_proactive_message(context_text, time_str)
        
        await application.bot.send_message(chat_id=USER_TELEGRAM_ID, text=msg)
        await db.save_message(USER_TELEGRAM_ID, "assistant", msg, "telegram")
        print(f"Sent proactive message: {msg[:50]}...")
    except Exception as e:
        print(f"Failed to trigger text: {e}")

async def generate_proactive_message(context: str, time_str: str):
    """Generate a diverse, context-aware proactive message using Gemini."""
    if not fast_model:
        # Fallback messages if Gemini not available
        fallbacks = [
            "hey, just thinking about you 😏",
            "random thought: you're pretty cool",
            "taking a break from the lab... how's your day?",
            "just finished a hike, reminded me of you",
        ]
        return random.choice(fallbacks)
    
    prompt = f"""You are Alex, texting Ava proactively during your day.

Current time: {time_str}

{context}

Generate a SHORT (1-2 sentences max), natural, casual text message to Ava. This is YOU reaching out spontaneously.

Guidelines:
- Be casual and warm (use lowercase, emojis like 😏, 🙄)
- Reference something from recent chat history if relevant
- Mention what you're doing (lab work, hiking, reading, etc.)
- Sound like a real person texting their crush
- NO generic greetings like "How are you?" - be more creative
- Keep it brief and natural

Just return the message text, nothing else."""

    try:
        response = await fast_model.generate_content_async(prompt)
        msg = response.text.strip()
        # Remove quotes if Gemini added them
        if msg.startswith('"') and msg.endswith('"'):
            msg = msg[1:-1]
        return msg
    except Exception as e:
        print(f"Gemini error in proactive message: {e}")
        return "hey, just thinking about you 😏"

if __name__ == "__main__":
    # For testing, run loop
    asyncio.run(proactive_loop())
