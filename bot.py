import telebot
import json
import os

# --- CONFIGURATION ---
# ⚠️ WARNING: Your Bot Token is hardcoded here!
# Please rotate/change your bot token immediately after testing.
BOT_TOKEN = "8684244889:AAGRgsOSW-c4XW_hMMSeS7oAjlVVYyuw3dU"
ADMIN_ID = 8167497030
USERS_FILE = "users.json" # Local storage file for broadcast

# Initialize the Bot
bot = telebot.TeleBot(BOT_TOKEN)

# --- LOCAL DATABASE FUNCTIONS ---
def load_users():
    """Loads users from a local JSON file."""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_user(user_id):
    """Saves a new user to the local JSON file so /broadcast works without a database."""
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f)
            print(f"New user {user_id} added to local storage.")
        except Exception as e:
            print(f"Failed to save user {user_id}: {e}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    
    # 1. Save user locally (Instant, no database delay)
    save_user(user_id)

    # 2. Send the premium welcome message
    # Note: To use REAL custom animated Telegram Premium emojis, you must use HTML parse mode
    # and know the specific emoji ID. 
    # Example format: <tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>
    welcome_text = (
        "<b>✨ Welcome to Swift Inr! 🚀</b>\n\n"
        "💎 We are absolutely thrilled to have you here.\n\n"
        "🎯 <i>To access the exclusive mini app</i>, simply tap the button on the bottom left, "
        "right next to your message input field. Let's get started! 🌟"
    )
    # Using parse_mode="HTML" for premium formatting support
    bot.reply_to(message, welcome_text, parse_mode="HTML")

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    user_id = message.from_user.id
    
    # 1. Verify if the user is the Admin
    if user_id != ADMIN_ID:
        bot.reply_to(message, "⛔ You are not authorized to use this command.")
        return

    # 2. Extract the broadcast message
    # Removes the "/broadcast " command part from the text
    broadcast_text = message.text.replace('/broadcast', '').strip()
    
    if not broadcast_text:
        bot.reply_to(message, "⚠️ Please provide a message to broadcast.\n\nUsage: <code>/broadcast Your message here</code>", parse_mode="HTML")
        return

    # 3. Fetch all users from local JSON file and send the message
    bot.reply_to(message, "⏳ Starting broadcast... This may take a moment.")
    
    users = load_users()
    success_count = 0
    fail_count = 0

    for target_id in users:
        try:
            bot.send_message(target_id, broadcast_text)
            success_count += 1
        except Exception as e:
            # User might have blocked the bot or deleted their account
            fail_count += 1
            print(f"Failed to send to {target_id}: {e}")

    # 4. Send the final report to the admin
    report = (
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"Delivered successfully: {success_count} users\n"
        f"Failed to deliver: {fail_count} users"
    )
    bot.reply_to(message, report, parse_mode="HTML")

# Start the bot
if __name__ == '__main__':
    print("Bot is running...")
    # infinity_polling keeps the bot running even if it encounters temporary network errors
    bot.infinity_polling()
