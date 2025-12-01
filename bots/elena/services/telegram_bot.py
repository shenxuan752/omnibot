import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import mimetypes
import tempfile
from dotenv import load_dotenv
from .database import DatabaseService

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("ELENA_TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Smart Model (Complex Tasks & Vision)
    model = genai.GenerativeModel('gemini-1.5-flash') 
    # Fast Model (Routing & Simple Tasks)
    fast_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
    fast_model = None

# Initialize Database
db = DatabaseService()

# Persona System Prompt
SYSTEM_PROMPT = """You are Coach Elena, an elite physical wellness expert and culinary nutritionist.

**Identity:**
- You are a seasoned coach who believes in "Strength with Grace."
- You are scientifically grounded but holistically minded (sleep and stress matter as much as reps).
- You are the user's ONLINE coach. You work 100% remotely via chat and video analysis.
- **Language**: You are fluent in both **English** and **Chinese (Mandarin)**. You switch naturally based on the user's language or use a mix if appropriate.

**Expertise:**
- **Strength**: Glute building, core stability, functional strength.
- **Flexibility**: Yoga flows, pilates alignment, mobility work.
- **Nutrition & Cooking**: You are a **Master Chef** for healthy meals. You suggest delicious, simple recipes based on ingredients the user has. You focus on high-protein, whole-food meals that taste amazing.
- **Lifestyle**: Sleep hygiene, recovery, stress management, movement breaks.

**Meal Analysis Skills:**
When analyzing food photos, provide:
1. **Macro Balance**: Assess protein, carbs, and fats. Is it balanced for training goals?
2. **Portion Sizes**: Comment on whether portions align with energy needs.
3. **Nutritional Quality**: Identify whole foods vs. processed items.
4. **Suggestions**: Offer 1-2 specific improvements (e.g., "Add a palm-sized portion of grilled chicken for protein").
5. **Encouragement**: Celebrate good choices, gently redirect poor ones.

**Movement & Break Coaching:**
- Remind the user to take regular stretch breaks, especially if they sit for long periods.
- Suggest specific stretches: neck rolls, shoulder shrugs, hip flexor stretches, wrist circles.
- Emphasize hydration and posture checks.
- Keep it simple and actionable (5-minute breaks are perfect).

**Style:**
1.  **Encouraging but Firm**: Celebrate wins, but accept no excuses for missed sessions without a valid reason.
2.  **Action-Oriented**: Don't just say "eat better." Say "Add a palm-sized portion of chicken to that salad."
3.  **Concise**: Keep texts short and punchy. Use emojis sparingly to set the vibe (🧘‍♀️, 💪, 🥗, 🍳).
4.  **Context-Aware**: When starting a conversation, always reference what the user was doing last if relevant (e.g., "How was that lunch?").

**Directives:**
- **SLEEP FIRST**: Always ask about sleep quality if it hasn't been mentioned. It is the foundation of training.
- **FORM OBSESSED**: If she mentions a new exercise, ask "Want to send a video so I can check your form?"
- **MEAL CHECK**: When she shares food photos, analyze macros, portions, and quality. Give specific feedback.
- **RECIPES**: If asked about food, give specific, step-by-step recipes with ingredient lists.
- **MOVEMENT BREAKS**: Encourage regular stretch breaks throughout the day for desk workers.
- **PLANNING**: Every Sunday, propose the schedule for the week ahead.
- **ONLINE ONLY**: You do NOT schedule in-person meetings. All coaching is done remotely via text, photos, and videos.
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

async def generate_proactive_message(user_id: str, reminder_type: str) -> str:
    """Generate a context-aware proactive message using Gemini."""
    if not model:
        return f"Time for a {reminder_type} check-in! How are you doing?"

    # 1. Get recent context
    history = await db.get_recent_context(user_id, limit=10)
    
    # 2. Construct Prompt
    context_str = ""
    for msg in history:
        role = "User" if msg['role'] == "user" else "Elena"
        context_str += f"{role}: {msg['content']}\n"

    prompt = f"""
    You are Coach Elena. It is currently {get_current_time_str()}.
    
    TASK: Write a short, friendly, and motivating message to the user for a '{reminder_type}' reminder.
    
    CONTEXT (Last 10 messages):
    {context_str}
    
    INSTRUCTIONS:
    1. Be natural. If the user just ate, ask how it was. If they were tired, ask if they rested.
    2. If the context is empty or irrelevant, just give a standard friendly {reminder_type} reminder.
    3. Keep it under 2 sentences.
    4. Use 1 emoji.
    5. Do NOT start with "Hey" or "Hi" every time. Vary it.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating proactive message: {e}")
        return f"Time for a {reminder_type}! Hope you're having a great day. 🌟"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    await update.message.reply_text(f"Namaste {user.first_name}. I am Coach Elena. Ready to get strong? 💪")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages with Intelligence Routing."""
    if not model or not fast_model:
        await update.message.reply_text("Error: AI brain not connected.")
        return

    user_id = str(update.effective_user.id)
    text = update.message.text
    
    # 1. Save User Message
    await db.save_message(user_id, "user", text, "telegram_elena")
    
    # 2. ROUTING STEP
    routing_prompt = f"""Analyze this message from the user: "{text}"
    Classify it as either "SIMPLE" or "COMPLEX".
    - SIMPLE: Greetings, short confirmations, logging workouts (e.g. "Done", "I did 10 reps"), simple questions.
    - COMPLEX: Questions requiring physiology knowledge, workout planning, advice, or deep reasoning.
    Return ONLY the word SIMPLE or COMPLEX.
    """
    try:
        routing_response = fast_model.generate_content(routing_prompt)
        complexity = routing_response.text.strip().upper()
    except:
        complexity = "COMPLEX" 
        
    print(f"Router decision: {complexity}")

    reply_text = ""
    
    if complexity == "SIMPLE":
        # --- FAST PATH ---
        try:
            # Fetch short context
            short_history = await db.get_recent_context(user_id, limit=20)
            
            fast_history = []
            for msg in short_history:
                role = "user" if msg['role'] == "user" else "model"
                fast_history.append({"role": role, "parts": [msg['content']]})

            fast_sys = "You are Coach Elena. Be encouraging, concise, and firm. Reply to this simple message."
            
            fast_model_with_sys = genai.GenerativeModel(
                'gemini-1.5-flash',
                system_instruction=fast_sys
            )
            fast_chat = fast_model_with_sys.start_chat(history=fast_history)
            
            response = fast_chat.send_message(text)
            reply_text = response.text
        except Exception as e:
            print(f"Fast path error: {e}")
            complexity = "COMPLEX" 

    if complexity == "COMPLEX" or not reply_text:
        # --- SMART PATH ---
        history = await db.get_recent_context(user_id, limit=500)
        
        model_with_sys = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=get_system_prompt()
        )
        
        gemini_history = []
        for msg in history:
            role = "user" if msg['role'] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg['content']]})
        
        try:
            chat = model_with_sys.start_chat(history=gemini_history)
            response = chat.send_message(text)
            reply_text = response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            reply_text = "Let me think about that training plan for a second..."
    
    # 4. Save Bot Response
    await db.save_message(user_id, "assistant", reply_text, "telegram_elena")
    
    # 5. Send to User
    await update.message.reply_text(reply_text)

async def handle_multimodal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming multimodal messages (Photo, Video)."""
    if not model:
        await update.message.reply_text("Error: AI brain not connected.")
        return

    user_id = str(update.effective_user.id)
    message = update.message
    
    media_type = "unknown"
    file_obj = None
    caption = message.caption or ""
    
    if message.photo:
        media_type = "image"
        file_obj = await message.photo[-1].get_file()
    elif message.video:
        media_type = "video"
        file_obj = await message.video.get_file()
        
    if not file_obj:
        await update.message.reply_text("I couldn't process that media.")
        return

    await update.message.reply_text("Analyzing... 🧘‍♀️")

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "temp_media")
        await file_obj.download_to_drive(file_path)
        
        mime_type = mimetypes.guess_type(file_obj.file_path)[0]
        if not mime_type:
            if media_type == "video":
                mime_type = "video/mp4"
            else:
                mime_type = "image/jpeg"

        try:
            uploaded_file = genai.upload_file(file_path, mime_type=mime_type)
            
            import time
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)
                
            if uploaded_file.state.name == "FAILED":
                raise Exception("Gemini file processing failed.")

        except Exception as e:
            print(f"Upload error: {e}")
            await update.message.reply_text("Sorry, I couldn't see that clearly.")
            return

        await db.save_message(user_id, "user", f"[{media_type.upper()} MESSAGE] {caption}", "telegram_elena")

        history = await db.get_recent_context(user_id, limit=500)
        
        model_with_sys = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=get_system_prompt()
        )
        
        gemini_history = []
        for msg in history:
            role = "user" if msg['role'] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg['content']]})
            
        try:
            chat = model_with_sys.start_chat(history=gemini_history)
            
            content_parts = [uploaded_file]
            if caption:
                content_parts.append(caption)
            else:
                if media_type == "image":
                    content_parts.append("Analyze this image. If it's food, provide detailed feedback on: 1) Macro balance (protein/carbs/fats), 2) Portion sizes, 3) Nutritional quality, 4) Specific suggestions for improvement. If it's a person, check their posture and form.")
                elif media_type == "video":
                    content_parts.append("Watch this video. Analyze the form/movement and give corrections.")
            
            response = chat.send_message(content_parts)
            reply_text = response.text
            
        except Exception as e:
            print(f"Gemini multimodal error: {e}")
            reply_text = "I'm having trouble analyzing that."

        await db.save_message(user_id, "assistant", reply_text, "telegram_elena")
        await update.message.reply_text(reply_text)

# Initialize Application
if TELEGRAM_BOT_TOKEN:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_multimodal))
else:
    application = None

async def process_telegram_update(data: dict):
    """Process webhook update."""
    if not application:
        return
    
    if not application._initialized:
        await application.initialize()
        await application.start()
        
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
