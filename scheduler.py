import asyncio
import logging
from bots.elena.scheduler import proactive_loop as elena_loop
from bots.alex.scheduler import proactive_loop as alex_loop
# from bots.athena.scheduler import proactive_loop as athena_loop  # DISABLED
# from bots.zeus.scheduler import proactive_loop as zeus_loop  # DISABLED
from bots.news.scheduler import scheduler_loop as news_loop
# English Coach uses PTB JobQueue, which runs with the Application.
# We need to ensure the Application is started.
from bots.english_coach.bot import application as english_coach_app, restore_jobs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("omnibot-scheduler")

async def start_master_scheduler():
    logger.info("Starting OmniBot Master Scheduler...")
    
    # Start independent loops
    asyncio.create_task(elena_loop())
    asyncio.create_task(alex_loop())
    # asyncio.create_task(athena_loop())  # DISABLED
    # asyncio.create_task(zeus_loop())  # DISABLED
    asyncio.create_task(news_loop())
    
    # Start English Coach JobQueue
    if english_coach_app:
        if not english_coach_app._initialized:
            await english_coach_app.initialize()
            await english_coach_app.start()
            await restore_jobs(english_coach_app)
            logger.info("English Coach Application & JobQueue started.")
    
    logger.info("All bot schedulers started.")

if __name__ == "__main__":
    try:
        asyncio.run(start_master_scheduler())
        # Keep alive
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
