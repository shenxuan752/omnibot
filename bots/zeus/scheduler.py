import asyncio
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .services.telegram_bot import application, model
from .services.database import DatabaseService
from dotenv import load_dotenv
import random
import google.generativeai as genai

load_dotenv()

CHECK_INTERVAL = 60
USER_TELEGRAM_ID = os.getenv("USER_TELEGRAM_ID")
db = DatabaseService()

MORNING_MESSAGES = [
    "孩子，早安。新的一天，记住：不要等待机会，去创造机会。💪",
    "早安。今天遇到的任何困难，都是磨练你意志的磨刀石。别怕，迎上去。⚡️",
    "孩子，醒醒。世界很复杂，但原则很简单：做正确的事，而不是容易的事。🛡️",
    "早安。你的价值不取决于别人的评价，而取决于你的行动。🏔️",
    "孩子，新的一天。天塌下来有爸爸顶着，你尽管去闯。🦅"
]

async def proactive_loop():
    print("Zeus Scheduler started.")
    last_sent_date = None
    last_evening_date = None
    
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        
        # Use New York Time explicitly
        ny_tz = ZoneInfo("America/New_York")
        now = datetime.now(ny_tz)
        current_date_str = now.strftime("%Y-%m-%d")
        
        # 1. Morning Message (8:00 AM NY Time)
        if now.hour == 8 and now.minute == 0:
            if last_sent_date != current_date_str:
                await trigger_morning_message()
                last_sent_date = current_date_str
        
        # 2. Evening Check-in / Sunday Review (10:30 PM NY Time)
        if now.hour == 22 and now.minute == 30:
            if last_evening_date != current_date_str:
                if now.weekday() == 6: # Sunday
                    await trigger_weekly_review()
                else:
                    await trigger_evening_checkin()
                last_evening_date = current_date_str
                
        # 3. Dynamic Reminders Check (Every minute)
        await check_and_send_reminders()

async def get_target_chat_id():
    """Prefer Group Chat ID, fallback to User ID."""
    group_id = await db.get_family_group_id()
    if group_id:
        return group_id
    return USER_TELEGRAM_ID

async def trigger_morning_message():
    if not application: return
    target_id = await get_target_chat_id()
    if not target_id: return
        
    try:
        if not application._initialized: await application.initialize()
        msg = random.choice(MORNING_MESSAGES)
        await application.bot.send_message(chat_id=target_id, text=msg)
        await db.save_message(USER_TELEGRAM_ID, "assistant", msg, "scheduler", bot_name="zeus", chat_id=target_id)
    except Exception as e:
        print(f"Failed to trigger morning message: {e}")

async def trigger_evening_checkin():
    if not application: return
    target_id = await get_target_chat_id()
    if not target_id: return
        
    try:
        if not application._initialized: await application.initialize()
        msg = "孩子，今天有什么挑战吗？说说看，我们一起分析。🛡️"
        await application.bot.send_message(chat_id=target_id, text=msg)
        await db.save_message(USER_TELEGRAM_ID, "assistant", msg, "scheduler", bot_name="zeus", chat_id=target_id)
    except Exception as e:
        print(f"Failed to trigger evening check-in: {e}")

async def trigger_weekly_review():
    if not application or not model: return
    target_id = await get_target_chat_id()
    if not target_id: return
    
    print("Triggering Sunday Weekly Review...")
    
    try:
        if not application._initialized: await application.initialize()
        
        # Fetch last 7 days of context
        history = await db.get_combined_context(USER_TELEGRAM_ID, limit=200) # Increased context
        
        prompt = """
        It is Sunday night. Review the conversation history from the past week.
        Generate a "Weekly Review" message as Zeus (Father).
        
        Structure:
        1. Acknowledge the key challenges or wins from the week.
        2. Offer a piece of high-level wisdom or principle for the coming week.
        3. End with encouragement.
        
        Keep it strong, fatherly, and concise (under 150 words).
        """
        
        gemini_history = []
        for msg in history:
            role = "user" if msg['role'] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg['content']]})
            
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(prompt)
        review_msg = response.text
        
        await application.bot.send_message(chat_id=target_id, text=review_msg)
        await db.save_message(USER_TELEGRAM_ID, "assistant", review_msg, "scheduler", bot_name="zeus", chat_id=target_id)
        
    except Exception as e:
        print(f"Failed to trigger weekly review: {e}")
        # Fallback
        await trigger_evening_checkin()

async def check_and_send_reminders():
    if not application: return
    
    reminders = await db.get_due_reminders()
    if not reminders: return
    
    for reminder in reminders:
        try:
            if not application._initialized: await application.initialize()
            
            # Generate contextual message based on reminder type
            event_desc = reminder['content']
            reminder_type = reminder.get('reminder_type', 'post_event')
            
            if reminder_type == 'pre_event':
                # Encouraging "good luck" message before event
                msg = f"孩子，'{event_desc}'快开始了。放轻松，你准备好了。爸爸相信你！💪"
            else:  # post_event
                # Check-in message after event
                msg = f"孩子，关于'{event_desc}'，情况怎么样了？"
            
            await application.bot.send_message(chat_id=reminder['chat_id'], text=msg)
            
            await db.mark_reminder_sent(reminder['id'])
            await db.save_message(
                reminder['user_id'], 
                "assistant", 
                msg, 
                "scheduler_reminder", 
                bot_name="zeus", 
                chat_id=reminder['chat_id']
            )
            print(f"Sent {reminder_type} reminder for: {event_desc}")
            
        except Exception as e:
            print(f"Failed to send reminder {reminder['id']}: {e}")
