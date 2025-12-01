import os
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from scheduler import scheduler_loop, send_digest

load_dotenv()

app = FastAPI(title="Telegram News Bot", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Start the scheduler on startup."""
    asyncio.create_task(scheduler_loop())

@app.api_route("/", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={"status": "ok", "message": "News Bot is running"})

@app.post("/send-now")
async def trigger_digest():
    """Manually trigger a digest (for testing)."""
    await send_digest()
    return JSONResponse(content={"status": "sent"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
