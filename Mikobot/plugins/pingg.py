from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

# <============================================== Ping Command with Refresh Button for All ======================================>
async def ptb_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    start_time = time.perf_counter()
    message = await msg.reply_text("🏓 Pinging...")
    elapsed_time = time.perf_counter() - start_time

    uptime = get_readable_time(int(time.time() - StartTime))
    utc_now, ist_now = format_datetime()

    refresh_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_ping")]
    ])

    await message.edit_text(
        f"🏓 <b>{small_caps('pong')}</b>\n\n"
        f"⏱ <b>{small_caps('ping time')}:</b> <code>{fancy_number_format(f'{elapsed_time:.3f}')} s</code>\n"
        f"🕒 <b>{small_caps('ping in ms')}:</b> <code>{fancy_number_format(f'{elapsed_time * 1000:.1f}')} ms</code>\n"
        f"⏳ <b>{small_caps('uptime')}:</b> <code>{uptime}</code>\n\n"
        f"🗓 <b>{small_caps('date/time (utc)')}:</b> <code>{utc_now}</code>\n"
        f"🗓 <b>{small_caps('date/time (ist)')}:</b> <code>{ist_now}</code>",
        reply_markup=refresh_button,
        parse_mode=ParseMode.HTML,
    )

async def refresh_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    start_time = time.perf_counter()
    elapsed_time = time.perf_counter() - start_time

    uptime = get_readable_time(int(time.time() - StartTime))
    utc_now, ist_now = format_datetime()

    await query.edit_message_text(
        f"🏓 <b>{small_caps('pong')}</b>\n\n"
        f"⏱ <b>{small_caps('ping time')}:</b> <code>{fancy_number_format(f'{elapsed_time:.3f}')} s</code>\n"
        f"🕒 <b>{small_caps('ping in ms')}:</b> <code>{fancy_number_format(f'{elapsed_time * 1000:.1f}')} ms</code>\n"
        f"⏳ <b>{small_caps('uptime')}:</b> <code>{uptime}</code>\n\n"
        f"🗓 <b>{small_caps('date/time (utc)')}:</b> <code>{utc_now}</code>\n"
        f"🗓 <b>{small_caps('date/time (ist)')}:</b> <code>{ist_now}</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=query.message.reply_markup,
    )

# Add the handlers for /ping and the refresh button
function(CommandHandler("ping", ptb_ping, block=False))
function(CallbackQueryHandler(refresh_ping, pattern="refresh_ping"))
