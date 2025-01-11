import time
from datetime import datetime, timezone, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from Mikobot import StartTime, function
from Mikobot.plugins.helper_funcs.chat_status import check_admin

# <============================================== Fancy Fonts & Small Caps ========================================>
def fancy_number_format(value):
    """Returns digits in fancy Unicode format."""
    fancy_digits = {'0': '𝟘', '1': '𝟙', '2': '𝟚', '3': '𝟛', '4': '𝟜', 
                    '5': '𝟝', '6': '𝟞', '7': '𝟟', '8': '𝟠', '9': '𝟡'}
    return ''.join(fancy_digits.get(char, char) for char in str(value))

def small_caps(text):
    """Converts regular text to small caps."""
    small_caps_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
    }
    return ''.join(small_caps_map.get(char, char) for char in text.lower())

def format_datetime():
    """Returns current UTC and IST date-time as strings."""
    utc_now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    ist_now = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S IST')
    return utc_now, ist_now

def get_readable_time(seconds: int) -> str:
    """Convert seconds into a human-readable string."""
    periods = [
        ('day', 86400),  # 60 * 60 * 24
        ('hour', 3600),  # 60 * 60
        ('minute', 60),
        ('second', 1),
    ]
    result = []
    for name, count in periods:
        value = seconds // count
        if value:
            seconds %= count
            result.append(f"{value} {name}{'s' if value > 1 else ''}")
    return ', '.join(result) if result else '0 seconds'

# <============================================== Ping Command with Refresh Button for All ======================================>
async def ptb_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    # Initializing start time
    start_time = time.perf_counter()

    # Sending an initial message
    message = await msg.reply_text("🏓 Pinging...")

    # Add a small delay to simulate a more realistic ping calculation
    await message.edit_text("🏓 Pinging...\nPlease wait...")
    time.sleep(0.05)  # Small delay (50ms)

    # Measure the time it takes to send and receive the message
    elapsed_time = time.perf_counter() - start_time
    ping_ms = elapsed_time * 1000  # Convert to ms

    uptime = get_readable_time(int(time.time() - StartTime))
    utc_now, ist_now = format_datetime()

    # Add refresh button
    refresh_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_ping")]
    ])

    await message.edit_text(
        f"🏓 <b>{small_caps('pong')}</b>\n\n"
        f"⏱ <b>{small_caps('ping time')}:</b> <code>{fancy_number_format(f'{elapsed_time:.3f}')} s</code>\n"
        f"🕒 <b>{small_caps('ping in ms')}:</b> <code>{fancy_number_format(f'{ping_ms:.1f}')} ms</code>\n"
        f"⏳ <b>{small_caps('uptime')}:</b> <code>{uptime}</code>\n\n"
        f"🗓 <b>{small_caps('date/time (utc)')}:</b> <code>{utc_now}</code>\n"
        f"🗓 <b>{small_caps('date/time (ist)')}:</b> <code>{ist_now}</code>",
        reply_markup=refresh_button,
        parse_mode=ParseMode.HTML,
    )

# Refresh the ping when button clicked
async def refresh_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Recalculate the ping on refresh
    start_time = time.perf_counter()

    # Add a small delay to simulate a more realistic ping calculation
    time.sleep(0.05)  # Small delay (50ms)

    elapsed_time = time.perf_counter() - start_time
    ping_ms = elapsed_time * 1000  # Convert to ms

    uptime = get_readable_time(int(time.time() - StartTime))
    utc_now, ist_now = format_datetime()

    await query.edit_message_text(
        f"🏓 <b>{small_caps('pong')}</b>\n\n"
        f"⏱ <b>{small_caps('ping time')}:</b> <code>{fancy_number_format(f'{elapsed_time:.3f}')} s</code>\n"
        f"🕒 <b>{small_caps('ping in ms')}:</b> <code>{fancy_number_format(f'{ping_ms:.1f}')} ms</code>\n"
        f"⏳ <b>{small_caps('uptime')}:</b> <code>{uptime}</code>\n\n"
        f"🗓 <b>{small_caps('date/time (utc)')}:</b> <code>{utc_now}</code>\n"
        f"🗓 <b>{small_caps('date/time (ist)')}:</b> <code>{ist_now}</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=query.message.reply_markup,
    )

# Add the handlers for /ping and the refresh button
function(CommandHandler("ping", ptb_ping, block=False))
function(CallbackQueryHandler(refresh_ping, pattern="refresh_ping"))
