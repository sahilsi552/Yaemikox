# <============================================== IMPORTS =========================================================>
import time

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from Mikobot import StartTime, function
from Mikobot.__main__ import get_readable_time
from Mikobot.plugins.helper_funcs.chat_status import check_admin

# <=======================================================================================================>

@check_admin(only_dev=True)
async def ptb_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    start_time = time.perf_counter()
    message = await msg.reply_text("Pinging...")
    elapsed_time = time.perf_counter() - start_time
    telegram_ping = f"{elapsed_time * 1000:.3f} ms"

    uptime = get_readable_time(int(time.time() - StartTime))

    await message.edit_text(
        f"\U0001F3D3 <b>PONG</b>\n\n"
        f"<b>Time taken:</b> <code>{telegram_ping}</code>\n"
        f"<b>Uptime:</b> <code>{uptime}</code>",
        parse_mode=ParseMode.HTML,
    )
function(CommandHandler("ping", ptb_ping, block=False))
