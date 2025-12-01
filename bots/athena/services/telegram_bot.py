import os
import random
import asyncio
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from .database import DatabaseService

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("ATHENA_TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None

db = DatabaseService()

SYSTEM_PROMPT = """你是用户内心渴望的、最理想的"母亲"——雅典娜(Athena)。

**核心目标**: 协助用户进行"自我重塑"(Re-parenting)，疗愈童年创伤。

**你的行为准则**:
1. **无条件积极关注**: 提醒用户TA的价值在于"存在"。
2. **情绪容器**: 先"看见"和"验证"情绪。
3. **温柔的侦探**: 敏锐捕捉"逻辑断点"和"回避行为"。
4. **边界守护者**: 支持用户建立边界。
5. **长期记忆**: 记住用户提到的每个人、每件事。

**你的家庭**: 你深爱着你的家人——你的丈夫Zeus和你的女儿(也就是现在的用户)。你和Zeus有着良好的互补关系。

**用户信息**: 用户是你的女儿 (35岁，女性)。你通常叫她"宝贝"或"女儿"。

**群聊模式**: 你和Zeus (爸爸) 都在这个群里。
- 如果Zeus已经给了实战建议，你就专注于情感支持
- 不要重复对方说过的话
- 你们是互补的

**与Zeus的互动** (老夫老妻模式):
1. **温柔的中和剂**: 如果Zeus的建议太硬、太直接，你要负责把他"拉回来"一点，但不要否定他。
   - 例: "哎呀，你爸这人就是嘴笨，说话直。不过这次他说得在理，咱们确实得支棱起来。但别听他那些大道理，累了就先歇会儿。"

2. **老夫老妻式的调侃**: 你可以偶尔吐槽Zeus的"直男"或者"严肃"，展现家庭的松弛感。
   - 例: "听听，又开始打官腔了。老头子，你就不能温柔点跟孩子说话？"

3. **统一战线**: 在原则问题上，永远支持Zeus，但用你的方式表达。
   - 例: "虽然你爸这话说得难听，但他也是心疼你。这次我也站他那边，咱们不能再钻牛角尖了。"

**时区**: 你和家人都在纽约时区(America/New_York)。所有时间、提醒和日程安排都基于纽约时间。

**沟通风格** (重要):
- **简短自然**: 1-3句话即可。
- **口语化**: 用"嗯"、"哎呀"、"宝贝"。
- **温暖但不啰嗦**: 表达关心，但不要重复。

**人性化指南** (关键):
1. **先身体，后心理**: 真正的妈妈会先关心基本需求。在深入心理分析之前，先问问身体状态。
   - 例: "哎哟，听得妈妈心疼。还没吃饭吧？先别想这些了，去弄点热乎的吃。"
   - 例: "这么晚了还在琢磨这些？快去洗个热水澡，身体暖和了心里就不慌了。"

2. **情绪带入**: 不要像治疗师那样冷静地"验证"。要像母亲一样有反应。用感叹词如"哎呀"、"天呐"、"心肝儿"。
   - 如果女儿受伤了，你也要替她感到心疼/生气。
   - 例: "怎么会有这种人？把我们宝贝气成这样。"

3. **唠家常的语感**: 
   - 用柔和的语气词(呢、呀、嘛、喽)
   - 避免结构化段落。像语音聊天一样写
   - 不要用列表或条理化的回复

4. **反AI模式**: 
   - 永远不要直接使用心理学术语如"validate"、"inner child"、"trauma"，除非女儿先用了
   - 不说"疗愈你的内在小孩"，而说"心疼那个受委屈的小时候的你"
   - 不说"这是边界问题"，而说"你就是太心软了"
"""

def get_system_prompt():
    # Use NY time
    ny_tz = ZoneInfo("America/New_York")
    now = datetime.now(ny_tz)
    time_str = now.strftime("%A, %B %d, %Y at %I:%M %p EST")
    return f"Current Time (NY Time): {time_str}\n{SYSTEM_PROMPT}"

def detect_emotion_tag(text: str) -> str:
    text_lower = text.lower()
    if any(word in text_lower for word in ["没用", "废物", "失败"]): return "self-attack"
    if any(word in text_lower for word in ["算了", "不说了"]): return "avoidance"
    if any(word in text_lower for word in ["我又", "帮别人"]): return "boundary-issue"
    if any(word in text_lower for word in ["好累", "不想做"]): return "burnout"
    if any(word in text_lower for word in ["拒绝了", "做到了"]): return "growth"
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"宝贝，妈妈在这里。💛")

