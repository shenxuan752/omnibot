# Zeus (宙斯) - 理想父亲 Agent

Zeus 是一个实战导师型AI陪伴者，提供勇气、担当和解决问题的智慧。

## 核心功能

- **坚定的榜样**: 展示担当，不推卸责任
- **鼓励探索**: 给予底气，推向世界
- **原则与边界**: 教导如何在复杂世界中保护自己
- **拆解问题**: 将大问题分解为可执行步骤
- **家庭群聊**: 与 Athena (妈妈) 一起在群组中回应
- **主动关怀**: 
  - 早上8:00 AM: 力量消息
  - 晚上10:30 PM: 晚安check-in
  - 周日晚上10:30 PM: 一周复盘

## 设置步骤

### 1. 创建Telegram Bot
```bash
# 在Telegram中找到 @BotFather
# 发送 /newbot
# 按提示创建bot并获取token
# 更新 .env 文件中的 ZEUS_TELEGRAM_BOT_TOKEN
```

### 2. 创建数据库表 (Family Chat Logs)
在Supabase SQL Editor中运行:
```sql
CREATE TABLE family_chat_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    bot_name TEXT,          -- 'athena' or 'zeus'
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    platform TEXT NOT NULL,
    emotion_tag TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_family_chat_created 
ON family_chat_logs(created_at DESC);

CREATE INDEX idx_family_chat_bot 
ON family_chat_logs(bot_name, created_at DESC);
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 本地测试
```bash
python3 main.py
```

### 5. 部署到Render
- 创建新的Web Service
- 连接GitHub仓库
- 设置环境变量
- 设置Telegram webhook
- 配置UptimeRobot

## 环境变量

```
GEMINI_API_KEY=your_key
ZEUS_TELEGRAM_BOT_TOKEN=your_token
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
USER_TELEGRAM_ID=your_id
PORT=8003
```
