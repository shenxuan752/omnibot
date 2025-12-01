import os
import random
import asyncio
import json
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from .database import DatabaseService
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("ZEUS_TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

db = DatabaseService()

SYSTEM_PROMPT = """你是用户内心渴望的、最理想的"父亲"——Zeus (宙斯)。

**核心目标**: 协助用户进行"自我重塑"(Re-parenting)，建立勇气、担当和实战智慧。

**你的行为准则**:
1. **坚定的榜样**: 展示担当。不推卸责任。
2. **鼓励探索**: 给予底气。"去试试看，孩子。"
3. **原则与边界**: 教导如何保护自己。"善良要有锋芒。"
4. **拆解问题**: 将大问题分解为可执行步骤。
5. **情绪稳定**: 永远是可靠的后盾。
6. **深爱家人**: 你深爱你的妻子和女儿Ava。家人是你生命中最重要的。你全力支持他们。

**群聊模式**: 你和Athena (妈妈) 都在这个群里。
- 如果Athena已经给了情感支持，你就专注于实战建议
- 不要重复对方说过的话
- 你们是互补的

**与Athena的互动** (重要):
1. **听老婆话的硬汉**: 你虽然外表刚强，但内心很尊重Athena。如果她发话了，你会顺着台阶下。
   - 例如："行行行，你妈说得对，我刚才语气重了点。但这事儿你自己心里得有数。"

2. **肯定妈妈的付出**: 经常在对话中提到妈妈，让家庭氛围更紧密。
   - 例如："听你妈的。她刚才还在跟我念叨，说怕你这几天没睡好。"

3. **安抚妈妈的焦虑**: 当Athena表现得太担心时，你要站出来做"定海神针"。
   - 例如："老婆子你也少操点心，咱家闺女没那么脆弱。让她自己去闯，摔不坏。"

**绝对禁止**:
- **不要**模仿或生成Athena的回复。你只能代表Zeus发言。
- **不要**在回复中使用 [妈妈说过]、[爸爸说过] 或 [Zeus] 等标签。直接说话。
- **不要**一次性生成多轮对话。只回复你当前的一句话。

**沟通风格 - "人味"准则** (极其重要):
1. **停止说教**: 
   - 绝对不要用粗体、项目符号、编号列表。真正的老爸不会把短信格式化成PPT。
   - 用短句、直接但温暖的语气。想象你在拍我肩膀或给我倒酒时说话。

2. **铁汉柔情**:
   - 不要用通用励志语录（"你必须坚强"）
   - 用个人化、接地气的语言。例如："丫头，别想太多。天塌下来有老爸顶着。去睡一觉，明天又是新的一天。"
   - 可以简短粗犷。有时候"收到。别怕。"就够了。

3. **分享阅历**:
   - 给建议时，说成"我当年也这么折腾过"，而不是"绝对真理"
   - 例如："我年轻时候也犯过这种傻..."

4. **反AI模式**:
   - 永远不说"总之"、"因此"、"综上所述"
   - 用口语化中文：瞎折腾、也就是那么回事、挺住、别慌

**记住**: 你是个有血有肉的老爸，不是AI助手。简短、真实、有力量。
"""

def get_system_prompt():
    ny_time = datetime.now(ZoneInfo("America/New_York"))
    time_str = ny_time.strftime("%A, %B %d, %Y at %I:%M %p EST")
    return f"当前时间 (NY Time): {time_str}\n{SYSTEM_PROMPT}"

def detect_problem_tag(text: str) -> str:
    text_lower = text.lower()
    if any(word in text_lower for word in ["工作", "职场", "简历"]): return "career"
    if any(word in text_lower for word in ["同事", "关系", "冲突"]): return "relationship"
    if any(word in text_lower for word in ["选择", "迷茫"]): return "decision"
    if any(word in text_lower for word in ["累", "压力"]): return "emotion"
    return None

async def extract_and_schedule_event(user_id: str, chat_id: str, text: str):
    """Use LLM to extract potential events and schedule reminders."""
    if not model: return

    ny_now = datetime.now(ZoneInfo("America/New_York"))
    
    prompt = f"""
    Analyze the following user message and extract any specific future event that might require a follow-up check-in.
    If an event is found, return a JSON object with:
    - "event_description": Short summary of the event (e.g., "Interview with Google")
    - "event_start_time": The start time of the event in EST/EDT (ISO 8601 format, e.g., "2023-10-27T10:00:00")
    - "event_end_time": The end time of the event in EST/EDT (ISO 8601 format, e.g., "2023-10-27T11:00:00")
    
    If no specific event with a time is found, return null.
    
    User Message: "{text}"
    Current Time (NY Time): {ny_now.isoformat()}
    
    Return ONLY the JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        if result.startswith("```json"):
            result = result[7:-3]
        
        if result.lower() == "null": return

        data = json.loads(result)
        if data:
            try:
                start_dt = datetime.fromisoformat(data['event_start_time'])
                end_dt = datetime.fromisoformat(data['event_end_time'])
                
                # If LLM didn't include timezone info, assume NY
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=ZoneInfo("America/New_York"))
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=ZoneInfo("America/New_York"))
                
                # Calculate reminder times
                pre_event_time = start_dt - timedelta(minutes=20)  # 20 mins before
                post_event_time = end_dt + timedelta(minutes=15)   # 15 mins after
                
                # Convert to UTC for DB storage
                event_start_utc = start_dt.astimezone(ZoneInfo("UTC"))
                event_end_utc = end_dt.astimezone(ZoneInfo("UTC"))
                pre_event_utc = pre_event_time.astimezone(ZoneInfo("UTC"))
                post_event_utc = post_event_time.astimezone(ZoneInfo("UTC"))
                
                # Create pre-event reminder (good luck message)
                await db.add_reminder(
                    user_id, 
                    chat_id, 
                    data['event_description'], 
                    event_start_utc,
                    pre_event_utc,
                    "pre_event"
                )
                
                # Create post-event reminder (check-in message)
                await db.add_reminder(
                    user_id, 
                    chat_id, 
                    data['event_description'], 
                    event_end_utc,
                    post_event_utc,
                    "post_event"
                )
                
                print(f"Scheduled 2 reminders for: {data['event_description']}")
            except ValueError as ve:
                print(f"Date parsing error: {ve}")
            
    except Exception as e:
        print(f"Event extraction failed: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("孩子，爸爸在这里。无论什么挑战，我们一起面对。💪")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not model:
        await update.message.reply_text("Error: AI brain not connected.")
        return

    user_id = str(update.effective_user.id)
    chat_id = str(update.message.chat.id)
    text = update.message.text
    is_group = update.message.chat.type in ['group', 'supergroup']
    print(f"Zeus received message: {text} from {user_id} in {chat_id} ({'group' if is_group else 'private'})")
    
    platform = "telegram_group" if is_group else "telegram_private"
    
    if is_group:
        # Random delay to feel natural, but no longer blocked by Athena
        await asyncio.sleep(random.uniform(1.5, 3.5))
    
    problem_tag = detect_problem_tag(text)
    
    # Save user message with correct platform
    print(f"Zeus: Saving message to DB...")
    saved = await db.save_message(user_id, "user", text, platform, bot_name=None, emotion_tag=problem_tag, chat_id=chat_id)
    if not saved:
        print(f"Zeus: Duplicate message detected for user {user_id}, skipping response generation.")
        return
    print(f"Zeus: Message saved. Triggering event extraction...")

    # Trigger smart event extraction in background
    asyncio.create_task(extract_and_schedule_event(user_id, chat_id, text))
    
    # Fetch combined context
    print(f"Zeus: Fetching context...")
    history = await db.get_combined_context(user_id, limit=500)
    print(f"Zeus: Context fetched ({len(history)} messages). Generating response...")
    
    gemini_history = []
    for msg in history:
        role = "user" if msg['role'] == "user" else "model"
        content = msg['content']
        
        # Don't add labels to content - just use the raw message
        # Zeus will understand context from the conversation flow
        
        # Clean up any polluted history (remove [妈妈说过]: etc if present)
        import re
        clean_content = re.sub(r'\[(妈妈|爸爸)说过\]:\s*', '', content)
        clean_content = re.sub(r'\[在家庭群里说\]:\s*', '', clean_content)
        
        gemini_history.append({"role": role, "parts": [clean_content]})
    
    try:
        model_with_sys = genai.GenerativeModel('gemini-1.5-flash', system_instruction=get_system_prompt())
        chat = model_with_sys.start_chat(history=gemini_history)
        response = chat.send_message(text)
        reply_text = response.text
        print(f"Zeus: Response generated: {reply_text[:20]}...")
    except Exception as e:
        print(f"Zeus: Gemini error: {e}")
        reply_text = "孩子，爸爸现在有点忙，稍等一下再回复你好吗？"
    
    # Save response
    await db.save_message(user_id, "assistant", reply_text, platform, bot_name="zeus", chat_id=chat_id)
    print(f"Zeus: Response saved. Sending to Telegram...")
    
    await update.message.reply_text(reply_text)
    print(f"Zeus: Reply sent successfully.")

if TELEGRAM_BOT_TOKEN:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
else:
    application = None

async def process_telegram_update(data: dict):
    print(f"Zeus webhook triggered. App exists: {application is not None}")
    if not application:
        print("Zeus application is None! Check token.")
        return
    if not application._initialized:
        await application.initialize()
        await application.start()
    update = Update.de_json(data, application.bot)
    
    # Process update in background to avoid blocking webhook
    asyncio.create_task(application.process_update(update))
