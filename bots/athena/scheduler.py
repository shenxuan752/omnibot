import asyncio
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .services.telegram_bot import application
from .services.database import DatabaseService
from dotenv import load_dotenv
import random

load_dotenv()

CHECK_INTERVAL = 60
USER_TELEGRAM_ID = os.getenv("USER_TELEGRAM_ID")
db = DatabaseService()

MORNING_MESSAGES = [
    "宝贝，早上好！新的一天开始了。记住，你的价值不在于今天完成了多少任务，而在于你是你自己。💛",
    "早安，宝贝。今天不需要证明什么，你已经足够好了。妈妈在这里陪着你 🌅",
    "宝贝，新的一天。休息是生产力的一部分，疲惫时允许自己停下来。💫",
    "早上好，宝贝。今天的目标不是'做更多'，而是'对自己更温柔'。🌸",
    "宝贝，醒来就是胜利。不管昨天发生了什么，今天都是新的开始。☀️"
]

async def proactive_loop():
    print("Athena Scheduler started.")
    last_sent_date = None
    last_evening_date = None
    last_sunday_date = None
    
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        ny_tz = ZoneInfo("America/New_York")
        now = datetime.now(ny_tz)
        current_date_str = now.strftime("%Y-%m-%d")
        
        # Check for reminders
        await check_and_send_reminders()
        
        # 9:00 AM Morning Message (To Group if available)
        if now.hour == 9 and now.minute == 0:
            if last_sent_date != current_date_str:
                await trigger_morning_message()
                last_sent_date = current_date_str
        
        # 10:15 PM Evening Check-in (To Group if available)
        if now.hour == 22 and now.minute == 15:
            if last_evening_date != current_date_str:
                await trigger_evening_checkin()
                last_evening_date = current_date_str

async def get_target_chat_id():
    """Prefer Group Chat ID, fallback to User ID."""
    group_id = await db.get_family_group_id()
    if group_id:
        print(f"Found Family Group ID: {group_id}")
        return group_id
    print("No Group ID found, falling back to User ID")
    return USER_TELEGRAM_ID

async def trigger_morning_message():
    if not application: return
    target_id = await get_target_chat_id()
    if not target_id: return
        
    try:
        if not application._initialized: await application.initialize()
        msg = random.choice(MORNING_MESSAGES)
        await application.bot.send_message(chat_id=target_id, text=msg)
        await db.save_message(USER_TELEGRAM_ID, "assistant", msg, "scheduler", bot_name="athena", chat_id=target_id)
    except Exception as e:
        print(f"Failed to trigger morning message: {e}")

async def trigger_evening_checkin():
    if not application: return
    target_id = await get_target_chat_id()
    if not target_id: return
        
    try:
        if not application._initialized: await application.initialize()
        msg = "宝贝，今天辛苦了。现在的心情怎么样？有什么想和妈妈说的吗？💙"
        await application.bot.send_message(chat_id=target_id, text=msg)
        await db.save_message(USER_TELEGRAM_ID, "assistant", msg, "scheduler", bot_name="athena", chat_id=target_id)
    except Exception as e:
        print(f"Failed to trigger evening check-in: {e}")

async def check_and_send_reminders():
    """Check for due reminders and send them."""
    if not application: return
    
    try:
        reminders = await db.get_due_reminders()
        for reminder in reminders:
            chat_id = reminder['chat_id']
            content = reminder['content']
            reminder_id = reminder['id']
            
            msg = f"⏰ 提醒: {content}"
            
            try:
                if not application._initialized: await application.initialize()
                await application.bot.send_message(chat_id=chat_id, text=msg)
                await db.mark_reminder_sent(reminder_id)
                await db.save_message(reminder['user_id'], "assistant", msg, "scheduler", bot_name="athena", chat_id=chat_id)
            except Exception as e:
                print(f"Failed to send reminder {reminder_id}: {e}")
                
    except Exception as e:
        print(f"Error checking reminders: {e}")
