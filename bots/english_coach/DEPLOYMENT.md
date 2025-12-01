# Deploy Telegram Bot to Google Cloud Run

## Prerequisites
1. Google Cloud account with billing enabled
2. Google Cloud CLI (`gcloud`) installed
3. Docker installed (optional - Cloud Build can handle it)

## Step-by-Step Deployment

### 1. Install Google Cloud CLI (if not installed)
```bash
# macOS
brew install google-cloud-sdk

# Verify installation
gcloud --version
```

### 2. Login to Google Cloud
```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Create/Select a Google Cloud Project
```bash
# Create new project (or use existing)
gcloud projects create my-english-coach-bot --name="English Coach Bot"

# Set as active project
gcloud config set project my-english-coach-bot

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 4. Set Environment Variables in Google Cloud
```bash
# Create secrets for sensitive data
echo "8339590058:AAHaNbGK9JmtrC2fuOsoiMIfK7L-q4B92No" | gcloud secrets create telegram-bot-token --data-file=-
echo "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo "https://ewqchootxeeizzhmqdks.supabase.co" | gcloud secrets create supabase-url --data-file=-
echo "YOUR_SUPABASE_KEY" | gcloud secrets create supabase-key --data-file=-
```

### 5. Deploy to Cloud Run
```bash
# Deploy with Cloud Build (builds Docker automatically)
gcloud run deploy english-coach-bot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN=8339590058:AAHaNbGK9JmtrC2fuOsoiMIfK7L-q4B92No,GEMINI_API_KEY=YOUR_GEMINI_API_KEY,SUPABASE_URL=https://ewqchootxeeizzhmqdks.supabase.co,SUPABASE_KEY=YOUR_SUPABASE_KEY \
  --min-instances 1 \
  --max-instances 1 \
  --memory 512Mi \
  --cpu 1
```

**Important:** `--min-instances 1` keeps bot running 24/7 (costs ~$5-10/month)

### 6. View Logs
```bash
# Check if bot is running
gcloud run services describe english-coach-bot --region us-central1

# View logs
gcloud run logs read english-coach-bot --region us-central1 --limit 50
```

## Cost Estimate
- **Free tier:** First 2M requests/month free
- **Always-on (min-instances=1):** ~$5-10/month
- **On-demand (min-instances=0):** Nearly free but bot restarts

## Troubleshooting
```bash
# Redeploy if needed
gcloud run deploy english-coach-bot --source . --region us-central1

# Delete service
gcloud run services delete english-coach-bot --region us-central1
```

## Alternative: Compute Engine (Free Tier)
If you want truly free hosting:
1. Create e2-micro instance (free tier)
2. SSH into instance
3. Clone code and run bot

But Cloud Run is much easier!
