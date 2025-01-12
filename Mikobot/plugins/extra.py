from time import gmtime, strftime, time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from Mikobot import LOGGER, app
from Mikobot.plugins.helper_funcs.chat_status import check_admin

# Uptime to check how long the bot has been running
UPTIME = time()


# ID Command
@app.on_message(filters.command("id"))
async def id_command(client: Client, message: Message):
    chat = message.chat
    your_id = message.from_user.id
    mention_user = message.from_user.mention
    message_id = message.id
    reply = message.reply_to_message

    text = f"**๏ [ᴍᴇssᴀɢᴇ ɪᴅ]({message.link})** » `{message_id}`\n"
    text += f"**๏ [{mention_user}](tg://user?id={your_id})** » `{your_id}`\n"

    if len(message.command) > 1:
        try:
            split = message.text.split(None, 1)[1].strip()
            user = await client.get_users(split)
            text += f"**๏ [{user.mention}](tg://user?id={user.id})** » `{user.id}`\n"
        except Exception:
            return await message.reply_text("**🪄 ᴛʜɪs ᴜsᴇʀ ᴅᴏᴇsɴ'ᴛ ᴇxɪsᴛ.**")

    text += f"**๏ [ᴄʜᴀᴛ ɪᴅ](https://t.me/{chat.username})** » `{chat.id}`\n\n"

    if reply:
        if reply.from_user:
            text += f"**๏ [ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ɪᴅ]({reply.link})** » `{reply.id}`\n"
            text += f"**๏ [ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ ɪᴅ](tg://user?id={reply.from_user.id})** » `{reply.from_user.id}`\n\n"
        if reply.forward_from_chat:
            text += f"๏ ᴛʜᴇ ғᴏʀᴡᴀʀᴅᴇᴅ ᴄʜᴀɴɴᴇʟ, {reply.forward_from_chat.title}, ʜᴀs ᴀɴ ɪᴅ ᴏғ `{reply.forward_from_chat.id}`\n\n"
        if reply.sender_chat:
            text += f"๏ ID ᴏғ ᴛʜᴇ ʀᴇᴘʟɪᴇᴅ ᴄʜᴀᴛ/ᴄʜᴀɴɴᴇʟ, ɪs `{reply.sender_chat.id}`"

    sticker_id = "CAACAgIAAx0EdppwYAABAgotZg5rBL4P05Xjmy80p7DdNdneDmUAAnccAALIWZhJPyYLf3FzPHs0BA"
    await message.reply_sticker(sticker=sticker_id)
    await message.reply_text(text, disable_web_page_preview=True)


# Logs Command
@app.on_message(filters.command("logs"))
async def logs_command(client: Client, message: Message):
    with open("Logs.txt", "rb") as f:
        caption = "Here is your log"
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close")]]
        )
        sent_message = await client.send_document(
            chat_id=message.chat.id,
            document=f,
            caption=caption,
            reply_markup=reply_markup,
        )
        app.user_data[message.chat.id] = sent_message.id


@app.on_callback_query(filters.regex("^close$"))
async def close_callback(client: Client, callback_query):
    message_id = app.user_data.get(callback_query.message.chat.id)
    if message_id:
        await callback_query.message.delete()


# PyroPing Command
@app.on_message(filters.command("pyroping"))
async def ping(client: Client, message: Message):
    # LOGGER.info(f"{message.from_user.id} used ping cmd in {message.chat.id}")
    start = time()
    replymsg = await message.reply_text(text="Pinging...", quote=True)
    delta_ping = time() - start

    up = strftime("%Hh %Mm %Ss", gmtime(time() - UPTIME))
    image_url = "https://telegra.ph/file/e1049f371bbec3f006f3a.jpg"

    await client.send_photo(
        chat_id=message.chat.id,
        photo=image_url,
        caption=f"<b>Pyro-Pong!</b>\n{delta_ping * 1000:.3f} ms\n\nUptime: <code>{up}</code>",
    )
    await replymsg.delete()


# Help Text
__help__ = """
❒ *Commands*:

〄 /instadl, /insta <link>: Get Instagram contents like reel video or images.

〄 /pyroping: See bot ping.

〄 /hyperlink <text> <link>: Creates a markdown hyperlink with the provided text and link.

〄 /pickwinner <participant1> <participant2> ...: Picks a random winner from the provided list of participants.

〄 /id: Reply to get user id.
"""

__mod_name__ = "Exᴛʀᴀ"
