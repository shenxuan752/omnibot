import re
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    fast_model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
else:
    fast_model = None

# Time/date keywords to detect
TIME_KEYWORDS = [
    # Days
    "tomorrow", "today", "tonight", "monday", "tuesday", "wednesday", 
    "thursday", "friday", "saturday", "sunday",
    # Times
    "am", "pm", "morning", "afternoon", "evening", "night", "noon", "midnight",
    # Phrases
    "at", "pick me up", "pick you up", "meet me", "meet you", "let's go",
    "see you", "call me", "call you"
]

# Cancellation keywords
CANCELLATION_KEYWORDS = [
    "cancel", "nevermind", "never mind", "forget it", "changed my mind",
    "can't make it", "won't make it", "not going", "let's not"
]

def has_time_keywords(message: str) -> bool:
    """Quick check if message contains time/date keywords."""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in TIME_KEYWORDS)

def has_cancellation_keywords(message: str) -> bool:
    """Quick check if message contains cancellation keywords."""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in CANCELLATION_KEYWORDS)

async def extract_plans_from_conversation(messages: List[Dict], user_message: str) -> List[Dict]:
    """
    Extract time-based plans from conversation using Gemini.
    Returns list of {scheduled_time, message_content, context}
    """
    if not fast_model:
        print("Gemini not configured, skipping plan extraction")
        return []
    
    # Build conversation context
    context = ""
    for msg in messages[-10:]:  # Last 10 messages
        role = "Ava" if msg['role'] == "user" else "Alex"
        context += f"{role}: {msg['content']}\n"
    
    # Get current time in NYC
    est_offset = timezone(timedelta(hours=-5))
    now_nyc = datetime.now(est_offset)
    current_time_str = now_nyc.strftime("%A, %B %d, %Y at %I:%M %p EST")
    
    prompt = f"""You are analyzing a conversation to extract time-based plans or commitments.

Current time: {current_time_str}

Recent conversation:
{context}

Latest message from Ava: "{user_message}"

Task: Identify if Ava mentioned any specific time-based plans that Alex should remind her about.

Examples of plans to extract:
- "Pick me up at 8am for hiking" → Alex should text at 7:55 AM
- "Let's meet at 3pm tomorrow" → Alex should text at 2:55 PM tomorrow
- "Call me at noon" → Alex should call/text at 11:55 AM

If you find a plan:
1. Extract the scheduled time (convert to specific datetime)
2. Generate a natural reminder message Alex would send (casual, with emoji)
3. Provide brief context

Return ONLY a JSON array (even if empty). Format:
[
  {{
    "scheduled_datetime": "2025-11-30T07:55:00",
    "message": "hey, heading out now to pick you up 🚗",
    "context": "hiking at 9am"
  }}
]

If NO plans found, return: []

IMPORTANT: 
- Subtract 5 minutes from the scheduled time for the reminder
- Use ISO format for datetime (YYYY-MM-DDTHH:MM:SS)
- Assume NYC timezone (EST/EDT)
- Only extract plans with specific times, not vague ones like "later" or "soon"
"""

    try:
        response = fast_model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract JSON from response
        import json
        # Remove markdown code blocks if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        plans = json.loads(result_text)
        
        # Convert datetime strings to datetime objects
        for plan in plans:
            dt_str = plan['scheduled_datetime']
            # Parse ISO format and add NYC timezone
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=est_offset)
            plan['scheduled_time'] = dt
            plan['message_content'] = plan.pop('message')
            plan.pop('scheduled_datetime')
        
        print(f"Extracted {len(plans)} plan(s) from conversation")
        return plans
        
    except Exception as e:
        print(f"Error extracting plans: {e}")
        return []

async def detect_cancellation(user_message: str, messages: List[Dict], scheduled_messages: List[Dict]) -> List[int]:
    """
    Detect if user is cancelling a scheduled plan.
    Returns list of scheduled message IDs to cancel.
    """
    if not fast_model or not scheduled_messages:
        return []
    
    # Build context
    context = ""
    for msg in messages[-5:]:
        role = "Ava" if msg['role'] == "user" else "Alex"
        context += f"{role}: {msg['content']}\n"
    
    # Build scheduled plans summary
    plans_summary = "Scheduled plans:\n"
    for sm in scheduled_messages:
        plans_summary += f"- ID {sm['id']}: {sm['context']} at {sm['scheduled_time']}\n"
    
    prompt = f"""You are analyzing if a user is cancelling a previously scheduled plan.

Recent conversation:
{context}

Latest message from Ava: "{user_message}"

{plans_summary}

Task: Determine if Ava is cancelling any of the scheduled plans above.

Return ONLY a JSON array of plan IDs to cancel. Format:
[1, 3]

If NO cancellations, return: []

Examples:
- "Let's cancel the hike" → find plans with "hike" in context
- "Never mind about tomorrow" → find plans scheduled for tomorrow
- "I can't make it to the meeting" → find plans with "meeting" in context
"""

    try:
        response = fast_model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Extract JSON
        import json
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        cancelled_ids = json.loads(result_text)
        print(f"Detected {len(cancelled_ids)} cancellation(s)")
        return cancelled_ids
        
    except Exception as e:
        print(f"Error detecting cancellation: {e}")
        return []
