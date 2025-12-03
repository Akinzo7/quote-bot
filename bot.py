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

# Files for persistent storage
SENT_FILE = "sent_messages.json"
QUOTES_DB = "quotes_database.json"

bot = Bot(token=TOKEN)

# ===== PERSISTENT STORAGE FUNCTIONS =====

def load_quotes_db():
    """Load all quotes from database"""
    try:
        with open(QUOTES_DB, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_quotes_db(quotes):
    """Save all quotes to database"""
    with open(QUOTES_DB, "w") as f:
        json.dump(quotes, f, indent=2)

def load_sent():
    """Load sent message IDs"""
    try:
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_sent(sent):
    """Save sent message IDs"""
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

# ===== QUOTE MANAGEMENT =====

def update_quotes_from_group():
    """Check for new messages in group and add to database"""
    print("🔍 Checking for new messages in group...")
    
    # Load existing quotes
    all_quotes = load_quotes_db()
    existing_texts = {q['text'] for q in all_quotes}
    
    # Get updates from Telegram
    updates = bot.get_updates(timeout=10)
    new_count = 0
    
    for u in updates:
        msg = u.message
        if msg and msg.chat.id == GROUP_ID:
            text = msg.text
            if text and text.strip() and text not in existing_texts:
                # Add new quote
                quote = {
                    'id': msg.message_id,
                    'text': text,
                    'date': str(msg.date),
                    'added_from': 'group'
                }
                all_quotes.append(quote)
                existing_texts.add(text)
                new_count += 1
                print(f"  📥 New quote: {text[:50]}...")
    
    # Save updated database
    if new_count > 0:
        save_quotes_db(all_quotes)
        print(f"✅ Added {new_count} new quotes to database")
    
    return all_quotes

def pick_message():
    """Pick a random unsent message"""
    # First update quotes from any new group messages
    all_quotes = update_quotes_from_group()
    
    if not all_quotes:
        return "📭 No quotes in database! Add some quotes to your group."
    
    # Get sent IDs
    sent_ids = load_sent()
    
    # Filter unsent quotes
    unsent = [q for q in all_quotes if q['id'] not in sent_ids]
    
    if not unsent:
        print("🔄 All quotes sent once. Resetting...")
        # Reset sent list
        sent_ids = []
        unsent = all_quotes.copy()
    
    # Pick random quote
    selected = random.choice(unsent)
    
    # Mark as sent
    sent_ids.append(selected['id'])
    save_sent(sent_ids)
    
    return selected['text']

# ===== MAIN FUNCTIONS =====

def send_daily_message():
    """Send one quote"""
    try:
        msg = pick_message()
        bot.send_message(chat_id=YOUR_USER_ID, text=msg)
        print(f"✅ Sent: {msg[:60]}...")
    except Exception as e:
        error_msg = f"❌ Error: {str(e)[:100]}"
        print(error_msg)
        try:
            bot.send_message(chat_id=YOUR_USER_ID, text=error_msg)
        except:
            pass

def show_stats():
    """Show database statistics"""
    quotes = load_quotes_db()
    sent = load_sent()
    print(f"📊 DATABASE STATS:")
    print(f"Total quotes: {len(quotes)}")
    print(f"Already sent: {len(sent)}")
    print(f"Available: {len(quotes) - len(sent)}")
    
    if quotes:
        print(f"\n📝 Recent quotes:")
        for q in quotes[-3:]:  # Last 3 quotes
            print(f"  - {q['text'][:50]}...")

# ===== SCHEDULER =====

def start_scheduler():
    """Start daily scheduler"""
    print(f"⏰ Starting daily scheduler at 7 AM ({TIMEZONE})...")
    print("The bot will:")
    print("1. Check for new messages in your group")
    print("2. Add them to the database")
    print("3. Send you one random unsent quote")
    print("\nPress Ctrl+C to stop")
    
    scheduler = BlockingScheduler(timezone=timezone(TIMEZONE))
    scheduler.add_job(send_daily_message, 'cron', hour=7, minute=0)
    
    # Show initial stats
    show_stats()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")

# ===== TEST =====
if __name__ == "__main__":
    # Update quotes and send test message
    print("🤖 Quote Bot Starting...")
    send_daily_message()
    show_stats()
    
    # Start scheduler
    start_scheduler()