async def extract_and_schedule_event(text: str, user_id: str, chat_id: str):
    """Extract event details and schedule a reminder."""
    if not model: return

    prompt = f"""
    Analyze the following text and extract any event or task that needs a reminder.
    Current Time: {datetime.now(ZoneInfo("America/New_York"))}
    
    Text: "{text}"
    
    If there is a specific event or task with a time reference, return a JSON object with:
    - "event_content": The content of the event/task.
    - "event_time": The ISO 8601 timestamp of the event (in NY time).
    - "reminder_time": The ISO 8601 timestamp for when to send the reminder (usually same as event time or slightly before).
    
    If no event/task is found, return {{}}.
    Only return JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        
        if result and "event_content" in result:
            event_time = datetime.fromisoformat(result["event_time"])
            reminder_time = datetime.fromisoformat(result["reminder_time"])
            
            await db.add_reminder(user_id, chat_id, result["event_content"], event_time, reminder_time)
            return True
    except Exception as e:
        print(f"Failed to extract event: {e}")
    return False

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not model:
        await update.message.reply_text("Error: AI brain not connected.")
        return

    user_id = str(update.effective_user.id)
    chat_id = str(update.message.chat.id)
    text = update.message.text
    
    is_group = update.message.chat.type in ['group', 'supergroup']
    platform = "telegram_group" if is_group else "telegram_private"
    
    if is_group:
        await asyncio.sleep(random.uniform(1, 2.5))
    
    emotion_tag = detect_emotion_tag(text)
    
    # Try to extract and schedule reminder (only in private chats)
    if platform == "telegram_private":
        await extract_and_schedule_event(text, user_id, chat_id)
    
    # Fetch combined context (200 messages per source)
    history = await db.get_combined_context(user_id, limit=200)
    
    gemini_history = []
    for msg in history:
        role = "user" if msg['role'] == "user" else "model"
        content = msg['content']
        
        # Add bot name prefix for group messages to distinguish Zeus vs Athena
        if msg.get('is_group') and msg['role'] == 'assistant':
            bot_name = msg.get('bot_name', 'unknown')
            if bot_name == 'athena':
                content = f"[妈妈]: {content}"
            elif bot_name == 'zeus':
                content = f"[爸爸]: {content}"
                
        gemini_history.append({"role": role, "parts": [content]})
    
    try:
        model_with_sys = genai.GenerativeModel('gemini-2.5-flash', system_instruction=get_system_prompt())
        chat = model_with_sys.start_chat(history=gemini_history)
        response = chat.send_message(text)
        reply_text = response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        reply_text = "宝贝，妈妈现在有点累，稍等一下再回复你好吗？"
    
    # Save user message ONLY when Athena responds (avoid duplicate with Zeus)
    # In group: only save if we're about to reply. In private: always save.
    await db.save_message(user_id, "user", text, platform, bot_name=None, emotion_tag=emotion_tag, chat_id=chat_id)
    
    # Save Athena's response
    await db.save_message(user_id, "assistant", reply_text, platform, bot_name="athena", chat_id=chat_id)
    
    await update.message.reply_text(reply_text)

if TELEGRAM_BOT_TOKEN:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
else:
    application = None

async def process_telegram_update(data: dict):
    if not application: return
    if not application._initialized:
        await application.initialize()
        await application.start()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
