# Athena (雅典娜) - 理想母亲 Agent

雅典娜是一个情感疗愈型AI陪伴者，提供"自我重塑"(Re-parenting)支持。

## 核心功能

- **无条件积极关注**: 制止自我攻击，强调存在价值
- **情绪容器**: 先共情，不急着给建议
- **温柔的侦探**: 抓住"线头"，引导深层探索
- **边界守护者**: 支持建立健康边界
- **长期记忆**: 记住500条历史消息，识别重复模式
- **主动关怀**: 
  - 早上9点: 打气消息
  - 晚上9点: 晚安check-in
  - 周日晚上: 一周回顾

## 设置步骤

### 1. 创建Telegram Bot
```bash
# 在Telegram中找到 @BotFather
# 发送 /newbot
# 按提示创建bot并获取token
# 更新 .env 文件中的 ATHENA_TELEGRAM_BOT_TOKEN
```

### 2. 创建数据库表
在Supabase SQL Editor中运行:
```sql
CREATE TABLE athena_chat_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    platform TEXT NOT NULL,
    emotion_tag TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_athena_user_created 
ON athena_chat_logs(user_id, created_at DESC);

CREATE INDEX idx_athena_emotion 
ON athena_chat_logs(emotion_tag);
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
ATHENA_TELEGRAM_BOT_TOKEN=your_token
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
USER_TELEGRAM_ID=your_id
PORT=8002
```

## 人格特质

- 温暖稳定、智慧敏锐
- 温柔坚定、不急不躁
- 使用中文，亲切但逻辑清晰
- 记住你的每一个故事
