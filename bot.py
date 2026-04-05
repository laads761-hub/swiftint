import telebot
from pymongo import MongoClient
import certifi # Required to fix MongoDB SSL handshake errors

# --- CONFIGURATION ---
# ⚠️ WARNING: Your Bot Token and MongoDB Password are hardcoded here!
# Please rotate/change your passwords and tokens immediately after testing, 
# and use environment variables (e.g., os.environ.get("BOT_TOKEN")) in production.
BOT_TOKEN = "8684244889:AAGRgsOSW-c4XW_hMMSeS7oAjlVVYyuw3dU"
MONGO_URI = "mongodb+srv://laads761_db_user:S5XqkFU1NXgdcsc2@cluster0.iqcvxxk.mongodb.net/?appName=Cluster0"
ADMIN_ID = 8167497030

# Initialize the Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize MongoDB connection
try:
    # Use certifi.where() to explicitly provide the CA certificates for SSL verification
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client['swift_int_bot_db']  # Creates/selects the database
    users_collection = db['users']   # Creates/selects the collection
    
    # Ping the database to force an immediate connection check
    # This prevents the bot from waiting until a user sends a message to crash
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # You might want to exit the script here if the database is critical
    # import sys; sys.exit(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    
    # 1. Save user to MongoDB if they don't already exist
    try:
        if not users_collection.find_one({"user_id": user_id}):
            try:
                users_collection.insert_one({"user_id": user_id})
                print(f"New user {user_id} added to the database.")
            except Exception as e:
                print(f"Failed to add user {user_id} to database: {e}")
    except Exception as e:
        print(f"Database read error during /start: {e}")

    # 2. Send the premium welcome message
    welcome_text = (
        "✨ **Welcome to Swift Inr!** 🚀\n\n"
        "💎 We are absolutely thrilled to have you here.\n\n"
        "🎯 *To access the exclusive mini app*, simply tap the button on the bottom left, "
        "right next to your message input field. Let's get started! 🌟"
    )
    # Added parse_mode="Markdown" so the bold and italic text renders correctly
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

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
    
    try:
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
        
    except Exception as e:
        print(f"Database error during broadcast: {e}")
        bot.reply_to(message, "❌ An error occurred while accessing the database for the broadcast.")

# Start the bot
if __name__ == '__main__':
    print("Bot is running...")
    # infinity_polling keeps the bot running even if it encounters temporary network errors
    bot.infinity_polling()
