import telebot
from pymongo import MongoClient
import certifi # Added certifi for SSL resolution

# --- CONFIGURATION ---
# Replace these with environment variables in a real production environment!
# Please CHANGE these credentials as they were exposed!
BOT_TOKEN = "8684244889:AAGRgsOSW-c4XW_hMMSeS7oAjlVVYyuw3dU"
MONGO_URI = "mongodb+srv://laads761_db_user:YOUR_NEW_PASSWORD@cluster0.iqcvxxk.mongodb.net/?appName=Cluster0"
ADMIN_ID = 8167497030

# Initialize the Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize MongoDB connection
try:
    # Added tlsCAFile=certifi.where() to fix the SSL handshake error
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client['swift_int_bot_db'] # Creates/selects the database
    users_collection = db['users']   # Creates/selects the collection
    
    # Send a quick ping to confirm the connection is fully established
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    
    # 1. Save user to MongoDB if they don't already exist
    if not users_collection.find_one({"user_id": user_id}):
        try:
            users_collection.insert_one({"user_id": user_id})
            print(f"New user {user_id} added to the database.")
        except Exception as e:
            print(f"Failed to add user {user_id} to database: {e}")

    # 2. Send the welcome message
    welcome_text = (
        "Welcome to swift inr bot! 🎉\n\n"
        "To access the mini app, find the button below on the left, "
        "right beside the message input field."
    )
    bot.reply_to(message, welcome_text)

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
        bot.reply_to(message, "⚠️ Please provide a message to broadcast.\n\nUsage: `/broadcast Your message here`", parse_mode="Markdown")
        return

    # 3. Fetch all users and send the message
    bot.reply_to(message, "⏳ Starting broadcast... This may take a moment depending on the number of users.")
    
    users = users_collection.find()
    success_count = 0
    fail_count = 0

    for user in users:
        target_id = user.get('user_id')
        try:
            bot.send_message(target_id, broadcast_text)
            success_count += 1
        except Exception as e:
            # User might have blocked the bot or deleted their account
            fail_count += 1
            print(f"Failed to send to {target_id}: {e}")

    # 4. Send the final report to the admin
    report = (
        f"✅ **Broadcast Complete!**\n\n"
        f"Delivered successfully: {success_count} users\n"
        f"Failed to deliver: {fail_count} users"
    )
    bot.reply_to(message, report, parse_mode="Markdown")

# Start the bot
if __name__ == '__main__':
    print("Bot is running...")
    # infinity_polling keeps the bot running even if it encounters temporary network errors
    bot.infinity_polling()
