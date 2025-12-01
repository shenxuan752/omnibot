# Deploy to Oracle Cloud Always-Free (Best for 24/7 Bots)

## Why Oracle Cloud?
✅ **Truly free FOREVER** - no credit card charges ever
✅ **Always-on** - VM runs 24/7
✅ **Perfect for scheduled tasks** - your 10 PM reminders will work!
✅ **No limits** - unlimited API calls

---

## Step-by-Step Setup (20 minutes)

### Part 1: Create Oracle Cloud Account

1. **Go to:** https://www.oracle.com/cloud/free/
2. **Click "Start for free"**
3. **Sign up** (requires email + phone verification)
4. **Add credit card** (required for verification but WON'T be charged)
   - Oracle clearly states: "Always Free services never expire"
   - Your bot uses Always-Free tier only

---

### Part 2: Create a VM Instance

1. **Login to Oracle Cloud Console**
   - https://cloud.oracle.com

2. **Create Compute Instance:**
   - Click **"Create a VM instance"**
   - Name: `english-coach-bot`
   - Image: **Ubuntu 22.04** (minimal)
   - Shape: **VM.Standard.E2.1.Micro** (Always Free eligible)
   - **IMPORTANT:** Check "Assign a public IPv4 address"
   - Click **"Create"**

3. **Download SSH Key:**
   - During instance creation, Oracle generates an SSH key
   - **Download and save it!** (e.g., `ssh-key.key`)
   - Move it: `mv ~/Downloads/ssh-key.key ~/.ssh/oracle-bot.key`
   - Set permissions: `chmod 400 ~/.ssh/oracle-bot.key`

4. **Wait 2-3 minutes** for instance to start

---

### Part 3: Connect to Your VM

1. **Get your VM's IP address** from Oracle console (e.g., `123.45.67.89`)

2. **SSH into your VM:**
   ```bash
   ssh -i ~/.ssh/oracle-bot.key ubuntu@YOUR_VM_IP
   ```
   
   Replace `YOUR_VM_IP` with your actual IP.

---

### Part 4: Install Python & Dependencies

Once connected to your VM, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python & pip
sudo apt install python3 python3-pip python3-venv git -y

# Install system dependencies for audio (needed for edge-tts)
sudo apt install ffmpeg -y

# Create directory for bot
mkdir ~/english-coach-bot
cd ~/english-coach-bot
```

---

### Part 5: Upload Your Bot Code

**From your Mac (new terminal window):**

```bash
# Copy your bot code to the VM
cd /Users/a90362/Documents/D/AI_Project/gemini/telegram-english-coach

scp -i ~/.ssh/oracle-bot.key -r \
  bot.py \
  services/ \
  requirements.txt \
  .env \
  ubuntu@YOUR_VM_IP:~/english-coach-bot/
```

Replace `YOUR_VM_IP` with your VM's IP address.

---

### Part 6: Run Your Bot

**Back in your VM SSH session:**

```bash
cd ~/english-coach-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test run bot
python bot.py
```

You should see: "🤖 Bot running with daily shadowing at 10 PM!"

**Press Ctrl+C to stop** (we'll make it run permanently next)

---

### Part 7: Make Bot Run 24/7 (systemd service)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/english-coach-bot.service
```

**Paste this content:**
```ini
[Unit]
Description=English Coach Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/english-coach-bot
Environment="PATH=/home/ubuntu/english-coach-bot/venv/bin"
ExecStart=/home/ubuntu/english-coach-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save:** Ctrl+X, then Y, then Enter

**Enable and start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable english-coach-bot
sudo systemctl start english-coach-bot

# Check status
sudo systemctl status english-coach-bot
```

You should see: "active (running)"

**View logs:**
```bash
sudo journalctl -u english-coach-bot -f
```

---

## Your Bot is Now Live 24/7! 🎉

**Features working:**
- ✅ Word lookup anytime
- ✅ Daily 10 PM shadowing reminders
- ✅ Voice analysis
- ✅ Database saving
- ✅ Runs forever (even if you close your laptop!)

---

## Useful Commands

**Check bot status:**
```bash
sudo systemctl status english-coach-bot
```

**Restart bot:**
```bash
sudo systemctl restart english-coach-bot
```

**View logs:**
```bash
sudo journalctl -u english-coach-bot -f
```

**Stop bot:**
```bash
sudo systemctl stop english-coach-bot
```

**Update bot code:**
```bash
# From your Mac, upload new code
scp -i ~/.ssh/oracle-bot.key bot.py ubuntu@YOUR_VM_IP:~/english-coach-bot/

# Then restart
ssh -i ~/.ssh/oracle-bot.key ubuntu@YOUR_VM_IP "sudo systemctl restart english-coach-bot"
```

---

## Cost: $0 Forever

Oracle's Always-Free tier includes:
- 2 VMs (you're using 1)
- 200GB storage total
- No time limits
- No surprise charges

**Your bot is 100% free forever!** 🎉

---

## Troubleshooting

**Can't SSH?**
- Check VM is running in Oracle Console
- Verify security list allows port 22

**Bot not responding?**
```bash
sudo journalctl -u english-coach-bot -n 50
```

**Need to update environment variables?**
```bash
nano ~/english-coach-bot/.env
sudo systemctl restart english-coach-bot
```

---

Enjoy your 24/7 English Coach Bot! 🚀
