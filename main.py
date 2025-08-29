import os
import threading
import asyncio
from pyrogram import Client, filters
from pyromod import listen
from careerwill import careerdl
from config import BOT_TEXT, CHANNEL_ID, CHANNEL_ID2, THUMB_URL

# --- Telegram Bot ---
bot = Client(
    "CW",
    bot_token=os.environ.get("BOT_TOKEN"),
    api_id=int(os.environ.get("22470912")),
    api_hash=os.environ.get("511be78079ed5d4bd4c967bc7b5ee023")
)

# --- /start Command ---
@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    await message.reply_text(
        f"{BOT_TEXT}\n\nPress **/cw** to start extracting courses."
    )

# --- /cw Command ---
@bot.on_message(filters.command("cw") & filters.private)
async def cw_handler(client, message):
    try:
        input1 = await bot.ask(message.chat.id, "🔑 Send ID*Password or Token:")
        login_input = input1.text.strip()
        if "*" in login_input:
            email, password = login_input.split("*")
            # Login and get token
            token = "YOUR_LOGIN_LOGIC_HERE"  # replace with actual login logic
        else:
            token = login_input

        input2 = await bot.ask(message.chat.id, "📚 Send Batch ID:")
        batch_id = input2.text.strip()

        input3 = await bot.ask(message.chat.id, "📝 Send topic IDs (1&2&3):")
        topic_ids = input3.text.strip()

        prog = await message.reply("🔄 Processing... Please wait")

        # Run extractor
        threading.Thread(
            target=lambda: asyncio.run(
                careerdl(bot, message, headers=None, batch_id=batch_id,
                         token=token, topic_ids=topic_ids, prog=prog, batch_name=batch_id)
            )
        ).start()

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# --- Run Bot ---
if __name__ == "__main__":
    bot.run()
            
