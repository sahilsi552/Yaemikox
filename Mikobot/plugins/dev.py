import os
import subprocess
import sys
from contextlib import suppress
from time import sleep

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import Unauthorized, TelegramError

import Mikobot
from Mikobot.modules.helper_funcs.chat_status import dev_plus

# Assuming MukeshRobot.ALLOW_CHATS is a boolean flag in the MukeshRobot module.
@dev_plus
async def allow_groups(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        await update.effective_message.reply_text(f"Current state: {Mikobot.ALLOW_CHATS}")
        return
    if args[0].lower() in ["off", "no"]:
        MukeshRobot.ALLOW_CHATS = True
    elif args[0].lower() in ["yes", "on"]:
        MukeshRobot.ALLOW_CHATS = False
    else:
        await update.effective_message.reply_text("Format: /lockdown Yes/No or Off/On")
        return
    await update.effective_message.reply_text("Done! Lockdown value toggled.")

@dev_plus
async def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        try:
            await bot.leave_chat(int(chat_id))
        except TelegramError:
            await update.effective_message.reply_text(
                "Beep boop, I could not leave that group(dunno why tho)."
            )
            return
        with suppress(Unauthorized):
            await update.effective_message.reply_text("Beep boop, I left that soup!.")
    else:
        await update.effective_message.reply_text("Send a valid chat ID")

@dev_plus
async def gitpull(update: Update, context: CallbackContext):
    sent_msg = await update.effective_message.reply_text(
        "Pulling all changes from remote and then attempting to restart."
    )
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\nChanges pulled...I guess.. Restarting in "

    for i in reversed(range(5)):
        await sent_msg.edit_text(sent_msg_text + str(i + 1))
        sleep(1)

    await sent_msg.edit_text("Restarted.")

    os.system("restart.bat")
    os.execv("start.bat", sys.argv)

@dev_plus
async def restart(update: Update, context: CallbackContext):
    await update.effective_message.reply_text(
        "Starting a new instance and shutting down this one"
    )

    os.system("restart.bat")
    os.execv("start.bat", sys.argv)

def main():
    # Initialize Application
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Handlers
    ALLOWGROUPS_HANDLER = CommandHandler("lockdown", allow_groups)
    LEAVE_HANDLER = CommandHandler("leave", leave)
    GITPULL_HANDLER = CommandHandler("gitpull", gitpull)
    RESTART_HANDLER = CommandHandler("reboot", restart)

    # Add Handlers to the Application
    application.add_handler(ALLOWGROUPS_HANDLER)
    application.add_handler(LEAVE_HANDLER)
    application.add_handler(GITPULL_HANDLER)
    application.add_handler(RESTART_HANDLER)

    # Start polling
  
