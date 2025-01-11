import random
from datetime import datetime
from pytz import timezone
from time import time
from sys import version_info

import pyrogram
import telegram
import telethon
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

from Infamous.karma import HEY_IMG, ALIVE_BTN
from Mikobot import BOT_NAME, app

# Helper function to convert text to small caps
def to_smallcaps(text: str) -> str:
    smallcaps = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘϙʀꜱᴛᴜᴠᴡxʏᴢABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    return text.translate(smallcaps)

@app.on_message(filters.command("alive"))
async def alive(_, message: Message):
    start_time = time()  # Start time for calculating ping
    utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (%H:%M:%S UTC)")  # UTC Date and Time
    ist_time = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S (%H:%M:%S IST)")  # IST Date and Time
    
    # Calculating ping
    ping_time = (time() - start_time) * 1000
    ping_display = f"{ping_time:.2f} ms"

    # Fancy and unified info block
    info_text = f"""
╭━━━ ❖ {to_smallcaps("alive")} ❖ ━━━╮
{to_smallcaps(f'hey, i am {BOT_NAME}')}  
━━━━━━━━━━━━━━━  
❒ 🕒 {to_smallcaps('date (ist)')}: {ist_time}  
❒ 🌍 {to_smallcaps('date (utc)')}: {utc_time}  
❒ 📡 {to_smallcaps('ping')}: {ping_display}  
❒ 🐍 {to_smallcaps('python')}: {version_info[0]}.{version_info[1]}.{version_info[2]}  
❒ 📦 {to_smallcaps('pyrogram')}: {pyrogram.__version__}  
❒ 🤖 {to_smallcaps('telethon')}: {telethon.__version__}  
❒ 🤖 {to_smallcaps('ptb')}: {telegram.__version__}  
━━━━━━━━━━━━━━━  
"""
    
    await message.reply_photo(
        HEY_IMG,
        caption=info_text,
        reply_markup=InlineKeyboardMarkup(ALIVE_BTN),
    )
