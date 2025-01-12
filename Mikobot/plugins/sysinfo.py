import os
import platform
from datetime import datetime
from pytz import timezone
from time import time
from sys import version_info
import psutil
import pyrogram  # Import Pyrogram to access its version

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message
from Mikobot import BOT_NAME, app
from Infamous.karma import HEY_IMG, ALIVE_BTN  # Replace with your correct imports

boot = time()  # Tracks the bot's start time

def to_smallcaps(text: str) -> str:
    smallcaps = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘϙʀꜱᴛᴜᴠᴡxʏᴢABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    return text.translate(smallcaps)

def get_readable_time(seconds: int) -> str:
    count_min, count_sec = divmod(seconds, 60)
    count_hour, count_min = divmod(count_min, 60)
    count_day, count_hour = divmod(count_hour, 24)
    time_string = (
        (f"{count_day}d " if count_day else "") +
        (f"{count_hour}h " if count_hour else "") +
        (f"{count_min}m " if count_min else "") +
        (f"{count_sec}s" if count_sec else "")
    )
    return time_string.strip()

@app.on_message(filters.command("sysinfo"))
async def sysinfo(_, message: Message):
    start_time = time()
    utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (%H:%M:%S UTC)")
    ist_time = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S (%H:%M:%S IST)")
    ping_time = (time() - start_time) * 1000
    ping_display = f"{ping_time:.2f} ms"

    bot_uptime = get_readable_time(int(time() - boot))
    cpu_usage = psutil.cpu_percent(interval=0.5)
    mem
