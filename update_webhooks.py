import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

# Render URL (update this to your actual Render URL)
RENDER_URL = "https://omnibot-dec2025.onrender.com"

# Bot configurations (ONLY ACTIVE BOTS)
BOTS = {
    "Elena": os.getenv("ELENA_TELEGRAM_BOT_TOKEN"),
    "Alex": os.getenv("ALEX_TELEGRAM_BOT_TOKEN"),
    "English Coach": os.getenv("ENGLISH_COACH_TELEGRAM_BOT_TOKEN"),
}

async def update_webhooks():
    for bot_name, token in BOTS.items():
        if not token:
            print(f"⚠️  {bot_name}: Token not found, skipping...")
            continue
        
        bot = Bot(token=token)
        webhook_path = bot_name.lower().replace(" ", "_")
        webhook_url = f"{RENDER_URL}/webhook/{webhook_path}"
        
        try:
            await bot.set_webhook(url=webhook_url)
            info = await bot.get_webhook_info()
            print(f"✅ {bot_name}: Webhook set to {info.url}")
        except Exception as e:
            print(f"❌ {bot_name}: Error - {e}")

if __name__ == "__main__":
    asyncio.run(update_webhooks())
