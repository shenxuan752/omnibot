import os
import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from telegram import Update
from bot import application, restore_jobs

load_dotenv()

app = FastAPI(title="English Coach Bot", version="2.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize bot and restore schedules on startup."""
    if not application._initialized:
        await application.initialize()
        await application.start()
    
    # Set Webhook
    webhook_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL")
    if webhook_url:
        webhook_url = f"{webhook_url}/telegram-webhook"
        await application.bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set to: {webhook_url}")
    else:
        print("⚠️ No WEBHOOK_URL found. Polling mode or manual webhook required.")

    # Restore jobs for all users
    await restore_jobs(application)
    print("✅ Bot initialized and jobs restored.")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown."""
    await application.stop()
    await application.shutdown()

@app.api_route("/", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint for UptimeRobot."""
    return JSONResponse(content={"status": "ok", "message": "English Coach is running 🚀"})

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Webhook endpoint for Telegram updates."""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        print(f"Error processing update: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
