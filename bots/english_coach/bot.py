import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, JobQueue
import os
from dotenv import load_dotenv
from datetime import time, datetime
import pytz
import random
import asyncio

from .services.gemini_ai import lookup_word, generate_word_of_day, analyze_audio_file, generate_journal_prompt, generate_weekly_mission
from .services.database import save_flashcard, get_flashcards, save_journal, save_mission_completion, get_random_journal, save_user, get_all_users
from .services.tts import text_to_speech
from .services.shadowing import generate_shadowing_task, create_reference_audio, analyze_voice_attempt

load_dotenv()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# State management
user_shadowing_tasks = {}
user_journal_states = {} # chat_id -> prompt_text
user_review_states = {} # chat_id -> {words: [], index: 0}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and set up schedules."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Save user to DB for persistence
    await save_user(user_id)
    
    # Schedule jobs
    await schedule_user_jobs(context.job_queue, chat_id, user_id)
    
    welcome_msg = """👋 **Welcome to English Coach Bot!**

I'm your 24/7 AI Coach powered by Gemini 1.5 Flash (Fast!).

**Daily Schedule:**
☀️ 09:00 AM - Word of the Day
🚀 Mon 9 AM - Weekly Mission
✍️ 11:30 PM - Micro-Journal
🎤 10:00 PM - Shadowing Practice

**Features:**
🔍 **Lookup:** Send ANY word
🎤 **Voice:** Send audio for analysis
🧠 **Review:** /review your words
📊 **Stats:** /stats

**Manual Triggers:**
/wod - Get Word of the Day now
/journal - Get Journal prompt now
/shadowing - Get Shadowing task now
/memory - See a random past journal

Let's start! Send me a word to define."""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def schedule_user_jobs(job_queue, chat_id, user_id):
    """Schedule all recurring jobs for a user."""
    if not job_queue:
        logger.warning(f"JobQueue is not available. Skipping schedule for user {user_id}.")
        return

    # 1. Word of the Day (9 AM)
    job_queue.run_daily(
        send_word_of_day,
        time=time(hour=9, minute=0, tzinfo=pytz.timezone('America/New_York')),
        chat_id=chat_id,
        name=f'wod_{user_id}'
    )
    
    # 2. Weekly Mission (Monday 9 AM)
    job_queue.run_daily(
        send_weekly_mission,
        time=time(hour=9, minute=0, tzinfo=pytz.timezone('America/New_York')),
        days=(1,), # Monday
        chat_id=chat_id,
        name=f'mission_{user_id}'
    )
    
    # 3. Daily Journal (9 PM)
    job_queue.run_daily(
        send_journal_prompt,
        time=time(hour=23, minute=30, tzinfo=pytz.timezone('America/New_York')),
        chat_id=chat_id,
        name=f'journal_{user_id}'
    )
    
    # 4. Shadowing (10 PM)
    job_queue.run_daily(
        send_shadowing_task,
        time=time(hour=22, minute=0, tzinfo=pytz.timezone('America/New_York')),
        chat_id=chat_id,
        name=f'shadowing_{user_id}'
    )
    logger.info(f"Scheduled jobs for user {user_id}")

async def restore_jobs(application):
    """Restore jobs for all active users on startup."""
    logger.info("Restoring jobs for all users...")
    users = await get_all_users()
    for user_id in users:
        # Assuming chat_id is same as user_id for private chats
        await schedule_user_jobs(application.job_queue, user_id, user_id)
    logger.info(f"Restored jobs for {len(users)} users.")

# --- Job Callbacks ---

