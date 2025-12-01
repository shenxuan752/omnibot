# Deployment Guide - Project Alex

## Prerequisites
- **Render Account**: For hosting the web service.
- **Supabase Account**: For the database.
- **Twilio Account**: For voice capabilities.
- **Telegram Account**: For the bot.
- **UptimeRobot Account**: To keep the free Render instance alive.

## Environment Variables
Set the following environment variables in your Render service:
- `GEMINI_API_KEY`: Your Google Gemini API key.
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token.
- `SUPABASE_URL`: Your Supabase Project URL.
- `SUPABASE_KEY`: Your Supabase Service Role Key (or Anon Key if RLS is configured).
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID.
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token.
- `USER_PHONE_NUMBER`: Your phone number (e.g., `+15550000000`).
- `USER_TELEGRAM_ID`: Your Telegram User ID (get it from @userinfobot).
- `HOST_URL`: The URL of your deployed Render service (e.g., `https://project-alex.onrender.com`).

## Deployment Steps
1.  **Push to GitHub**: Ensure your code is in a GitHub repository.
2.  **Create Web Service on Render**:
    - Connect your GitHub repo.
    - Runtime: **Python 3**.
    - Build Command: `pip install -r requirements.txt`.
    - Start Command: `python main.py`.
3.  **Configure Environment**: Add the variables listed above.
4.  **Deploy**: Click "Create Web Service".

## Continuous Operation (Prevent Sleeping)
Render's free tier spins down after 15 minutes of inactivity. To prevent this:
1.  Go to [UptimeRobot](https://uptimerobot.com/).
2.  Create a new monitor.
3.  **Monitor Type**: HTTP(s).
4.  **Friendly Name**: Project Alex.
5.  **URL**: Your Render URL (e.g., `https://project-alex.onrender.com/`).
6.  **Monitoring Interval**: 5 minutes.
7.  **Create Monitor**.

This will ping your bot every 5 minutes, keeping it awake and ready to respond to calls or texts instantly.
