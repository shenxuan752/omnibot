import asyncio
import os
from datetime import datetime, time, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Fallback for Python < 3.9
from dotenv import load_dotenv
from telegram import Bot
from .services.news_fetcher import fetch_all_news
from .services.formatter import format_digest

load_dotenv()

BOT_TOKEN = os.getenv("NEWS_TELEGRAM_BOT_TOKEN")
USER_ID = os.getenv("USER_TELEGRAM_ID")
DIGEST_TIME = os.getenv("DIGEST_TIME", "13:00")  # Default 1:00 PM

async def send_digest():
    """Fetch news and send digest to user."""
    print(f"[{datetime.now()}] Sending daily digest...")
    
    try:
        # Fetch news
        news = fetch_all_news()
        
        # Format message
        message = format_digest(news)
        
        # Send via Telegram
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=USER_ID,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        
        print(f"[{datetime.now()}] Digest sent successfully!")
        
    except Exception as e:
        print(f"[{datetime.now()}] Error sending digest: {e}")

async def scheduler_loop():
    """Run daily at specified time in NY timezone."""
    try:
        tz = ZoneInfo("America/New_York")
    except Exception as e:
        print(f"Error loading timezone: {e}")
        # Fallback to UTC if timezone fails, but log it
        from datetime import timezone
        tz = timezone.utc
        
    print(f"Scheduler started. Digest will be sent daily at {DIGEST_TIME} {tz}")
    
    target_hour, target_minute = map(int, DIGEST_TIME.split(":"))
    
    while True:
        # Get current time in NY
        now = datetime.now(tz)
        
        # Create target time for today in NY
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # If target time has passed today, schedule for tomorrow
        if now >= target_time:
            target_time = target_time + timedelta(days=1)
        
        # Calculate seconds until next digest
        # Both datetimes are timezone-aware, so subtraction works correctly
        wait_seconds = (target_time - now).total_seconds()
        
        print(f"[{now}] Next digest at {target_time} (in {wait_seconds/3600:.1f} hours)")
        
        await asyncio.sleep(wait_seconds)
        await send_digest()

if __name__ == "__main__":
    asyncio.run(scheduler_loop())