async def send_word_of_day(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        wod = await generate_word_of_day()
        msg = f"""☀️ **Word of the Day: {wod['word']}**

**Definition:** {wod['definition']}
**Chinese:** {wod['chinese']}
**Example:** _{wod['example']}_"""
        
        await context.bot.send_message(job.chat_id, text=msg, parse_mode='Markdown')
        
        # Audio
        audio_path = await text_to_speech(wod['word'])
        with open(audio_path, 'rb') as audio:
            await context.bot.send_voice(job.chat_id, audio)
        os.remove(audio_path)
        
        # Save to flashcards automatically
        await save_flashcard(wod, job.chat_id) # Assuming chat_id is user_id
        
    except Exception as e:
        logger.error(f"Error sending WOD: {e}")

async def send_weekly_mission(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        mission = await generate_weekly_mission()
        msg = f"""🚀 **Weekly Mission: {mission['title']}**

{mission['description']}

**Goal:** {mission['goal']}

*Reply with "Mission Complete" when done!*"""
        await context.bot.send_message(job.chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending mission: {e}")

async def send_journal_prompt(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        prompt = await generate_journal_prompt()
        user_journal_states[job.chat_id] = prompt
        
        msg = f"""✍️ **Micro-Journal Time**

**Prompt:** {prompt}

*Reply with your answer (1-2 sentences).*"""
        await context.bot.send_message(job.chat_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending journal prompt: {e}")

async def send_shadowing_task(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        task = await generate_shadowing_task()
        user_shadowing_tasks[job.chat_id] = task
        
        msg = f"""🎤 **Shadowing Practice**

**Sentence:** "{task['sentence']}"

1. Listen to the audio below.
2. Record yourself saying it.
3. Send the voice note here."""
        
        await context.bot.send_message(job.chat_id, text=msg, parse_mode='Markdown')
        
        # Reference Audio
        audio_path = await create_reference_audio(task['sentence'])
        with open(audio_path, 'rb') as audio:
            await context.bot.send_voice(job.chat_id, audio)
        os.remove(audio_path)
        
    except Exception as e:
        logger.error(f"Error sending shadowing task: {e}")

# --- Commands ---

async def shadowing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Manual trigger
    chat_id = update.effective_chat.id
    # Ensure user is saved
    await save_user(update.effective_user.id)
    
    # Create a dummy job object to reuse the function
    class DummyJob:
        def __init__(self, chat_id):
            self.chat_id = chat_id
    
    context.job = DummyJob(chat_id)
    await send_shadowing_task(context)

async def wod_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Ensure user is saved
    await save_user(update.effective_user.id)
    
    class DummyJob:
        def __init__(self, chat_id):
            self.chat_id = chat_id
    context.job = DummyJob(chat_id)
    await send_word_of_day(context)

async def journal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Ensure user is saved
    await save_user(update.effective_user.id)
    
    class DummyJob:
        def __init__(self, chat_id):
            self.chat_id = chat_id
    context.job = DummyJob(chat_id)
    await send_journal_prompt(context)

async def review_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start flashcard review session (Quiz Mode)."""
    user_id = update.effective_user.id
    # Fetch up to 20 due cards
    cards = await get_flashcards(user_id, limit=20, mode='review')
    
    if not cards:
        await update.message.reply_text("🎉 No cards due for review! You're all caught up.\nUse /review again later or lookup new words.")
        return
        
    # Shuffle
    random.shuffle(cards)
    
    user_review_states[update.effective_chat.id] = {
        'cards': cards,
        'index': 0
    }
    
    await update.message.reply_text(f"🚀 Starting Quiz: {len(cards)} words due.")
    await send_review_card(update.effective_chat.id, context)

async def send_review_card(chat_id, context):
    state = user_review_states.get(chat_id)
    if not state or state['index'] >= len(state['cards']):
        await context.bot.send_message(chat_id=chat_id, text="🎉 Review complete! Great job.")
        if chat_id in user_review_states:
            del user_review_states[chat_id]
        return

    card = state['cards'][state['index']]
    
    # Quiz Mode: Show word, hide definition
    keyboard = [[InlineKeyboardButton("👁️ Reveal Answer", callback_data="reveal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🧠 **Quiz ({state['index']+1}/{len(state['cards'])})**\n\nWord: **{card['word']}**\n\n*Do you know this word?*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    state = user_review_states.get(chat_id)
    
    if not state:
        await query.edit_message_text("Session expired.")
        return

    card = state['cards'][state['index']]

    if query.data == "reveal":
        # Show answer and grading buttons
        keyboard = [
            [
                InlineKeyboardButton("🔊 Listen", callback_data="listen"),
            ],
            [
                InlineKeyboardButton("✅ I knew it", callback_data="know"),
                InlineKeyboardButton("❌ Forgot", callback_data="forgot")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        ipa_text = f"\n**IPA:** {card.get('ipa', '')}" if card.get('ipa') else ""
        
        await query.edit_message_text(
            text=f"🧠 **{card['word']}**{ipa_text}\n📖 {card['definition']}\n🇨🇳 {card['chinese']}\n📝 _{card['example']}_",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
    elif query.data == "listen":
        # Send audio
        try:
            audio_path = await text_to_speech(card['word'])
            with open(audio_path, 'rb') as audio:
                await context.bot.send_voice(chat_id, audio)
            os.remove(audio_path)
        except Exception as e:
            print(f"Error sending audio: {e}")
            
    elif query.data in ["know", "forgot"]:
        print(f"English Coach: Review button clicked: {query.data}")
        # Update SRS progress
        success = (query.data == "know")
        try:
            await update_flashcard_progress(card['id'], success)
            print(f"English Coach: Progress updated for card {card['id']}")
        except Exception as e:
            print(f"English Coach: Error updating progress: {e}")
        
        # Feedback
        feedback = "✅ Great!" if success else "💪 Keep practicing!"
        await context.bot.send_message(chat_id=chat_id, text=feedback)
        
        # Next card
        state['index'] += 1
        print(f"English Coach: Moving to index {state['index']}")
        await send_review_card(chat_id, context)

# --- Handlers ---

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (Journal vs Word Lookup)."""
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Check if waiting for journal
    if chat_id in user_journal_states:
        prompt = user_journal_states[chat_id]
        
        # Save journal with date
        try:
            entry_date = datetime.now().strftime("%Y-%m-%d")
            result = await save_journal({
                "entry_date": entry_date,
                "entry": text
            }, user_id)
            del user_journal_states[chat_id]
            
            logger.info(f"Journal saved for user {user_id}: {result}")
            await update.message.reply_text("✅ Journal entry saved!")
        except Exception as e:
            logger.error(f"Error saving journal: {e}")
            await update.message.reply_text(f"❌ Error saving journal: {e}")
        return

    # Check for Mission Complete
    if text.lower().startswith("mission complete"):
        await save_mission_completion({'status': 'completed'}, user_id)
        await update.message.reply_text("🎉 Mission accomplished! Great job!")
        return

    # Otherwise: Word Lookup
    if len(text.split()) <= 3:
        await process_word_lookup(update, text)
    else:
        await update.message.reply_text("Just send a word to lookup, or use /help.")

async def process_word_lookup(update: Update, word: str):
    await update.message.reply_text(f"🔍 Looking up '{word}'...")
    try:
        result = await lookup_word(word)
        
        response = f"""📚 **{result['word'].upper()}**
        
**Definition:** {result['definition']}
**IPA:** {result.get('ipa', '')}
**Chinese:** {result['chinese']}
**Example:** _{result['example']}_"""
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
        audio_path = await text_to_speech(result['word'])
        with open(audio_path, 'rb') as audio:
            await update.message.reply_voice(audio)
        os.remove(audio_path)
        
        # Save
        save_result = await save_flashcard(result, update.effective_user.id)
        if save_result and save_result.get('status') == 'skipped':
             await update.message.reply_text("⚠️ Word already in flashcards!")
        else:
             await update.message.reply_text("✅ Saved!")
             
    except Exception as e:
        logger.error(f"Lookup error: {e}")
        await update.message.reply_text("Could not find that word.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    voice_file = await update.message.voice.get_file()
    file_path = f"voice_{chat_id}.ogg"
    await voice_file.download_to_drive(file_path)
    
    await update.message.reply_text("🎧 Analyzing...")
    
    try:
        if chat_id in user_shadowing_tasks:
            # Shadowing feedback
            feedback = await analyze_audio_file(file_path)
            # Use None for parse_mode to avoid markdown errors with raw text
            await update.message.reply_text(f"✅ **Shadowing Feedback**\n\n{feedback['text']}", parse_mode=None)
            del user_shadowing_tasks[chat_id]
        else:
            # General analysis
            feedback = await analyze_audio_file(file_path)
            # Use None for parse_mode to avoid markdown errors with raw text
            await update.message.reply_text(f"🎙️ **Voice Analysis**\n\n{feedback['text']}", parse_mode=None)
            
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve a random past journal entry."""
    user_id = update.effective_user.id
    entry = await get_random_journal(user_id)
    
    if not entry:
        await update.message.reply_text("📝 No journal entries yet! Use /journal to start writing.")
        return
    
    entry_date = entry.get('entry_date', 'Unknown date')
    entry_text = entry.get('entry', 'No content')
    
    msg = f"""📖 **Memory from {entry_date}**

{entry_text}

*Use /memory to see another random entry!*"""
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**Commands:**\n/shadowing - Practice\n/wod - Word of Day\n/journal - Journal\n/memory - Random journal\n/review - Flashcards\n/stats - Progress\n/help - Info",
        parse_mode='Markdown'
    )

async def debug_jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all scheduled jobs."""
    jobs = context.job_queue.jobs()
    if not jobs:
        await update.message.reply_text("No jobs scheduled.")
        return
        
    msg = "📅 **Scheduled Jobs:**\n\n"
    for job in jobs:
        next_run = job.next_t.strftime("%Y-%m-%d %H:%M:%S %Z") if job.next_t else "Unknown"
        msg += f"🔹 **{job.name}**\n   Next run: {next_run}\n\n"
        
    await update.message.reply_text(msg, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cards = await get_flashcards(user_id, limit=5)
    await update.message.reply_text(f"📊 You have **{len(cards) if cards else 0}** flashcards saved.", parse_mode='Markdown')

# Initialize Application
token = os.getenv('ENGLISH_COACH_TELEGRAM_BOT_TOKEN')
if token:
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("shadowing", shadowing_command))
    application.add_handler(CommandHandler("wod", wod_command))
    application.add_handler(CommandHandler("journal", journal_command))
    application.add_handler(CommandHandler("review", review_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("memory", memory_command))
    application.add_handler(CommandHandler("debug_jobs", debug_jobs_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
else:
    application = None

async def process_telegram_update(data: dict):
    """Process webhook update."""
    if not application:
        return
    
    if not application._initialized:
        await application.initialize()
        await application.start()
        # Restore jobs on startup
        await restore_jobs(application)
        
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
