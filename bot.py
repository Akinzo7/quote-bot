from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone
import random
import json
import os

# CONFIG - Load from environment
TOKEN = os.getenv("BOT_TOKEN", "")
GROUP_ID = int(os.getenv("GROUP_ID", "-1003235575515"))
YOUR_USER_ID = int(os.getenv("USER_ID", "7109052051"))
TIMEZONE = 'Africa/Lagos'
SENT_FILE = "sent_messages.json"

bot = Bot(token=TOKEN)

# Fetch all messages from the group (requires bot to be admin)
def fetch_group_messages():
    updates = bot.get_updates(timeout=10)
    messages = []
    for u in updates:
        msg = u.message
        if msg and msg.chat.id == GROUP_ID:
            text = msg.text
            if text:
                messages.append(text)
    return messages

# Load sent messages
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

# Save sent messages
def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

# Pick random unsent message
def pick_message():
    all_messages = fetch_group_messages()
    sent = load_sent()
    unsent = [m for m in all_messages if m not in sent]

    if not unsent:
        sent = []
        unsent = all_messages.copy()

    message = random.choice(unsent)
    sent.append(message)
    save_sent(sent)
    return message

# Send message to yourself
def send_daily_message():
    msg = pick_message()
    bot.send_message(chat_id=YOUR_USER_ID, text=msg)
    print(f"Sent message: {msg}")

# Test the function immediately
print("🤖 Bot starting... Testing send function now...")
try:
    send_daily_message()
    print("✅ Test message sent successfully!")
except Exception as e:
    print(f"❌ Error in test send: {e}")

# Start scheduler for 7 AM
print("\n⏰ Starting scheduler for daily 07:00 (Africa/Lagos)...")
scheduler = BlockingScheduler(timezone=timezone(TIMEZONE))
scheduler.add_job(send_daily_message, 'cron', hour=7, minute=0)

print("✅ Scheduler started!")
print("The bot will now send you a message every day at 7 AM.")
print("Keep this script running...")
print("Press Ctrl+C to stop\n")

try:
    scheduler.start()
except KeyboardInterrupt:
    print("\n👋 Scheduler stopped by user")
except Exception as e:
    print(f"❌ Scheduler error: {e}")