import html
import json
import os
from typing import Optional
from telegram import Update, ParseMode
from telegram.ext import CommandHandler
from telegram.helpers import mention_html

from Mikobot import dispatcher
from Mikobot.plugins.helper_funcs.chat_status import dev_plus, sudo_plus
from Mikobot.plugins.helper_funcs.extraction import extract_user
from Mikobot.plugins.log_channel import gloggable

ELEVATED_USERS_FILE = os.path.join(os.getcwd(), "Mikobot/elevated_users.json")

DISASTER_LEVELS = {
    "Dragon": "DRAGONS",
    "Demon": "DEMONS",
    "Wolf": "WOLVES",
    "Tiger": "TIGERS",
}

async def check_user_id(user_id: int) -> Optional[str]:
    if not user_id:
        return "That...is a chat! baka ka omae?"
    return None

async def update_elevated_users(data):
    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

async def add_disaster_level(update: Update, level: str, context) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, context, args)
    user_member = await bot.get_chat(user_id)
    
    reply = await check_user_id(user_id)
    if reply:
        await message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in data.get(DISASTER_LEVELS[level], []):
        await message.reply_text(f"This user is already a {level} Disaster.")
        return ""

    for disaster_level, disaster_users in DISASTER_LEVELS.items():
        if user_id in data.get(disaster_users, []):
            data[disaster_users].remove(user_id)

    data.setdefault(DISASTER_LEVELS[level], []).append(user_id)
    await update_elevated_users(data)

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#{level.upper()}\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    await message.reply_text(
        f"Successfully set Disaster level of {user_member.first_name} to {level}!"
    )
    await message.reply_text(log_message, parse_mode=ParseMode.HTML)

@dev_plus
@gloggable
async def addsudo(update: Update, context) -> str:
    await add_disaster_level(update, "Dragon", context)

@sudo_plus
@gloggable
async def addsupport(update: Update, context) -> str:
    await add_disaster_level(update, "Demon", context)

@sudo_plus
@gloggable
async def addwhitelist(update: Update, context) -> str:
    await add_disaster_level(update, "Wolf", context)

@sudo_plus
@gloggable
async def addtiger(update: Update, context) -> str:
    await add_disaster_level(update, "Tiger", context)

async def remove_disaster_level(update: Update, level: str, context) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, context, args)
    user_member = await bot.get_chat(user_id)
    reply = await check_user_id(user_id)

    if reply:
        await message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id not in data.get(DISASTER_LEVELS[level], []):
        await message.reply_text(f"This user is not a {level} Disaster.")
        return ""

    data[DISASTER_LEVELS[level]].remove(user_id)
    await update_elevated_users(data)

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#REMOVE_{level.upper()}\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    await message.reply_text(
        f"Successfully removed Disaster level '{level}' from {user_member.first_name}!"
    )
    await message.reply_text(log_message, parse_mode=ParseMode.HTML)

@dev_plus
@gloggable
async def rmsudo(update: Update, context) -> str:
    await remove_disaster_level(update, "Dragon", context)

@sudo_plus
@gloggable
async def rmsupport(update: Update, context) -> str:
    await remove_disaster_level(update, "Demon", context)

@sudo_plus
@gloggable
async def rmwhitelist(update: Update, context) -> str:
    await remove_disaster_level(update, "Wolf", context)

@sudo_plus
@gloggable
async def rmtiger(update: Update, context) -> str:
    await remove_disaster_level(update, "Tiger", context)

async def list_disaster_levels(update: Update, context) -> None:
    message = update.effective_message
    
    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    result = []
    for level, key in DISASTER_LEVELS.items():
        user_ids = data.get(key, [])
        if not user_ids:
            result.append(f"🛑 <b>{level} Disasters</b>: None")
        else:
            users = []
            for user_id in user_ids:
                user_info = await context.bot.get_chat(user_id)
                users.append(f"{mention_html(user_info.id, html.escape(user_info.first_name))}")
            result.append(f"🛑 <b>{level} Disasters</b>: " + ", ".join(users))
    
    await message.reply_text("\n\n".join(result), parse_mode=ParseMode.HTML)

# Registering Command Handlers
SUDO_HANDLER = CommandHandler("addsudo", addsudo, block=False)
SUPPORT_HANDLER = CommandHandler(("addsupport", "adddemon"), addsupport, block=False)
TIGER_HANDLER = CommandHandler("addtiger", addtiger, block=False)
WHITELIST_HANDLER = CommandHandler(("addwhitelist", "addwolf"), addwhitelist, block=False)
RMSUDO_HANDLER = CommandHandler("rmsudo", rmsudo, block=False)
RMSUPPORT_HANDLER = CommandHandler(("rmsupport", "rmdemon"), rmsupport, block=False)
RMTIGER_HANDLER = CommandHandler("rmtiger", rmtiger, block=False)
RMWHITELIST_HANDLER = CommandHandler(("rmwhitelist", "rmwolf"), rmwhitelist, block=False)
LIST_HANDLER = CommandHandler("disasterlist", list_disaster_levels, block=False)

dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(TIGER_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(RMSUDO_HANDLER)
dispatcher.add_handler(RMSUPPORT_HANDLER)
dispatcher.add_handler(RMTIGER_HANDLER)
dispatcher.add_handler(RMWHITELIST_HANDLER)
dispatcher.add_handler(LIST_HANDLER)

__mod_name__ = "ᴅᴇᴠꜱ"
__handlers__ = [
    SUDO_HANDLER,
    SUPPORT_HANDLER,
    TIGER_HANDLER,
    WHITELIST_HANDLER,
    RMSUDO_HANDLER,
    RMSUPPORT_HANDLER,
    RMTIGER_HANDLER,
    RMWHITELIST_HANDLER,
    LIST_HANDLER,
]
