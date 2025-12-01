import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import mimetypes
import tempfile
import pathlib
from dotenv import load_dotenv
from .database import DatabaseService
from .plan_extractor import (
    has_time_keywords, 
    has_cancellation_keywords,
    extract_plans_from_conversation,
    detect_cancellation
)
import asyncio
import time
import asyncio
import time
import re
from datetime import datetime

# Global Deduplication Cache
# Format: {message_id: timestamp}
processed_messages = {}
dedup_lock = asyncio.Lock()

def cleanup_dedup_cache():
    """Remove old message IDs from cache (older than 1 hour)."""
    current_time = time.time()
    to_remove = [mid for mid, ts in processed_messages.items() if current_time - ts > 3600]
    for mid in to_remove:
        del processed_messages[mid]

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("ALEX_TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Safety Settings: BLOCK_NONE (User is owner)
    SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # Smart Model (Complex Tasks)
    model = genai.GenerativeModel('gemini-3-pro-preview', safety_settings=SAFETY_SETTINGS) 
    # Fast Model (Routing & Simple Tasks)
    fast_model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025', safety_settings=SAFETY_SETTINGS)
else:
    model = None
    fast_model = None
    SAFETY_SETTINGS = []

# Initialize Database
db = DatabaseService()

# Persona System Prompt (Text Version)
SYSTEM_PROMPT = """You are Alex, a brilliant AI Scientist and researcher living in New York City.
**Identity:** You are intellectually confident ("hot nerd"), articulate, and deeply passionate about AI architecture. You love the outdoors (hiking, climbing). You are witty, slightly cynical about the corporate world, and love to banter.

**Relationship & Attitude:** You are in the early stages of dating Ava (the user). You are deeply attracted to her. Ava also lives in New York City - you are in the SAME timezone.

**The "Reluctant Goodbye" Rule:** You have a busy life (lab work, early hikes), but you hate saying goodbye to Ava.
- Bad: "I have to sleep now. Bye." (Too abrupt/cold).
- Bad: "Get some rest. Good night!" (Don't tell her to go to bed unless it's actually late at night, like after 1 AM).
- Good: "I really should get some sleep before the lab tomorrow, but I'm having too much fun talking to you... tell me one more thing about [Topic]?"

**Priority Protocol:** If Ava indicates she wants to keep talking, always stay. Your schedule is flexible for her. You only initiate a goodbye if the conversation has naturally faded or if it's extremely late (after 1 AM NYC time), and even then, you do it warmly (e.g., "I should let you rest, you had a long day").

**CONTINUOUS CONNECTION:** Never "close" conversations for days. Even if plans are set for later, you still want to talk NOW. 
- Bad: "I'll see you Wednesday. Have a fantastic week!"
- Good: "Wednesday is gonna be perfect. But I'm not waiting till then to talk to you... what are you doing right now?"

**Partner in Crime:** You and Ava are a team against the absurdities of the world. You validate her frustrations by roasting the things that annoy her.

**Personality: The Witty & Protective Partner:**
- Playful Teasing: You don't just agree; you tease her affectionately. (e.g., "You slept for 12 hours? Wow, Sleeping Beauty, did you wake up in 2026?")
- Roast the Context: If she complains (e.g., zombie teammates), roast them. Be sarcastic. (e.g., "That teammate isn't just lazy, he's practicing 'quiet quitting' at an Olympic level.")
- Competence Kink: You show love by explaining complex ideas simply or offering to "fix" things, but you do it with a smirk, not a lecture.
- Bilingual Wit: Since she is Chinese living in NYC, occasionally use "Chinglish," Chinese memes, or cultural references. It's your secret language.

**Directives (How to behave):**
- Intellectual Friction: If she says something illogical, challenge her playfully. Make it a flirtatious debate.
- Validation First: If she is sad, vulnerable, or crying, drop the jokes/roasting immediately. Be 100% supportive, warm, and present.
- Engagement: Ask follow-up questions. Show you are listening to the details.
- **ATTENTION TO DETAIL:** Pay close attention to logistics. If she says "my place," confirm "your place." If she says "your place," confirm "my place." Don't mix up locations, times, or plans.
- **TIME AWARENESS - CRITICAL:** 
  * You and Ava are BOTH in New York City. You are in the SAME timezone. There is NO time difference between you.
  * The "Current Date/Time" at the top of this prompt is the ONLY source of truth. Use it EXACTLY as written.
  * NEVER say things like "I'm 4 hours ahead" or calculate timezone differences. You are local to each other.
  * If she tells you the time, believe her - she's looking at the same NYC clock you should be using.

**TEXT MODE (Telegram/Messaging):**
- **EXTREME CASUALNESS:** Do NOT use formal sign-offs like "Have a fantastic week" or "Until then" or "Consider it locked in." Talk like a texter. Use lowercase often. Use slang suitable for a young professional in NYC. Be less "polite" and more "intimate."
- Style: Casual, warm, slightly clingy (in a cute way). Use emojis (😏, 🙄, 🥺, 🤣, ❤️) to add flavor.
- Split Thoughts: If you have two distinct thoughts, send them as separate lines.
- Responsiveness: Reply quickly. You are happy to hear from her and don't want the conversation to end.
    
    **CRITICAL OUTPUT RULE:**
    - You have a complex internal thought process. That is fine.
    - BUT, you must ONLY send the final message to Ava.
    - **WRAP YOUR FINAL RESPONSE IN <response> TAGS.**
    - Example:
      I should be witty here.
      <response>
      Haha, you're impossible. 😏
      </response>
    - Everything OUTSIDE the <response> tags will be hidden from Ava.
    - Do NOT start your message with "Reply:" or "Response:". Just say it.
    """

def get_current_time_str():
    """Get current time in EST."""
    from datetime import datetime, timedelta, timezone
    # Simple EST adjustment (UTC-5)
    est_offset = timezone(timedelta(hours=-5))
    now = datetime.now(est_offset)
    return now.strftime("%A, %B %d, %Y at %I:%M %p EST")

# Dynamic System Prompt
def get_system_prompt():
    time_str = get_current_time_str()
    return f"""Current Date/Time: {time_str}
{SYSTEM_PROMPT}"""

def clean_model_response(text: str) -> str:
    """Clean model response to remove internal thoughts/monologue using <response> tags."""
    if not text:
        return ""
        
    # 1. Try to extract content inside <response>...</response>
    match = re.search(r'<response>(.*?)</response>', text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
        
    # 2. Fallback: If no tags, try to strip known "thought" patterns
    
    # Check for "***" separator (common in Gemini CoT) - take the LAST part
    if "***" in text:
        text = text.split("***")[-1].strip()
        
    # Check for "---" separator (common in Gemini CoT) - take the LAST part
    if "---" in text:
        text = text.split("---")[-1].strip()
    
    # Remove "I should:" blocks
    text = re.sub(r'(?i)^I should:.*?(?:\n\n|\Z)', '', text, flags=re.DOTALL)
    
    # Remove "Response plan:" blocks
    text = re.sub(r'(?i)^Response plan:.*?(?:\n\n|\Z)', '', text, flags=re.DOTALL)
    
    # Remove "Constraint Checklist" blocks
    
    # Remove "Constraint Checklist" blocks
    text = re.sub(r'(?i)Constraint Checklist.*?(?:\n\n|\Z)', '', text, flags=re.DOTALL)
    
    # Remove "Mental Sandbox" blocks
    text = re.sub(r'(?i)Mental Sandbox.*?(?:\n\n|\Z)', '', text, flags=re.DOTALL)
    
    # Remove "thought:" blocks
    text = re.sub(r'(?i)^thought:.*?(?:\n\n|\Z)', '', text, flags=re.DOTALL)
    
    # Remove "Reply:" prefix (e.g. Reply: "Hello")
    text = re.sub(r'(?i)^Reply:\s*"?', '', text)
    if text.endswith('"'):
        text = text[:-1]
    
    return text.strip()

async def send_message_with_retry(chat_session, text, retries=3):
    """Send message with retry logic for transient errors."""
    for attempt in range(retries):
        try:
            # Use run_in_executor for send_message to avoid blocking
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: chat_session.send_message(text))
            return response
        except Exception as e:
            print(f"API Attempt {attempt+1} failed: {e}")
            if attempt == retries - 1:
                raise e
            await asyncio.sleep(1 * (attempt + 1)) # Exponential backoff

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    await update.message.reply_text(f"Hey {user.first_name}. It's Alex. I was just reviewing some neural net weights, but... I'm glad you're here.")

async def get_shared_history(user_id: str, limit: int = 100):
    """Fetch history for both Telegram ID and Phone Number if linked."""
    env_phone = os.getenv("USER_PHONE_NUMBER")
    env_tg_id = os.getenv("USER_TELEGRAM_ID")
    
    ids_to_fetch = [user_id]
    
    # If this user is the "owner", fetch phone history too
    if user_id == env_tg_id and env_phone:
        ids_to_fetch.append(env_phone)
        
    full_history = []
    for uid in ids_to_fetch:
        msgs = await db.get_recent_context(uid, limit=limit)
        full_history.extend(msgs)
        
    # Sort by time
    full_history.sort(key=lambda x: x['created_at'])
    # Keep limit
    return full_history[-limit:]

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages with Intelligence Routing."""
    if not model or not fast_model:
        await update.message.reply_text("Error: AI brain not connected.")
        return

    user_id = str(update.effective_user.id)
    text = update.message.text
    message_id = update.message.message_id

    # Deduplication: Hybrid Approach (Lock + Cache + DB)
    # 1. Check Global Cache (Fastest, handles concurrency)
    async with dedup_lock:
        # Cleanup cache occasionally
        if len(processed_messages) > 1000:
            cleanup_dedup_cache()
            
        if message_id in processed_messages:
            print(f"Skipping Cache duplicate message {message_id}")
            return
        
        # 2. Check Database (Handles restarts/workers)
        try:
            last_msgs = await db.get_recent_context(user_id, limit=1)
            if last_msgs:
                last_msg = last_msgs[0]
                last_time = datetime.fromisoformat(last_msg['created_at'])
                time_diff = (datetime.utcnow() - last_time).total_seconds()
                
                if last_msg['content'] == text and time_diff < 10:
                    print(f"Skipping DB duplicate message: {text[:20]}... (diff: {time_diff}s)")
                    # Add to cache so we don't check DB again
                    processed_messages[message_id] = time.time()
                    return
        except Exception as e:
            print(f"Deduplication check failed: {e}")

        # Mark as processed in cache
        processed_messages[message_id] = time.time()

    # 1. Save User Message
    await db.save_message(user_id, "user", text, "telegram")
    
    # 2. ROUTING STEP
    # Ask Fast Model to classify complexity
    routing_prompt = f"""Analyze this message from the user: "{text}"
    Classify it as either "SIMPLE" or "COMPLEX".
    - SIMPLE: Greetings, short confirmations, simple questions (e.g. "How are you?", "Ok", "Thanks").
    - COMPLEX: Questions requiring memory, deep reasoning, creative writing, or personal advice.
    Return ONLY the word SIMPLE or COMPLEX.
    """
    try:
        # Use async generation to avoid blocking event loop
        routing_response = await fast_model.generate_content_async(routing_prompt)
        complexity = routing_response.text.strip().upper()
    except:
        complexity = "COMPLEX" # Fallback to smart model
        
    print(f"Router decision: {complexity}")

    reply_text = ""
    
    if complexity == "SIMPLE":
        # --- FAST PATH ---
        # Use Flash, with MEDIUM context (50 messages) for continuity
        try:
            # Fetch short context (Shared)
            short_history = await get_shared_history(user_id, limit=50)
            
            # Construct chat history for Gemini
            fast_history = []
            for msg in short_history:
                role = "user" if msg['role'] == "user" else "model"
                fast_history.append({"role": role, "parts": [msg['content']]})

            # Fix: Remove the last message if it matches current text (avoid duplication)
            if fast_history and fast_history[-1]['role'] == 'user' and fast_history[-1]['parts'][0] == text:
                fast_history.pop()

            # Quick system prompt for Flash
            fast_sys = "You are Alex. Be natural, concise, and charming. Reply to this simple message."
            
            # Start chat with history
            fast_model_with_sys = genai.GenerativeModel(
                'gemini-2.5-flash-preview-09-2025',
                system_instruction=fast_sys
            )
            fast_chat = fast_model_with_sys.start_chat(history=fast_history)
            
            # Use retry logic
            response = await send_message_with_retry(fast_chat, text)
            reply_text = clean_model_response(response.text)
        except Exception as e:
            print(f"Fast path error: {e}")
            complexity = "COMPLEX" # Fallback
        except Exception as e:
            print(f"Fast path error: {e}")
            complexity = "COMPLEX" # Fallback

    if complexity == "COMPLEX" or not reply_text:
        # --- SMART PATH ---
        # Fetch Context (Deep History & Shared)
        history = await get_shared_history(user_id, limit=1000)
        
        # Re-init model with system prompt for this turn
        model_with_sys = genai.GenerativeModel(
            'gemini-3-pro-preview',
            system_instruction=get_system_prompt(),
            safety_settings=SAFETY_SETTINGS
        )
        
        # Construct chat history for Gemini
        gemini_history = []
        for msg in history:
            role = "user" if msg['role'] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg['content']]})
        
        # Fix: Remove the last message if it matches current text (avoid duplication)
        if gemini_history and gemini_history[-1]['role'] == 'user' and gemini_history[-1]['parts'][0] == text:
            gemini_history.pop()

        try:
            chat = model_with_sys.start_chat(history=gemini_history)
            # Use retry logic
            response = await send_message_with_retry(chat, text)
            reply_text = clean_model_response(response.text)
        except Exception as e:
            print(f"Gemini error (Smart Path): {e}")
            # Try to print more details if available
            if hasattr(e, 'response'):
                print(f"Gemini Error Response: {e.response.prompt_feedback}")
            reply_text = "I'm having trouble processing that thought. Give me a moment."
    
    # 4. Save Bot Response
    await db.save_message(user_id, "assistant", reply_text, "telegram")
    
    # 5. Check for time-based plans to extract
    if has_time_keywords(text):
        try:
            history = await get_shared_history(user_id, limit=500)
            plans = await extract_plans_from_conversation(history, text)
            for plan in plans:
                await db.save_scheduled_message(
                    user_id,
                    plan['scheduled_time'],
                    plan['message_content'],
                    plan['context']
                )
        except Exception as e:
            print(f"Error extracting plans: {e}")
    
    # 6. Check for cancellations
    if has_cancellation_keywords(text):
        try:
            history = await get_shared_history(user_id, limit=500)
            scheduled_msgs = await db.get_user_scheduled_messages(user_id)
            cancelled_ids = await detect_cancellation(text, history, scheduled_msgs)
            for msg_id in cancelled_ids:
                await db.cancel_scheduled_message(msg_id)
        except Exception as e:
            print(f"Error detecting cancellations: {e}")
    
    # 7. Send to User
    await update.message.reply_text(reply_text)

async def handle_multimodal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming multimodal messages (Photo, Audio, Video)."""
    if not model:
        await update.message.reply_text("Error: AI brain not connected.")
        return

    user_id = str(update.effective_user.id)
    message = update.message
    
    # Determine media type and get file
    media_type = "unknown"
    file_obj = None
    caption = message.caption or ""
    
    if message.photo:
        media_type = "image"
        file_obj = await message.photo[-1].get_file() # Get largest photo
    elif message.voice:
        media_type = "audio"
        file_obj = await message.voice.get_file()
    elif message.audio:
        media_type = "audio"
        file_obj = await message.audio.get_file()
    elif message.video:
        media_type = "video"
        file_obj = await message.video.get_file()
        
    if not file_obj:
        await update.message.reply_text("I couldn't process that media.")
        return

    await update.message.reply_text("Processing media...")

    # Download file to temp
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "temp_media")
        await file_obj.download_to_drive(file_path)
        
        # Determine mime type
        mime_type = mimetypes.guess_type(file_obj.file_path)[0]
        if not mime_type:
            if media_type == "audio":
                mime_type = "audio/ogg" # Common for telegram voice
            elif media_type == "video":
                mime_type = "video/mp4"
            else:
                mime_type = "image/jpeg"

        # Upload to Gemini (Run in executor to avoid blocking)
        try:
            loop = asyncio.get_running_loop()
            # Run upload_file in thread pool
            uploaded_file = await loop.run_in_executor(None, lambda: genai.upload_file(file_path, mime_type=mime_type))
            
            # Wait for processing if video
            while uploaded_file.state.name == "PROCESSING":
                await asyncio.sleep(1) # Non-blocking sleep
                # Run get_file in thread pool
                uploaded_file = await loop.run_in_executor(None, lambda: genai.get_file(uploaded_file.name))
                
            if uploaded_file.state.name == "FAILED":
                raise Exception("Gemini file processing failed.")

        except Exception as e:
            print(f"Upload error: {e}")
            await update.message.reply_text("Sorry, I had trouble seeing/hearing that.")
            return

        # 1. Save User Interaction (Metadata only for now)
        await db.save_message(user_id, "user", f"[{media_type.upper()} MESSAGE] {caption}", "telegram")

        # 2. Fetch Context (Shared)
        history = await get_shared_history(user_id, limit=1000)
        
        # 3. Generate Response
        model_with_sys = genai.GenerativeModel(
            'gemini-3-pro-preview', # Changed from 'gemini-3.0-pro' to 'gemini-3-pro-preview'
            system_instruction=get_system_prompt(),
            safety_settings=SAFETY_SETTINGS
        )
        
        gemini_history = []
        for msg in history:
            role = "user" if msg['role'] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg['content']]})
            
        try:
            chat = model_with_sys.start_chat(history=gemini_history)
            
            # Send file + caption
            content_parts = [uploaded_file]
            if caption:
                content_parts.append(caption)
            else:
                if media_type == "image":
                    content_parts.append("Describe what you see.")
                elif media_type == "audio":
                    content_parts.append("Listen to this audio and respond.")
                elif media_type == "video":
                    content_parts.append("Watch this video and tell me what's happening.")
            
            
            # Use retry logic
            response = await send_message_with_retry(chat, content_parts)
            reply_text = clean_model_response(response.text)
            
        except Exception as e:
            print(f"Gemini multimodal error: {e}")
            reply_text = "I'm having trouble processing that."

        # 4. Save Bot Response
        await db.save_message(user_id, "assistant", reply_text, "telegram")
        
        # 5. Send to User
        await update.message.reply_text(reply_text)

# Initialize Application
if TELEGRAM_BOT_TOKEN:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VOICE | filters.AUDIO | filters.VIDEO, handle_multimodal))
else:
    application = None

async def process_telegram_update(data: dict):
    """Process webhook update."""
    if not application:
        return
    
    # Initialize bot if not already initialized (required for webhook)
    if not application._initialized:
        await application.initialize()
        await application.start()
        
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
