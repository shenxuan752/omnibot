# Deploy to Railway (Free & Easy)

## Why Railway?
✅ $5 free credit/month (enough for bot)
✅ No credit card required initially
✅ Clear limits - no surprise charges
✅ 5 minute deployment

---

## Step-by-Step Deployment

### Option 1: Deploy from Local Files (Easiest)

1. **Install Railway CLI**
   ```bash
   npm i -g @railway/cli
   
   # Or with brew
   brew install railway
   ```

2. **Login to Railway**
   ```bash
   railway login
   ```
   Opens browser - sign up/login with GitHub

3. **Initialize Project**
   ```bash
   cd /Users/a90362/Documents/D/AI_Project/gemini/telegram-english-coach
   
   railway init
   ```
   Name your project: "English Coach Bot"

4. **Set Environment Variables**
   ```bash
   railway variables set TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   railway variables set GEMINI_API_KEY=YOUR_GEMINI_API_KEY
   railway variables set SUPABASE_URL=https://ewqchootxeeizzhmqdks.supabase.co
   railway variables set SUPABASE_KEY=YOUR_SUPABASE_KEY
   ```

5. **Deploy!**
   ```bash
   railway up
   ```
   
   Your bot is now live! 🎉

---

### Option 2: Deploy from GitHub (Recommended for updates)

1. **Create GitHub repo**
   ```bash
   cd /Users/a90362/Documents/D/AI_Project/gemini/telegram-english-coach
   git init
   git add .
   git commit -m "Initial commit"
   
   # Create repo on GitHub, then:
   git remote add origin https://github.com/YOUR_USERNAME/telegram-english-coach.git
   git push -u origin main
   ```

2. **Go to Railway**
   - Visit: https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repo
   - Add environment variables in Railway dashboard
   - Deploy!

---

## Check if Bot is Running

```bash
# View logs
railway logs

# Check status
railway status
```

---

## Cost
- **Free tier**: $5 credit/month
- **Your bot usage**: ~$2-3/month
- **No overages**: Stops when credit runs out (safe!)

---

## Troubleshooting

**Bot not responding?**
```bash
railway logs --follow
```

**Redeploy:**
```bash
railway up
```

**Remove deployment:**
```bash
railway down
```

---

That's it! Much simpler than Google Cloud 😊
