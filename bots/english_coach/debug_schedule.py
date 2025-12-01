import asyncio
import os
from dotenv import load_dotenv
from services.database import get_all_users
from datetime import datetime
import pytz

load_dotenv()

async def check_system():
    print("--- Checking Database Users ---")
    try:
        users = await get_all_users()
        print(f"Found {len(users)} users: {users}")
    except Exception as e:
        print(f"❌ Error getting users: {e}")

    print("\n--- Checking Timezone ---")
    ny_tz = pytz.timezone('America/New_York')
    now_ny = datetime.now(ny_tz)
    print(f"Current NY Time: {now_ny}")
    print(f"Timezone Info: {ny_tz}")

if __name__ == "__main__":
    asyncio.run(check_system())
