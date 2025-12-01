# Deploy to Render.com (Free & Reliable)

## Prerequisites
1. GitHub account
2. Render.com account (sign up with GitHub)

## Step 1: Push Code to GitHub

1. Create a new repository on GitHub named `english-coach-bot`
2. Open your terminal and run:

```bash
cd /Users/a90362/Documents/D/AI_Project/gemini/telegram-english-coach
git init
git add .
git commit -m "Initial commit with Render support"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/english-coach-bot.git
git push -u origin main
```
*(Replace `YOUR_USERNAME` with your actual GitHub username)*

## Step 2: Create Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New +** -> **Web Service**
3. Connect your GitHub repository
4. Settings:
   - **Name:** `english-coach-bot`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** Free

5. **Environment Variables** (Click "Advanced" or "Environment"):
   Add these keys and values:
   - `TELEGRAM_BOT_TOKEN`: `YOUR_TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`: `YOUR_GEMINI_API_KEY`
   - `SUPABASE_URL`: `https://ewqchootxeeizzhmqdks.supabase.co`
   - `SUPABASE_KEY`: `YOUR_SUPABASE_KEY`
   - `PYTHON_VERSION`: `3.11.5` (Optional, but good practice)

6. Click **Create Web Service**

## Step 3: Keep It Awake (The Trick!)

Render free services sleep after 15 mins. To keep your 10 PM scheduler running:

1. Copy your Render URL (e.g., `https://english-coach-bot.onrender.com`)
   - It should show "I am alive! 🤖" when you visit it.
2. Go to [UptimeRobot.com](https://uptimerobot.com) (Free)
3. Create a new monitor:
   - **Type:** HTTP(s)
   - **Friendly Name:** English Coach
   - **URL:** Your Render URL
   - **Monitoring Interval:** 5 minutes
4. Start monitoring!

**Result:** UptimeRobot pings your bot every 5 mins -> Bot stays awake -> 10 PM task runs perfectly! 🎉
