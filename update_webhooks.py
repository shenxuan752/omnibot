import os
import requests
from dotenv import load_dotenv

load_dotenv()

RENDER_URL = "https://omnibot-648d.onrender.com"

bots = [
    ("ELENA_TELEGRAM_BOT_TOKEN", "elena"),
    ("ALEX_TELEGRAM_BOT_TOKEN", "alex"),
    ("ATHENA_TELEGRAM_BOT_TOKEN", "athena"),
    ("ZEUS_TELEGRAM_BOT_TOKEN", "zeus"),
    ("ENGLISH_COACH_TELEGRAM_BOT_TOKEN", "english_coach"),
]

print(f"Updating webhooks to: {RENDER_URL}...\n")

for token_var, path in bots:
    token = os.getenv(token_var)
    if not token:
        print(f"❌ Missing token for {path} ({token_var})")
        continue
        
    webhook_url = f"{RENDER_URL}/webhook/{path}"
    api_url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200 and response.json().get("ok"):
            print(f"✅ {path.capitalize()}: Webhook updated successfully!")
        else:
            print(f"❌ {path.capitalize()}: Failed! {response.text}")
    except Exception as e:
        print(f"❌ {path.capitalize()}: Error {e}")

print("\nDone!")
