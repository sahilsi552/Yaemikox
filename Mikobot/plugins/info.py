       # <============================================== IMPORTS =========================================================>
import os
import re
from html import escape
from random import choice

from telegram import (
    ChatMemberAdministrator,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatID, ChatType, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, ContextTypes
from telegram.helpers import mention_html

from Database.mongodb.approve_db import is_approved
from Infamous.karma import START_IMG, SUPPORT_CHAT
from Mikobot import DEV_USERS, DRAGONS, INFOPIC, OWNER_ID, function, BOT_NAME, DEMONS, TIGERS, WOLVES
from Mikobot.__main__ import STATS, USER_INFO
from Mikobot.plugins.helper_funcs.chat_status import support_plus
from Mikobot.plugins.users import get_user_id
from Mikobot import BOT_NAME, app
from unidecode import unidecode
from PIL import Image, ImageChops, ImageDraw, ImageFont
from pyrogram import filters
from pyrogram.enums import ParseMode


# <============================================== IMAGE PROCESSING ==================================================>
async def circle(pfp, size=(900, 900)):
    pfp = pfp.resize(size, Image.LANCZOS).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new("L", bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size, Image.LANCZOS)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp


async def download_and_process_pfp(user):
    try:
        pic = await app.download_media(
            user.photo.big_file_id, file_name=f"pp{user.id}.png"
        )
        if pic:
            pfp = Image.open(pic).convert("RGBA")
            return await circle(pfp, size=(900, 900))
    except Exception as e:
        print(e)
    finally:
        if "pic" in locals() and pic:
            os.remove(pic)
    return None


async def userinfopic(
    user,
    user_x,
    user_y,
    user_id_x,
    user_id_y,
    pfp_x_offset=0,
    pfp_y_offset=0,
    pfp_size=(1218, 1385),
):
    user_name = unidecode(user.first_name)

    # Load the background image
    background = Image.open("Extra/user.jpg")
    background = background.resize(
        (background.size[0], background.size[1]), Image.LANCZOS
    )

    draw = ImageDraw.Draw(background)
    font = ImageFont.truetype("Extra/default.ttf", 100)

    try:
        pfp = await download_and_process_pfp(user)
        if pfp:
            # Adjust pfp_x and pfp_y with the offsets
            pfp_x = 927 + pfp_x_offset
            pfp_y = (background.size[1] - pfp.size[1]) // 2 - 290 + pfp_y_offset

            # Increase the size of the pfp circle
            pfp = await circle(pfp, size=pfp_size)
            background.paste(pfp, (pfp_x, pfp_y), pfp)

        # Update text size calculation
        user_name_bbox = draw.textbbox((user_x, user_y), user_name, font=font)
        user_id_bbox = draw.textbbox((user_id_x, user_id_y), str(user.id), font=font)

        draw.text((user_x, user_y), user_name, font=font, fill="white")
        draw.text((user_id_x, user_id_y), str(user.id), font=font, fill="white")

        userinfo = f"downloads/userinfo_{user.id}.png"
        background.save(userinfo)

    except Exception as e:
        print(f"Error: {e}")
        userinfo = None

    return userinfo


# <============================================== COMMAND HANDLERS ==================================================>
@app.on_message(filters.command("uinfo"))
async def userinfo_command(client, message):
    user = message.from_user
    user_x, user_y = 1035, 2885
    user_id_x, user_id_y = 1035, 2755

    try:
        # Send a message indicating that user information is being processed
        processing_message = await message.reply("Processing user information...")

        # Generate user info image
        image_path = await userinfopic(user, user_x, user_y, user_id_x, user_id_y)

        # Delete the processing message
        await processing_message.delete()

        if image_path:
            # Initialize the caption with basic information
            caption = (
                f"「 **According to the Mikos analogy, the userinfo is...** : 」\n\n"
                f"❐  𝗜𝗗: {user.id}\n"
                f"❐  𝗙𝗶𝗿𝘀𝘁 𝗡𝗮𝗺𝗲: {user.first_name}\n"
                f"❐  𝗟𝗮𝘀𝘁 𝗡𝗮𝗺𝗲: {user.last_name}\n"
                f"❐  𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: {user.username}\n"
                f"❐  𝗨𝘀𝗲𝗿𝗹𝗶𝗻𝗸: [link](https://t.me/{user.username})\n"
            )

            # Check if the user's ID matches one of the predefined ranks
            if user.id == OWNER_ID:
                caption += "\n\n〄 The disaster level of this user is **Owner**.\n"
            elif user.id in DEV_USERS:
                caption += "\n\n〄 This user is a member of **Developer**.\n"
            elif user.id in DRAGONS:
                caption += "\n\n〄 The disaster level of this user is **Sudo**.\n"
            elif user.id in DEMONS:
                caption += "\n\n〄 The disaster level of this user is **Demon**.\n"
            elif user.id in TIGERS:
                caption += "\n\n〄 The disaster level of this user is **Tiger**.\n"
            elif user.id in WOLVES:
                caption += "\n\n〄 The disaster level of this user is **Wolf**.\n"

            # Add the RANK line only if the user's ID matches one of the predefined ranks
            if (
                user.id == OWNER_ID
                or user.id in DEV_USERS
                or user.id in DRAGONS
                or user.id in DEMONS
                or user.id in TIGERS
                or user.id in WOLVES
            ):
                caption += "\n\n〄 𝗥𝗮𝗻𝗸: "

                if user.id == OWNER_ID:
                    caption += "**CREATOR**"
                elif user.id in DEV_USERS:
                    caption += "**DEVELOPER**"
                elif user.id in DRAGONS:
                    caption += "**DRAGON**"
                elif user.id in DEMONS:
                    caption += "**DEMON**"
                elif user.id in TIGERS:
                    caption += "**TIGER**"
                elif user.id in WOLVES:
                    caption += "**WOLF**"

                caption += "\n"

            await message.reply_photo(
                photo=image_path, caption=caption, parse_mode=ParseMode.MARKDOWN
            )
            os.remove(image_path)

    except Exception as e:
        print(e)


# <================================================ FUNCTION =======================================================>
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    bot = context.bot

    def reply_with_text(text):
        return message.reply_text(text, parse_mode=ParseMode.HTML)

    head = ""
    premium = False

    reply = await reply_with_text("<code>Getting information...</code>")

    user_id = None
    user_name = None

    if len(args) >= 1:
        if args[0][0] == "@":
            user_name = args[0]
            user_id = await get_user_id(user_name)

        if not user_id:
            try:
                chat_obj = await bot.get_chat(user_name)
                userid = chat_obj.id
            except BadRequest:
                await reply_with_text(
                    "I can't get information about this user/channel/group."
                )
                return
        else:
            userid = user_id
    elif len(args) >= 1 and args[0].lstrip("-").isdigit():
        userid = int(args[0])
    elif message.reply_to_message and not message.reply_to_message.forum_topic_created:
        if message.reply_to_message.sender_chat:
            userid = message.reply_to_message.sender_chat.id
        elif message.reply_to_message.from_user:
            if message.reply_to_message.from_user.id == ChatID.FAKE_CHANNEL:
                userid = message.reply_to_message.chat.id
            else:
                userid = message.reply_to_message.from_user.id
                premium = message.reply_to_message.from_user.is_premium
    elif not message.reply_to_message and not args:
        if message.from_user.id == ChatID.FAKE_CHANNEL:
            userid = message.sender_chat.id
        else:
            userid = message.from_user.id
            premium = message.from_user.is_premium

    try:
        chat_obj = await bot.get_chat(userid)
    except (BadRequest, UnboundLocalError):
        await reply_with_text("I can't get information about this user/channel/group.")
        return

    if chat_obj.type == ChatType.PRIVATE:
        if chat_obj.username:
            head = f"⇨【 <b>USER INFORMATION</b> 】⇦\n\n"
            if chat_obj.username.endswith("bot"):
                head = f"⇨【 <b>BOT INFORMATION</b> 】⇦\n\n"

        head += f"➲ <b>ID:</b> <code>{chat_obj.id}</code>"
        head += f"\n➲ <b>First Name:</b> {chat_obj.first_name}"
        if chat_obj.last_name:
            head += f"\n➲ <b>Last Name:</b> {chat_obj.last_name}"
        if chat_obj.username:
            head += f"\n➲ <b>Username:</b> @{chat_obj.username}"
        head += f"\n➲ <b>Permalink:</b> {mention_html(chat_obj.id, 'link')}"

        if chat_obj.username and not chat_obj.username.endswith("bot"):
            head += f"\n\n💎 <b>Premium User:</b> {premium}"

        if chat_obj.bio:
            head += f"\n\n<b>➲ Bio:</b> {chat_obj.bio}"

        chat_member = await chat.get_member(chat_obj.id)
        if isinstance(chat_member, ChatMemberAdministrator):
            head += f"\n➲ <b>Presence:</b> {chat_member.status}"
            if chat_member.custom_title:
                head += f"\n➲ <b>Admin Title:</b> {chat_member.custom_title}"
        else:
            head += f"\n➲ <b>Presence:</b> {chat_member.status}"

        if is_approved(chat.id, chat_obj.id):
            head += f"\n➲ <b>Approved:</b> This user is approved in this chat."

        disaster_level_present = False

        if chat_obj.id == OWNER_ID:
            head += "\n\n👑 <b>The disaster level of this person is My Owner.</b>"
            disaster_level_present = True
        elif chat_obj.id in DEV_USERS:
            head += "\n\n🐉 <b>This user is a member of Infamous Hydra.</b>"
            disaster_level_present = True
        elif chat_obj.id in DRAGONS:
            head += "\n\n🐲 <b>The disaster level of this person is Dragon.</b>"
            disaster_level_present = True
        if disaster_level_present:
            head += " [?]"

        for mod in USER_INFO:
            try:
                mod_info = mod.__user_info__(chat_obj.id).strip()
            except TypeError:
                mod_info = mod.__user_info__(chat_obj.id, chat.id).strip()

            head += "\n\n" + mod_info if mod_info else ""

    if chat_obj.type == ChatType.SENDER:
        head = f"📨 Sender Chat Information:\n"
        await reply_with_text("Found sender chat, getting information...")
        head += f"<b>ID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"\n🏷️ <b>Title:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"\n📧 <b>Username:</b> @{chat_obj.username}"
        head += f"\n🔗 Permalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"\n📝 <b>Description:</b> {chat_obj.description}"

    elif chat_obj.type == ChatType.CHANNEL:
        head = f"Channel Information:\n"
        await reply_with_text("Found channel, getting information...")
        head += f"<b>ID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"\n<b>Title:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"\n<b>Username:</b> @{chat_obj.username}"
        head += f"\nPermalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"\n<b>Description:</b> {chat_obj.description}"
        if chat_obj.linked_chat_id:
            head += f"\n<b>Linked Chat ID:</b> <code>{chat_obj.linked_chat_id}</code>"

    elif chat_obj.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        head = f"Group Information:\n"
        await reply_with_text("Found group, getting information...")
        head += f"<b>ID:</b> <code>{chat_obj.id}</code>"
        if chat_obj.title:
            head += f"\n<b>Title:</b> {chat_obj.title}"
        if chat_obj.username:
            head += f"\n<b>Username:</b> @{chat_obj.username}"
        head += f"\nPermalink: {mention_html(chat_obj.id, 'link')}"
        if chat_obj.description:
            head += f"\n<b>Description:</b> {chat_obj.description}"

    if INFOPIC:
        try:
            if chat_obj.photo:
                _file = await chat_obj.photo.get_big_file()
                await _file.download_to_drive(f"{chat_obj.id}.png")
                await message.reply_photo(
                    photo=open(f"{chat_obj.id}.png", "rb"),
                    caption=(head),  




async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ID = update.effective_message.from_user.id
    if ID != OWNER_ID:
        return
    stats = f"📊 <b>{BOT_NAME} Bot's Statistics:</b>\n\n" + "\n".join(
        [mod.__stats__() for mod in STATS]
    )
    result = re.sub(r"(\d+)", r"<code>\1</code>", stats)

    keyboard = [
        [
            InlineKeyboardButton(
                "support", url=f"https://t.me/{SUPPORT_CHAT}"
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_photo(
        photo=str(choice(START_IMG)),
        caption=result,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )


# <=================================================== HELP ====================================================>


__help__ = """
*Overall information about user:*
        draw.text((user_id_x, user_id_y), str(user.id), font=font, fill="white")

        userinfo = f"downloads/userinfo_{user.id}.png"
        background.save(userinfo)

    except Exception as e:
        print(f"Error: {e}")
        userinfo = None

    return userinfo


# Command handler for /userinfo
@app.on_message(filters.command("uinfo"))
async def userinfo_command(client, message):
    user = message.from_user
    user_x, user_y = 1035, 2885
    user_id_x, user_id_y = 1035, 2755

    try:
        # Send a message indicating that user information is being processed
        processing_message = await message.reply("Processing user information...")

        # Generate user info image
        image_path = await userinfopic(user, user_x, user_y, user_id_x, user_id_y)

        # Delete the processing message
        await processing_message.delete()

        if image_path:
            # Initialize the caption with basic information
            caption = (
                f"「 **According to the Mikos analogy, the userinfo is...** : 」\n\n"
                f"❐  𝗜𝗗: {user.id}\n"
                f"❐  𝗙𝗶𝗿𝘀𝘁 𝗡𝗮𝗺𝗲: {user.first_name}\n"
                f"❐  𝗟𝗮𝘀𝘁 𝗡𝗮𝗺𝗲: {user.last_name}\n"
                f"❐  𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: {user.username}\n"
                f"❐  𝗨𝘀𝗲𝗿𝗹𝗶𝗻𝗸: [link](https://t.me/{user.username})\n"
            )

            # Check if the user's ID matches one of the predefined ranks
            if user.id == OWNER_ID:
                caption += "\n\n〄 The disaster level of this user is **Owner**.\n"
            elif user.id in DEV_USERS:
                caption += "\n\n〄 This user is a member of **Developer**.\n"
            elif user.id in DRAGONS:
                caption += "\n\n〄 The disaster level of this user is **Sudo**.\n"
            elif user.id in DEMONS:
                caption += "\n\n〄 The disaster level of this user is **Demon**.\n"
            elif user.id in TIGERS:
                caption += "\n\n〄 The disaster level of this user is **Tiger**.\n"
            elif user.id in WOLVES:
                caption += "\n\n〄 The disaster level of this user is **Wolf**.\n"

            # Add the RANK line only if the user's ID matches one of the predefined ranks
            if (
                user.id == OWNER_ID
                or user.id in DEV_USERS
                or user.id in DRAGONS
                or user.id in DEMONS
                or user.id in TIGERS
                or user.id in WOLVES
            ):
                caption += "\n\n〄 𝗥𝗮𝗻𝗸: "

                if user.id == OWNER_ID:
                    caption += "**CREATOR**"
                elif user.id in DEV_USERS:
                    caption += "**DEVELOPER**"
                elif user.id in DRAGONS:
                    caption += "**DRAGON**"
                elif user.id in DEMONS:
                    caption += "**DEMON**"
                elif user.id in TIGERS:
                    caption += "**TIGER**"
                elif user.id in WOLVES:
                    caption += "**WOLF**"

                caption += "\n"

            await message.reply_photo(
                photo=image_path, caption=caption, parse_mode=ParseMode.MARKDOWN
            )
            os.remove(image_path)

    except Exception as e:
        print(e)

# <================================================ FUNCTION =======================================================>
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

        if chat_obj.username:
            head = f"⇨【 <b>USER INFORMATION</b> 】⇦\n\n"
            if chat_obj.username.endswith("bot"):
                head = f"⇨【 <b>BOT INFORMATION</b> 】⇦\n\n"

        head += f"➲ <b>ID:</b> <code>{chat_obj.id}</code>"
        head += f"\n➲ <b>First Name:</b> {chat_obj.first_name}"
        if chat_obj.last_name:
            head += f"\n➲ <b>Last Name:</b> {chat_obj.last_name}"
        if chat_obj.username:
            head += f"\n➲ <b>Username:</b> @{chat_obj.username}"
        head += f"\n➲ <b>Permalink:</b> {mention_html(chat_obj.id, 'link')}"

        if chat_obj.username and not chat_obj.username.endswith("bot"):
            head += f"\n\n💎 <b>Premium User:</b> {premium}"

        if chat_obj.bio:
            head += f"\n\n<b>➲ Bio:</b> {chat_obj.bio}"

        chat_member = await chat.get_member(chat_obj.id)
        if isinstance(chat_member, ChatMemberAdministrator):
            head += f"\n➲ <b>Presence:</b> {chat_member.status}"
            if chat_member.custom_title:
                head += f"\n➲ <b>Admin Title:</b> {chat_member.custom_title}"
        else:
            head += f"\n➲ <b>Presence:</b> {chat_member.status}"

        if is_approved(chat.id, chat_obj.id):
            head += f"\n➲ <b>Approved:</b> This user is approved in this chat."

        )




async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ID = update.effective_message.from_user.id
    if ID != OWNER_ID:
        return
    stats = f"📊 <b>{BOT_NAME} Bot's Statistics:</b>\n\n" + "\n".join(
        [mod.__stats__() for mod in STATS]
    )
    result = re.sub(r"(\d+)", r"<code>\1</code>", stats)

    keyboard = [
        [
            InlineKeyboardButton(
                "support", url=f"https://t.me/{SUPPORT_CHAT}"
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_photo(
        photo=str(choice(START_IMG)),
        caption=result,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )


# <=================================================== HELP ====================================================>


__help__ = """
*Overall information about user:*

» /info : Fetch user information.

» /uinfo : Fetch user information in banner.
"""

# <================================================ HANDLER =======================================================>
STATS_HANDLER = CommandHandler(["stats", "gstats"], stats, block=False)
INFO_HANDLER = CommandHandler(("info", "book"), info, block=False)

function(STATS_HANDLER)
function(INFO_HANDLER)

__mod_name__ = "Iɴꜰᴏ"
__command_list__ = ["info"]
__handlers__ = [INFO_HANDLER, STATS_HANDLER]
# <================================================ END =======================================================>

» /info : Fetch user information.

» /uinfo : Fetch user information in banner.
"""

# <================================================ HANDLER =======================================================>
STATS_HANDLER = CommandHandler(["stats", "gstats"], stats, block=False)
INFO_HANDLER = CommandHandler(("info", "book"), info, block=False)

function(STATS_HANDLER)
function(INFO_HANDLER)

__mod_name__ = "Iɴꜰᴏ"
__command_list__ = ["info"]
__handlers__ = [INFO_HANDLER, STATS_HANDLER]
# <================================================ END =======================================================>
