import logging
import asyncio
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import Bot Webhook Handlers
from bots.elena.services.telegram_bot import process_telegram_update as elena_handler
from bots.alex.services.telegram_bot import process_telegram_update as alex_handler
# from bots.athena.services.telegram_bot import process_telegram_update as athena_handler  # DISABLED
# from bots.zeus.services.telegram_bot import process_telegram_update as zeus_handler  # DISABLED
from bots.english_coach.bot import process_telegram_update as english_coach_handler

# Import Scheduler
from scheduler import start_master_scheduler

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Lifecycle Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks."""
    logger.info("🚀 Starting OmniBot (Webhook Mode)...")
    asyncio.create_task(start_master_scheduler())
    yield
    logger.info("🛑 Shutting down OmniBot...")

# --- FastAPI App ---
app = FastAPI(lifespan=lifespan)

# Serve FluentAI Frontend (Optional, but good to keep)
if os.path.exists("fluentai---american-accent-coach/dist"):
    app.mount("/fluentai", StaticFiles(directory="fluentai---american-accent-coach/dist", html=True), name="fluentai")

@app.get("/")
@app.head("/")
async def health_check():
    """Health check endpoint for UptimeRobot."""
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

@app.post("/webhook/english_coach")
async def webhook_english_coach(request: Request):
    try:
        data = await request.json()
        await english_coach_handler(data)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"English Coach Webhook Error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

