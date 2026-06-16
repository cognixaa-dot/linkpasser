import os
import time
import requests
import telebot
from flask import Flask
from threading import Thread

# 1. Setup Bot Configurations
TOKEN = os.getenv("BOT_TOKEN")
# Make sure your website link includes your custom key at the very end
KEY_URL = os.getenv("KEY_GENERATOR_URL", "https://google.com")
bot = telebot.TeleBot(TOKEN)

# Simple tracking dictionary: { user_id: expiry_timestamp }
user_keys = {}

# 2. Flask Setup to bypass Render's free tier sleep shutdown
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))

# 3. Telegram Bot Handlers
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **Welcome to the Premium Link Bypasser!**\n\n"
        "To get free 24-hour ad-free bypassing access, you need a key.\n"
        "👉 Type `/getkey` to generate your access token!\n\n"
        "Once you have it, simply type:\n`/verify YOUR_KEY`"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['getkey'])
def provide_key_link(message):
    msg = (
        "🔑 **Get Your 24-Hour Pass**\n\n"
        f"Click the link below, complete the captcha step, and copy the final key text:\n\n"
        f"🔗 [CLICK HERE TO GENERATE KEY]({KEY_URL})\n\n"
        "After getting the key, send it here like this:\n`/verify VALIDKEY`"
    )
    bot.reply_to(message, msg, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(commands=['verify'])
def verify_user_key(message):
    try:
        user_input = message.text.split(" ", 1)[1].strip()
    except IndexError:
        bot.reply_to(message, "❌ Please provide the key! Example: `/verify VALIDKEY`")
        return

    # Check if they pasted the correct text matching your shortener's final page setup
    if user_input == "VALIDKEY":
        user_id = message.from_user.id
        # Add exactly 24 hours of uptime access to this user ID
        user_keys[user_id] = time.time() + (24 * 3600)
        bot.reply_to(message, "✅ **Key Verified!** You have full bypassing access for the next 24 hours. Send me your links now!")
    else:
        bot.reply_to(message, "❌ **Invalid Key!** Please get a valid key using the `/getkey` command.")

@bot.message_handler(func=lambda message: True)
def handle_links(message):
    user_id = message.from_user.id
    current_time = time.time()

    # Verify if user has an active 24-hour session
    if user_id not in user_keys or current_time > user_keys[user_id]:
        bot.reply_to(message, "🔒 **Access Expired or Restricted!**\n\nYou need a valid 24-hour access key.\nUse `/getkey` to get one instantly for free.")
        return

    incoming_url = message.text.strip()
    if not incoming_url.startswith(("http://", "https://")):
        bot.reply_to(message, "🤖 Please send a valid link starting with http:// or https://")
        return

    status_msg = bot.reply_to(message, "⚡ *Bypassing your link... Please wait...*", parse_mode="Markdown")
    
    try:
        # Utilizing an open-source public bypass API structure
        api_endpoint = f"https://bypass.pm/api/bypass?url={incoming_url}"
        response = requests.get(api_endpoint, timeout=15)
        data = response.json()

        if data.get("status") == "success" or "destination" in data:
            final_link = data.get("destination") or data.get("bypassed_url")
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"✅ **Bypassed Successfully!**\n\n🔗 **Original Link:** {final_link}",
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text="❌ Could not bypass this link automatically. Make sure it is a supported ad-shortener link!"
            )
    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text="⚠️ An error occurred while processing your request. Please try again later."
        )

# Start webserver and bot polling
if __name__ == "__main__":
    t = Thread(target=run)
    t.start()
    bot.infinity_polling()
