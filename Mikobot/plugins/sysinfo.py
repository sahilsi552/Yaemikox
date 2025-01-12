import os
import platform
from datetime import datetime
from pytz import timezone
from time import time
from sys import version_info
import psutil

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message
from Mikobot import BOT_NAME, app
from Infamous.karma import HEY_IMG, ALIVE_BTN  # Replace with your correct imports

# Small caps conversion function
def to_smallcaps(text: str) -> str:
    smallcaps = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘϙʀꜱᴛᴜᴠᴡxʏᴢABCDEFGHIJKLMNOPQRSTUVWXYZ"
    )
    return text.translate(smallcaps)

# Readable time conversion function
def get_readable_time(seconds: int) -> str:
    """Convert seconds to a readable time format."""
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

    # Bot uptime
    bot_uptime = get_readable_time(int(time() - boot))

    # System stats
    cpu_usage = psutil.cpu_percent(interval=0.5)
    mem_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage("/").percent
    cpu_load_avg = os.getloadavg()  # Load averages for 1, 5, and 15 minutes
    load_avg_display = f"{cpu_load_avg[0]:.2f}, {cpu_load_avg[1]:.2f}, {cpu_load_avg[2]:.2f}"

    info_text = f"""
╭━━━ ❖ {to_smallcaps("system info")} ❖ ━━━╮
{to_smallcaps(f'hello, i am {BOT_NAME}')}

━━━━━━━━━━━━━━━
❒ 🕒 {to_smallcaps('date (ist)')}: {ist_time}  
❒ 🌍 {to_smallcaps('date (utc)')}: {utc_time}  
❒ 📡 {to_smallcaps('ping')}: {ping_display}  
❒ ⚙️ {to_smallcaps('cpu usage')}: {cpu_usage}%  
❒ 🧠 {to_smallcaps('memory usage')}: {mem_usage}%  
❒ 💾 {to_smallcaps('disk usage')}: {disk_usage}%  
❒ 🔄 {to_smallcaps('load average')}: {load_avg_display}  
❒ ⏱️ {to_smallcaps('bot uptime')}: {bot_uptime}  
❒ 🐍 {to_smallcaps('python')}: {version_info[0]}.{version_info[1]}.{version_info[2]}  
❒ 📦 {to_smallcaps('pyrogram')}: {pyrogram.__version__}  
━━━━━━━━━━━━━━━
"""
    await message.reply_photo(
        HEY_IMG,
        caption=info_text,
        reply_markup=InlineKeyboardMarkup(ALIVE_BTN),
    )
