import os
import asyncio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from services.telegram_bot import process_telegram_update
from scheduler import proactive_loop

load_dotenv()

app = FastAPI(title="Zeus (宙斯)", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Start background tasks."""
    asyncio.create_task(proactive_loop())

@app.api_route("/", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={"status": "ok", "message": "Zeus is standing guard 🛡️"})

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Webhook endpoint for Telegram updates."""
    data = await request.json()
    await process_telegram_update(data)
    return JSONResponse(content={"status": "ok"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
