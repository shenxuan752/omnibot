import os
import logging
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("omnibot")

app = FastAPI(title="OmniBot Super Server")

from scheduler import start_master_scheduler

# Import Bot Webhook Handlers
from bots.elena.services.telegram_bot import process_telegram_update as elena_handler
from bots.alex.services.telegram_bot import process_telegram_update as alex_handler
from bots.athena.services.telegram_bot import process_telegram_update as athena_handler
from bots.zeus.services.telegram_bot import process_telegram_update as zeus_handler
from bots.english_coach.bot import process_telegram_update as english_coach_handler

@app.on_event("startup")
async def startup_event():
    """Start background tasks."""
    logger.info("Starting up OmniBot...")
    import asyncio
    asyncio.create_task(start_master_scheduler())

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "OmniBot is running"}

from fastapi.staticfiles import StaticFiles

# Serve FluentAI static files
fluentai_dist = "fluentai---american-accent-coach/dist"
if os.path.exists(fluentai_dist):
    app.mount("/fluentai", StaticFiles(directory=fluentai_dist, html=True), name="fluentai")
else:
    logger.warning(f"FluentAI dist directory not found at {fluentai_dist}. Skipping mount.")

# --- Webhook Routes ---

@app.post("/webhook/elena")
async def elena_webhook(request: Request):
    data = await request.json()
    await elena_handler(data)
    return {"status": "ok"}

@app.post("/webhook/alex")
async def alex_webhook(request: Request):
    data = await request.json()
    await alex_handler(data)
    return {"status": "ok"}

@app.post("/webhook/athena")
async def athena_webhook(request: Request):
    data = await request.json()
    await athena_handler(data)
    return {"status": "ok"}

@app.post("/webhook/zeus")
async def zeus_webhook(request: Request):
    data = await request.json()
    await zeus_handler(data)
    return {"status": "ok"}

@app.post("/webhook/english_coach")
async def english_coach_webhook(request: Request):
    data = await request.json()
    await english_coach_handler(data)
    return {"status": "ok"}

# News Bot (Broadcast only, but we can add a trigger if needed)
# @app.post("/webhook/news")
# async def news_webhook(request: Request):
#     return {"status": "ignored", "reason": "broadcast_only"}

@app.post("/webhook/{bot_name}")
async def generic_webhook(bot_name: str, request: Request):
    """
    Fallback for unknown bots.
    """
    logger.warning(f"Received webhook for unknown bot: {bot_name}")
    return {"status": "unknown_bot", "bot": bot_name}
