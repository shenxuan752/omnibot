import logging
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import Bot Webhook Handlers
from bots.elena.services.telegram_bot import process_telegram_update as elena_handler
from bots.alex.services.telegram_bot import process_telegram_update as alex_handler
from bots.athena.services.telegram_bot import process_telegram_update as athena_handler
from bots.zeus.services.telegram_bot import process_telegram_update as zeus_handler
from bots.english_coach.bot import process_telegram_update as english_coach_handler

# Import Scheduler
from scheduler import start_master_scheduler

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks."""
    logger.info("Starting up OmniBot (Webhook Mode)...")
    asyncio.create_task(start_master_scheduler())
    yield
    logger.info("Shutting down OmniBot...")

app = FastAPI(lifespan=lifespan)

# Serve FluentAI Frontend
if os.path.exists("fluentai---american-accent-coach/dist"):
    app.mount("/fluentai", StaticFiles(directory="fluentai---american-accent-coach/dist", html=True), name="fluentai")

@app.get("/")
@app.head("/")
async def health_check():
    return {"status": "alive", "mode": "webhook"}

@app.get("/health")
@app.head("/health")
async def health_check_alias():
    return {"status": "alive", "mode": "webhook"}

# --- Webhook Endpoints ---

@app.post("/webhook/elena")
async def webhook_elena(request: Request):
    try:
        data = await request.json()
        await elena_handler(data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Elena Webhook Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/webhook/alex")
async def webhook_alex(request: Request):
    try:
        data = await request.json()
        await alex_handler(data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Alex Webhook Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/webhook/athena")
async def webhook_athena(request: Request):
    try:
        data = await request.json()
        await athena_handler(data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Athena Webhook Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/webhook/zeus")
async def webhook_zeus(request: Request):
    try:
        data = await request.json()
        await zeus_handler(data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Zeus Webhook Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/webhook/english_coach")
async def webhook_english_coach(request: Request):
    try:
        data = await request.json()
        await english_coach_handler(data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"English Coach Webhook Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/webhook/{bot_path}")
async def webhook_fallback(bot_path: str, request: Request):
    logger.warning(f"Received webhook for unknown bot: {bot_path}")
    return {"status": "ignored"}
