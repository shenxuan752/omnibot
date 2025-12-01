import os
import requests
from dotenv import load_dotenv

load_dotenv()

bots = [
    ("ELENA_TELEGRAM_BOT_TOKEN", "elena"),
    ("ALEX_TELEGRAM_BOT_TOKEN", "alex"),
    ("ATHENA_TELEGRAM_BOT_TOKEN", "athena"),
    ("ZEUS_TELEGRAM_BOT_TOKEN", "zeus"),
    ("ENGLISH_COACH_TELEGRAM_BOT_TOKEN", "english_coach"),
]

print("Deleting webhooks to enable Polling Mode...\n")

for token_var, name in bots:
    token = os.getenv(token_var)
    if not token:
        print(f"❌ Missing token for {name}")
        continue
        
    api_url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=True"
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200 and response.json().get("ok"):
            print(f"✅ {name.capitalize()}: Webhook deleted!")
        else:
            print(f"❌ {name.capitalize()}: Failed! {response.text}")
    except Exception as e:
        print(f"❌ {name.capitalize()}: Error {e}")

print("\nDone! Bots are ready for Polling.")
