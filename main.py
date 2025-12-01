import os
import logging
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Import Bot Applications
from bots.elena.services.telegram_bot import application as elena_app
from bots.alex.services.telegram_bot import application as alex_app
from bots.athena.services.telegram_bot import application as athena_app
from bots.zeus.services.telegram_bot import application as zeus_app
from bots.english_coach.bot import application as english_coach_app, restore_jobs

# Import Scheduler
from scheduler import start_master_scheduler

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Polling Management ---
async def start_polling_bot(app, name):
    """Initialize and start polling for a bot application."""
    if not app:
        logger.warning(f"{name} application is None. Skipping.")
        return

    logger.info(f"Starting {name} in Polling Mode...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info(f"{name} started successfully.")

async def stop_polling_bot(app, name):
    """Stop a bot application."""
    if not app: return
    logger.info(f"Stopping {name}...")
    await app.updater.stop()
    await app.stop()
    await app.shutdown()

# --- Lifecycle Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of bots."""
    logger.info("🚀 Starting OmniBot (Polling Mode)...")
    
    # 1. Start Scheduler
    asyncio.create_task(start_master_scheduler())
    
    # 2. Start English Coach Jobs (Special Case)
    if english_coach_app:
        await english_coach_app.initialize()
        await english_coach_app.start()
        await restore_jobs(english_coach_app)
        await english_coach_app.updater.start_polling(drop_pending_updates=True)
        logger.info("English Coach started with JobQueue.")

    # 3. Start Other Bots
    await start_polling_bot(elena_app, "Elena")
    await start_polling_bot(alex_app, "Alex")
    await start_polling_bot(athena_app, "Athena")
    await start_polling_bot(zeus_app, "Zeus")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down OmniBot...")
    await stop_polling_bot(english_coach_app, "English Coach")
    await stop_polling_bot(elena_app, "Elena")
    await stop_polling_bot(alex_app, "Alex")
    await stop_polling_bot(athena_app, "Athena")
    await stop_polling_bot(zeus_app, "Zeus")

# --- FastAPI App (For UptimeRobot) ---
app = FastAPI(lifespan=lifespan)

# Serve FluentAI Frontend (Optional, but good to keep)
if os.path.exists("fluentai---american-accent-coach/dist"):
    app.mount("/fluentai", StaticFiles(directory="fluentai---american-accent-coach/dist", html=True), name="fluentai")

@app.get("/")
async def health_check():
    """Health check endpoint for UptimeRobot."""
    return {"status": "alive", "mode": "polling"}

@app.get("/health")
async def health_check_alias():
    return {"status": "alive", "mode": "polling"}
