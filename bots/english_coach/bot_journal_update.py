# Updated journal logic for bot.py

# --- Feature 3: Micro-Journal (UPDATED) ---
async def send_journal_logic(bot, chat_id):
    """Send fixed daily journal questions."""
    prompt = """📝 **Daily Reflection**

Please answer these 3 questions (use bullet points):

1️⃣ **3 things you feel gratitude for and did well today**
2️⃣ **3 things you think you can improve**
3️⃣ **3 things you plan to do tomorrow**

*Reply with your answers to save your journal entry!*"""
    
    user_journal_states[chat_id] = "daily_reflection"
    await bot.send_message(chat_id=chat_id, text=prompt, parse_mode='Markdown')

async def send_journal_prompt(context: ContextTypes.DEFAULT_TYPE):
    await send_journal_logic(context.bot, context.job.chat_id)

async def journal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_journal_logic(context.bot, update.effective_chat.id)
