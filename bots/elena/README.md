# Coach Elena

Elena is your AI Physical Wellness Coach.

## Setup

1.  **Environment Variables**:
    Create a `.env` file in this directory (or set them in Render) with:
    ```
    GEMINI_API_KEY=your_key
    ELENA_TELEGRAM_BOT_TOKEN=your_new_bot_token
    SUPABASE_URL=your_url
    SUPABASE_KEY=your_key
    USER_TELEGRAM_ID=your_id
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run Locally**:
    ```bash
    python main.py
    ```

## Features
- **Daily Check-in**: 9:00 AM EST (Sleep/Diet).
- **Body Check**: Every 3 days.
- **Multimodal**: Send photos of food or videos of workouts.
- **Bilingual**: Speaks English and Chinese.
