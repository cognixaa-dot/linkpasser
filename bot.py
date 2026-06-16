import os
import time
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re
import requests

# Simulated internal tracking for user keys
user_access = {} 
# In-memory session bypass tokens (Valid for 24 hours)
# Format: {user_id: expiration_timestamp}

# --- CONFIGURATION (Loaded from Render Environment Variables later) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
KEY_GENERATOR_URL = os.getenv("KEY_GENERATOR_URL", "https://google.com") 
# ^ Change this to your ShrinkEarn/GPLinks custom alias link later!

# Hardcoded text string for the universal key system
DAILY_SECRET_KEY = "VALID_KEY_2026" 

def is_user_valid(user_id):
    """Check if user has an unexpired 24 hour key session"""
    if user_id in user_access:
        if time.time() < user_access[user_id]:
            return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to the Ultimate Direct Bypasser Bot!**\n\n"
        "Drop any shortener link here, and I will instantly extract the destination link for you without any forced ads or channel joins!\n\n"
        "🔑 **Access System:** To maintain server costs, you need to generate an access key once every 24 hours.\n"
        "Use /getkey to get your link, or paste your key here directly to unlock!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def get_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instructions = (
        "🔗 **Click the link below to get your 24-Hour Key:**\n"
        f"{KEY_GENERATOR_URL}\n\n"
        "Complete the shortener page, copy the text key, and paste it directly into this chat!"
    )
    await update.message.reply_text(instructions, parse_mode="Markdown")

def bypass_link_logic(url):
    """Simplistic fallback bypass handler for presentation"""
    try:
        # Basic protection/resolution pattern
        response = requests.get(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception:
        return "Could not resolve link automatically. Make sure it is a valid URL."

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text.strip()

    # Case A: User is typing the secret key to unlock access
    if user_text == DAILY_SECRET_KEY:
        user_access[user_id] = time.time() + 86400  # 24 Hours in seconds
        await update.message.reply_text("✅ **Key Activated!** You now have unrestricted ad-free bypassing access for the next 24 hours!")
        return

    # Case B: User tries to send a link but isn't authenticated yet
    if not is_user_valid(user_id):
        lockout_msg = (
            "⚠️ **Access Denied!** Your 24-hour key is either missing or expired.\n\n"
            "👉 Type /getkey to instantly generate your free 24-hour token key."
        )
        await update.message.reply_text(lockout_msg, parse_mode="Markdown")
        return

    # Case C: Valid authenticated user sends a link to bypass
    urls = re.findall(r'(https?://[^\s]+)', user_text)
    if not urls:
        await update.message.reply_text("Please send a valid HTTP/HTTPS link to bypass.")
        return

    await update.message.reply_text("🔄 *Bypassing your link... please wait...*", parse_mode="Markdown")
    
    bypassed_url = bypass_link_logic(urls[0])
    await update.message.reply_text(f"💚 **Bypassed Destination Link:**\n\n{bypassed_url}")

def main():
    if not BOT_TOKEN:
        print("Error: No BOT_TOKEN found in environment variables.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getkey", get_key_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    # Run the bot using built-in webhook/polling framework
    print("Bot is running perfectly...")
    application.run_polling()

if __name__ == '__main__':
    main()
