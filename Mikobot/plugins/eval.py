import io
import os
import sys
import time
import requests as req
import pyrogram

from pyrogram import filters, enums, errors
from Mikobot import LOGGER, dispatcher, pgram as pbot, OWNER_ID
from Mikobot import telethn as client, DEV_USERS
from Mikobot.modules.helper_funcs.chat_status import dev_plus
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ApplicationBuilder, CommandHandler
from contextlib import redirect_stdout
import textwrap
import traceback

namespaces = {}

thumb = "./VegetaRobot/resources/IMG_20211227_141907_345.jpg"

async def pyroaexec(code, pbot, message, my, m, r, ru):
    exec(
        "async def __pyroaexec(pbot, message, my, m, r, ru): "
        + "".join(f"\n {l_}" for l_ in code.split("\n"))
    )
    return await locals()["__pyroaexec"](pbot, message, my, m, r, ru)

def cleanup_code(code):
    if code.startswith('```') and code.endswith('```'):
        return '\n'.join(code.split('\n')[1:-1])
    return code.strip('` \n')

async def send(bot, chat_id, msg, reply_to_message_id=None):
    if len(str(msg)) > 2000:
        with io.BytesIO(str.encode(msg)) as out_file:
            out_file.name = "output.txt"
            await bot.send_document(
                chat_id=chat_id,
                document=out_file,
                caption="Output too long",
            )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_to_message_id=reply_to_message_id,
        )

@pbot.on_message(filters.command('peval') & filters.user(DEV_USERS))
async def pyroevaluate(pbot, message):
    status_message = await message.reply("`Running Code...`")
    try:
        cmd = message.text.split(maxsplit=1)[1]
    except IndexError:
        await status_message.delete()
        return
    start_time = time.time()

    r = message.reply_to_message
    m = message
    my = getattr(message, 'from_user', None)
    ru = getattr(r, 'from_user', None)

    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    try:
        await pyroaexec(code=cmd, message=message, my=my, m=message, r=r, ru=ru, pbot=pbot)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    evaluation = exc or stderr or stdout or "Success"
    taken_time = round(time.time() - start_time, 3)
    output = evaluation.strip()

    format_text = (
        "<pre>Command:</pre><pre language='python'>{}</pre>\n"
        "<pre>Time Taken: {}'s</pre><pre language='python'>{}</pre>"
    )
    final_output = format_text.format(cmd, taken_time, output)

    if len(final_output) > 4096:
        filename = "output.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(str(final_output))
        await message.reply_document(document=filename, caption=f"`{cmd}`")
        os.remove(filename)
    else:
        await status_message.edit(final_output, parse_mode=enums.ParseMode.HTML)

async def evaluate(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    content = "".join(update.message.text.split(maxsplit=1)[1:])
    body = cleanup_code(content)
    env = {'bot': context.bot, **globals()}

    stdout = io.StringIO()
    to_compile = f'def func():\n{textwrap.indent(body, "  ")}'

    try:
        exec(to_compile, env)
    except Exception as e:
        result = f'{e.__class__.__name__}: {e}'
    else:
        func = env['func']
        try:
            with redirect_stdout(stdout):
                func_return = func()
        except Exception as e:
            result = f'{stdout.getvalue()}{traceback.format_exc()}'
        else:
            result = stdout.getvalue() or func_return or repr(eval(body, env))
    await send(context.bot, chat_id, result, reply_to_message_id=update.message.message_id)

async def execute(update: Update, context: CallbackContext):
    await evaluate(update, context)

async def clear(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in namespaces:
        del namespaces[chat_id]
    await send(context.bot, chat_id, "Cleared locals.", reply_to_message_id=update.message.message_id)

dispatcher.add_handler(CommandHandler(["e", "ev", "eva", "eval"], evaluate))
dispatcher.add_handler(CommandHandler(["x", "ex", "exe", "exec", "py"], execute))
dispatcher.add_handler(CommandHandler("clearlocals", clear))
