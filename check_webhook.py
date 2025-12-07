import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

async def check_webhook():
    token = os.getenv("ALEX_TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: ALEX_TELEGRAM_BOT_TOKEN not found in .env")
        return

    bot = Bot(token=token)
    info = await bot.get_webhook_info()
    print(f"--- Webhook Info for Alex ---")
    print(f"URL: {info.url}")
    print(f"Has Custom Certificate: {info.has_custom_certificate}")
    print(f"Pending Update Count: {info.pending_update_count}")
    print(f"Last Error Date: {info.last_error_date}")
    print(f"Last Error Message: {info.last_error_message}")
    print("-----------------------------")

if __name__ == "__main__":
    asyncio.run(check_webhook())
