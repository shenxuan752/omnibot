from services.audio_utils import pcm16_to_mulaw
import os
import json
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv
from services.gemini_live import GeminiLiveClient
from services.twilio_voice import generate_twiml_for_stream
from services.telegram_bot import process_telegram_update
from services.database import DatabaseService
from scheduler import proactive_loop

# Load environment variables
load_dotenv()

app = FastAPI(title="Project ALEX", version="1.0.0")
db = DatabaseService()

@app.on_event("startup")
async def startup_event():
    """Start background tasks."""
    asyncio.create_task(proactive_loop())

@app.api_route("/", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={"status": "ok", "message": "Alex is listening..."})

@app.post("/voice")
async def voice_entry(request: Request):
    """Twilio Voice webhook entry point."""
    # Get form data (Twilio sends data as form-urlencoded)
    form_data = await request.form()
    user_number = form_data.get("From", "Unknown")
    
    host = request.headers.get("host")
    # Pass user number in query param
    stream_url = f"wss://{host}/voice-stream?user_number={user_number}"
    twiml = generate_twiml_for_stream(stream_url)
    return PlainTextResponse(content=twiml, media_type="text/xml")

@app.websocket("/voice-stream")
async def voice_stream(websocket: WebSocket):
    """WebSocket endpoint for Twilio Media Streams."""
    await websocket.accept()
    print("Twilio connected")
    
    # Extract user number from query params
    user_number = websocket.query_params.get("user_number")
    
    # Transcript buffer for saving conversation
    alex_transcript_buffer = []
    
    # Fetch Context
    history_text = ""
    if user_number:
        # Try to find user by phone number (assuming user_id in DB matches phone for voice users)
        # Note: In Telegram, user_id is Telegram ID. In Voice, it's Phone Number.
        # Ideally we link them, but for MVP we might just check both or assume separate sessions unless linked.
        # User asked for cross-channel. We need a way to link Phone <-> Telegram ID.
        # For now, let's just fetch history for this phone number AND the Telegram ID if known.
        # But wait, we don't know the Telegram ID from the phone call easily without a lookup table.
        # Let's assume the user put their phone number in .env as USER_PHONE_NUMBER and Telegram ID as USER_TELEGRAM_ID.
        # We can try to fetch history for BOTH if they match the env vars.
        
        env_phone = os.getenv("USER_PHONE_NUMBER")
        env_tg_id = os.getenv("USER_TELEGRAM_ID")
        
        ids_to_fetch = []
        if user_number == env_phone:
            ids_to_fetch.append(env_phone)
            if env_tg_id:
                ids_to_fetch.append(env_tg_id)
        else:
            ids_to_fetch.append(user_number)
            
        # Fetch history for all IDs and merge
        full_history = []
        print(f"Fetching history for IDs: {ids_to_fetch}")
        for uid in ids_to_fetch:
            msgs = await db.get_recent_context(uid, limit=100)
            print(f"Found {len(msgs)} messages for {uid}")
            full_history.extend(msgs)
            
        # Sort by time
        full_history.sort(key=lambda x: x['created_at'])
        # Keep last 100
        full_history = full_history[-100:]
        
        # Format for System Prompt
        if full_history:
            history_text = "\n**Recent Chat History:**\n"
            for msg in full_history:
                role = "User" if msg['role'] == "user" else "Alex"
                content = msg['content']
                # Truncate if too long
                if len(content) > 100:
                    content = content[:100] + "..."
                history_text += f"{role}: {content}\n"

    gemini_client = GeminiLiveClient()
    
    # Inject history and time into system prompt
    from datetime import datetime, timedelta, timezone
    est_offset = timezone(timedelta(hours=-5))
    time_str = datetime.now(est_offset).strftime("%A, %B %d, %Y at %I:%M %p EST")
    
    current_prompt = gemini_client.session_config["systemInstruction"]["parts"][0]["text"]
    
    # Add Time
    new_prompt = f"Current Date/Time: {time_str}\n" + current_prompt
    
    # Add History
    if history_text:
        new_prompt += history_text
        
    gemini_client.update_system_instruction(new_prompt)

    stream_sid = None
    
    try:
        # Connect to Gemini
        await gemini_client.connect()
        
        async def receive_from_twilio():
            nonlocal stream_sid
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message['event'] == 'media':
                        # Twilio sends audio in 'media' -> 'payload' (base64 mulaw)
                        audio_chunk = message['media']['payload']
                        # Send to Gemini
                        await gemini_client.send_audio(audio_chunk)
                    elif message['event'] == 'start':
                        stream_sid = message['start']['streamSid']
                        print(f"Stream started: {stream_sid}")
                    elif message['event'] == 'stop':
                        print("Stream stopped")
                        break
            except Exception as e:
                print(f"Twilio receive error: {e}")

        async def receive_from_gemini():
            try:
                while True:
                    response = await gemini_client.receive()
                    if response is None:
                        break
                    
                    if "serverContent" in response and "modelTurn" in response["serverContent"]:
                        parts = response["serverContent"]["modelTurn"]["parts"]
                        for part in parts:
                            # Capture text transcript if available
                            if "text" in part:
                                alex_transcript_buffer.append(part["text"])
                            
                            # Handle audio response
                            if "inlineData" in part:
                                payload_pcm = part["inlineData"]["data"]
                                # Convert PCM 24kHz to mulaw 8kHz for Twilio
                                payload_mulaw = pcm16_to_mulaw(payload_pcm, from_rate=24000, to_rate=8000)
                                if stream_sid:
                                    msg = {
                                        "event": "media",
                                        "streamSid": stream_sid,
                                        "media": {"payload": payload_mulaw}
                                    }
                                    await websocket.send_text(json.dumps(msg))
            except Exception as e:
                print(f"Gemini receive error: {e}")

        # Run both tasks concurrently
        await asyncio.gather(receive_from_twilio(), receive_from_gemini())

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Save voice conversation to database
        if user_number and alex_transcript_buffer:
            try:
                alex_text = " ".join(alex_transcript_buffer)
                await db.save_message(user_number, "assistant", alex_text, "voice")
                await db.save_message(user_number, "user", "Voice call", "voice")
                print(f"Saved voice conversation for {user_number}")
            except Exception as e:
                print(f"Error saving voice transcript: {e}")
        
        await gemini_client.close()
        try:
            await websocket.close()
        except:
            pass

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook endpoint for Telegram updates."""
    data = await request.json()
    # Process in background to return 200 OK immediately and prevent Telegram retries
    background_tasks.add_task(process_telegram_update, data)
    return JSONResponse(content={"status": "ok"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
