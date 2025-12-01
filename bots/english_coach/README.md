# Telegram English Coach Bot

Your personal AI English learning assistant powered by Gemini 3 Pro!

## Features

✅ **Word Lookup** - Instant definitions + Chinese translations + pronunciation audio
✅ **Flashcard Review** - Interactive spaced repetition
✅ **Voice Shadowing** - Send voice messages, get AI feedback
✅ **Daily Journal** - 3-bullet reflection prompts
✅ **Word of the Day** - Daily vocabulary delivered to you
✅ **Missions** - Weekly real-world challenges

## Setup

### 1. Create Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Choose a name (e.g., "My English Coach")
4. Get your bot token

### 2. Configure Environment

Edit `.env` file:
```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
GEMINI_API_KEY=YOUR_GEMINI_KEY_HERE
SUPABASE_URL=https://ewqchootxeeizzhmqdks.supabase.co
SUPABASE_KEY=your_supabase_key_here
```

### 3. Run the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run bot
python bot.py
```

## Usage

- `/start` - Welcome message
- `/lookup synergy` - Look up a word
- Just type any word to look it up!
- Send voice messages for pronunciation practice
- `/review` - Start flashcard quiz
- `/help` - Show all commands

## Tech Stack

- **AI**: Google Gemini 3 Pro
- **Framework**: python-telegram-bot
- **Database**: Supabase
- **TTS**: Google Text-to-Speech

## Next Steps

- Add daily scheduled reminders
- Implement voice message handler
- Add journal prompts
- Deploy to cloud (Railway/Render)

Enjoy learning English! 🚀
