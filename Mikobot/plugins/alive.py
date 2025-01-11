# SOURCE https://github.com/Team-ProjectCodeX
# CREATED BY https://t.me/O_okarma
# PROVIDED BY https://t.me/ProjectCodeX

# <============================================== IMPORTS =========================================================>
import random
from sys import version_info
import pyrogram
import telegram
import telethon
from pyrogram.types import InlineKeyboardMarkup, Message

from Infamous.karma import HEY_IMG, ALIVE_BTN
from Mikobot import BOT_NAME, app, StartTime ,BOT_USERNAME, DRAGONS
import time

from pyrogram.enums import ParseMode
from Mikobot.utils.human_read import get_readable_time
        
from pyrogram.types import Message
from pyrogram import Client, filters

from Database.mongodb.sangmata_db import (
    add_userdata,
    cek_userdata,
    get_userdata,
    is_sangmata_on,
    sangmata_off,
    sangmata_on,
)
from Mikobot.utils.can_restrict import can_restrict
from Mikobot.utils.custom_filters import PREFIX_HANDLER


import json
import random


from pyrogram.types import InputMediaPhoto, Message

from Mikobot.state import state

from datetime import datetime
from Database.mongodb.karma_mongo import get_couple, save_couple


# <=======================================================================================================>

BINGSEARCH_URL = "https://sugoi-api.vercel.app/search"
NEWS_URL = "https://sugoi-api.vercel.app/news?keyword={}"
# <=======================================================================================================>

from os import remove

from Database.mongodb.toggle_mongo import is_nsfw_on, nsfw_off, nsfw_on
from Mikobot.state import arq
from Mikobot.utils.can_restrict import can_restrict
from Mikobot.utils.errors import capture_err
from Python_ARQ import ARQ
ARQ_API_KEY = "RLWCED-WZASYO-AWOLTB-ITBWTP-ARQ"  # GET API KEY FROM @ARQRobot
ARQ_API_URL = "arq.hamker.dev"
from aiohttp import ClientSession

# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
async def get_file_id_from_message(message):
    file_id = None
    if message.document:
        if int(message.document.file_size) > 3145728:
            return
        mime_type = message.document.mime_type
        if mime_type not in ("image/png", "image/jpeg"):
            return
        file_id = message.document.file_id

    if message.sticker:
        if message.sticker.is_animated:
            if not message.sticker.thumbs:
                return
            file_id = message.sticker.thumbs[0].file_id
        else:
            file_id = message.sticker.file_id

    if message.photo:
        file_id = message.photo.file_id

    if message.animation:
        if not message.animation.thumbs:
            return
        file_id = message.animation.thumbs[0].file_id

    if message.video:
        if not message.video.thumbs:
            return
        file_id = message.video.thumbs[0].file_id
    return file_id


@app.on_message(
    (
        filters.document
        | filters.photo
        | filters.sticker
        | filters.animation
        | filters.video
    )
    & ~filters.private,
    group=8,
)
@capture_err
async def detect_nsfw(_, message):
    if not await is_nsfw_on(message.chat.id):
        return
    if not message.from_user:
        return
    file_id = await get_file_id_from_message(message)
    if not file_id:
        return
    file = await _.download_media(file_id)
    try:
        arq = ARQ(ARQ_API_URL, ARQ_API_KEY,ClientSession())
        results = await arq.nsfw_scan(file=file)
    except Exception:
        return
    if not results.ok:
        return
    results = results.result
    remove(file)
    nsfw = results.is_nsfw
    if message.from_user.id in DRAGONS:
        return
    if not nsfw:
        return
    try:
        await message.delete()
    except Exception:
        return
    await message.reply_text(
        f"""
**🔞 NSFW Image Detected & Deleted Successfully!**

**✪ User:** {message.from_user.mention} [`{message.from_user.id}`]
**✪ Safe:** `{results.neutral} %`
**✪ Porn:** `{results.porn} %`
**✪ Adult:** `{results.sexy} %`
**✪ Hentai:** `{results.hentai} %`
**✪ Drawings:** `{results.drawings} %`
"""
    )


@app.on_message(filters.command(["nsfwscan", f"nsfwscan@{BOT_USERNAME}"]))
@capture_err
async def nsfw_scan_command(_, message):
    if not message.reply_to_message:
        await message.reply_text(
            "Reply to an image/document/sticker/animation to scan it."
        )
        return
    reply = message.reply_to_message
    if (
        not reply.document
        and not reply.photo
        and not reply.sticker
        and not reply.animation
        and not reply.video
    ):
        await message.reply_text(
            "Reply to an image/document/sticker/animation to scan it."
        )
        return
    m = await message.reply_text("Scanning")
    file_id = await get_file_id_from_message(reply)
    if not file_id:
        return await m.edit("Something wrong happened.")
    file = await _.download_media(file_id)
    try:
        arq = ARQ(ARQ_API_URL, ARQ_API_KEY,ClientSession())
        results = await arq.nsfw_scan(file=file)
        print(results)
    except Exception as e:
        print(str(e))
        return await m.edit("Something wrong happened.")
    remove(file)
    if not results.ok:
        return await m.edit(results.result)
    results = results.result
    await m.edit(
        f"""
**➢ Neutral:** `{results.neutral} %`
**➢ Porn:** `{results.porn} %`
**➢ Hentai:** `{results.hentai} %`
**➢ Sexy:** `{results.sexy} %`
**➢ Drawings:** `{results.drawings} %`
**➢ NSFW:** `{results.is_nsfw}`
"""
    )


@app.on_message(
    filters.command(["antinsfw", f"antinsfw@{BOT_USERNAME}"]) & ~filters.private
)
@can_restrict
async def nsfw_enable_disable(_, message):
    if len(message.command) != 2:
        await message.reply_text("Usage: /antinsfw [on/off]")
        return
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status in ("on", "yes"):
        if await is_nsfw_on(chat_id):
            await message.reply_text("Antinsfw is already enabled.")
            return
        await nsfw_on(chat_id)
        await message.reply_text(
            "Enabled AntiNSFW System. I will Delete Messages Containing Inappropriate Content."
        )
    elif status in ("off", "no"):
        if not await is_nsfw_on(chat_id):
            await message.reply_text("Antinsfw is already disabled.")
            return
        await nsfw_off(chat_id)
        await message.reply_text("Disabled AntiNSFW System.")
    else:
        await message.reply_text("Unknown Suffix, Use /antinsfw [on/off]")


# <================================================ FUNCTION =======================================================>


# <=======================================================================================================>


# <================================================ NAME =======================================================>
__mod_name__ = "ALIVE"
# <================================================ END =======================================================>
# <============================================== IMPORTS =========================================================>


# <=======================================================================================================>
# Check user that change first_name, last_name and usernaname
@app.on_message(
    filters.group & ~filters.bot & ~filters.via_bot,
    group=5,
)
async def cek_mataa(_, ctx: Message):
    if ctx.sender_chat or not await is_sangmata_on(ctx.chat.id):
        return
    if not await cek_userdata(ctx.from_user.id):
        return await add_userdata(
            ctx.from_user.id,
            ctx.from_user.username,
            ctx.from_user.first_name,
            ctx.from_user.last_name,
        )
    
    username_before, first_name, last_name_before = await get_userdata(ctx.from_user.id)
    msg = ""
    
    if (
        username_before != ctx.from_user.username
        or first_name != ctx.from_user.first_name
        or last_name_before != ctx.from_user.last_name
    ):
        msg += f"<b>➼ 𝗠𝗜𝗞𝗢 𝗠𝗔𝗧𝗔</b>\n\n🧑‍💼 User: {ctx.from_user.mention} [<code>{ctx.from_user.id}</code>]\n"
    
    if username_before != ctx.from_user.username:
        username_before = f"@{username_before}" if username_before else "<code>No Username</code>"
        username_after = f"@{ctx.from_user.username}" if ctx.from_user.username else "<code>No Username</code>"
        msg += f"✨ Changed username from {username_before} ➡️ {username_after}.\n"
        await add_userdata(
            ctx.from_user.id,
            ctx.from_user.username,
            ctx.from_user.first_name,
            ctx.from_user.last_name,
        )
    
    if first_name != ctx.from_user.first_name:
        msg += f"✨ Changed first name from {first_name} ➡️ {ctx.from_user.first_name}.\n"
        await add_userdata(
            ctx.from_user.id,
            ctx.from_user.username,
            ctx.from_user.first_name,
            ctx.from_user.last_name,
        )
    
    if last_name_before != ctx.from_user.last_name:
        last_name_before = last_name_before or "<code>No Last Name</code>"
        last_name_after = ctx.from_user.last_name or "<code>No Last Name</code>"
        msg += f"✨ Changed last name from {last_name_before} ➡️ {last_name_after}.\n"
        await add_userdata(
            ctx.from_user.id,
            ctx.from_user.username,
            ctx.from_user.first_name,
            ctx.from_user.last_name,
        )
    
    if msg != "":
        await ctx.reply(msg, quote=False)

@app.on_message(
    filters.group
    & filters.command("imposter")
    & ~filters.bot
    & ~filters.via_bot
)
@can_restrict
async def set_mataa(_, ctx: Message):
    if len(ctx.command) == 1:
        return await ctx.reply("Use /{} on, to enable Mikomata. If you want disable, you can use off parameter.".format(ctx.command[0]))
    
    if ctx.command[1] == "on":
        is_enabled = await is_sangmata_on(ctx.chat.id)
        if is_enabled:
            await ctx.reply("Mikomata already enabled in your groups. 😊")
        else:
            await sangmata_on(ctx.chat.id)
            await ctx.reply("Mikomata enabled in your groups. 🎉")
    
    elif ctx.command[1] == "off":
        is_enabled = await is_sangmata_on(ctx.chat.id)
        if not is_enabled:
            await ctx.reply("Mikomata already disabled in your groups. 🙁")
        else:
            await sangmata_off(ctx.chat.id)
            await ctx.reply("Mikomata disabled in your groups. ❌")
    else:
        await ctx.reply("Unknown parameter, use only on/off parameter. ❓")

# <================================================ FUNCTION =======================================================>
@app.on_message(filters.command("news"))
async def news(_, message: Message):
    keyword = (
        message.text.split(" ", 1)[1].strip() if len(message.text.split()) > 1 else ""
    )
    url = NEWS_URL.format(keyword)

    try:
        response = await state.get(url)  # Assuming state is an asynchronous function
        news_data = response.json()

        if "error" in news_data:
            error_message = news_data["error"]
            await message.reply_text(f"Error: {error_message}")
        else:
            if len(news_data) > 0:
                news_item = random.choice(news_data)

                title = news_item["title"]
                excerpt = news_item["excerpt"]
                source = news_item["source"]
                relative_time = news_item["relative_time"]
                news_url = news_item["url"]

                message_text = f"𝗧𝗜𝗧𝗟𝗘: {title}\n𝗦𝗢𝗨𝗥𝗖𝗘: {source}\n𝗧𝗜𝗠𝗘: {relative_time}\n𝗘𝗫𝗖𝗘𝗥𝗣𝗧: {excerpt}\n𝗨𝗥𝗟: {news_url}"
                await message.reply_text(message_text)
            else:
                await message.reply_text("No news found.")

    except Exception as e:  # Replace with specific exception type if possible
        await message.reply_text(f"Error: {str(e)}")


@app.on_message(filters.command("bingsearch"))
async def bing_search(client: Client, message: Message):
    try:
        if len(message.command) == 1:
            await message.reply_text("Please provide a keyword to search.")
            return

        keyword = " ".join(
            message.command[1:]
        )  # Assuming the keyword is passed as arguments
        params = {"keyword": keyword}

        response = await state.get(
            BINGSEARCH_URL, params=params
        )  # Use the state.get method

        if response.status_code == 200:
            results = response.json()
            if not results:
                await message.reply_text("No results found.")
            else:
                message_text = ""
                for result in results[:7]:
                    title = result.get("title", "")
                    link = result.get("link", "")
                    message_text += f"{title}\n{link}\n\n"
                await message.reply_text(message_text.strip())
        else:
            await message.reply_text("Sorry, something went wrong with the search.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")


# Command handler for the '/bingimg' command
@app.on_message(filters.command("bingimg"))
async def bingimg_search(client: Client, message: Message):
    try:
        text = message.text.split(None, 1)[
            1
        ]  # Extract the query from command arguments
    except IndexError:
        return await message.reply_text(
            "Provide me a query to search!"
        )  # Return error if no query is provided

    search_message = await message.reply_text("🔎")  # Display searching message

    # Send request to Bing image search API using state function
    bingimg_url = "https://sugoi-api.vercel.app/bingimg?keyword=" + text
    resp = await state.get(bingimg_url)
    images = json.loads(resp.text)  # Parse the response JSON into a list of image URLs

    media = []
    count = 0
    for img in images:
        if count == 7:
            break

        # Create InputMediaPhoto object for each image URL
        media.append(InputMediaPhoto(media=img))
        count += 1

    # Send the media group as a reply to the user
    await message.reply_media_group(media=media)

    # Delete the searching message and the original command message
    await search_message.delete()
    await message.delete()


# Command handler for the '/googleimg' command
@app.on_message(filters.command("googleimg"))
async def googleimg_search(client: Client, message: Message):
    try:
        text = message.text.split(None, 1)[
            1
        ]  # Extract the query from command arguments
    except IndexError:
        return await message.reply_text(
            "Provide me a query to search!"
        )  # Return error if no query is provided

    search_message = await message.reply_text("💭")  # Display searching message

    # Send request to Google image search API using state function
    googleimg_url = "https://sugoi-api.vercel.app/googleimg?keyword=" + text
    resp = await state.get(googleimg_url)
    images = json.loads(resp.text)  # Parse the response JSON into a list of image URLs

    media = []
    count = 0
    for img in images:
        if count == 7:
            break

        # Create InputMediaPhoto object for each image URL
        media.append(InputMediaPhoto(media=img))
        count += 1

    # Send the media group as a reply to the user
    await message.reply_media_group(media=media)

    # Delete the searching message and the original command message
    await search_message.delete()
    await message.delete()


# <=======================================================================================================>

# List of additional images
ADDITIONAL_IMAGES = [
    "https://telegra.ph/file/7ef6006ed6e452a6fd871.jpg",
    "https://telegra.ph/file/16ede7c046f35e699ed3c.jpg",
    "https://telegra.ph/file/f16b555b2a66853cc594e.jpg",
    "https://telegra.ph/file/7ef6006ed6e452a6fd871.jpg",
]


# <================================================ FUNCTION =======================================================>
def dt():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M")
    dt_list = dt_string.split(" ")
    return dt_list


def dt_tom():
    a = (
        str(int(dt()[0].split("/")[0]) + 1)
        + "/"
        + dt()[0].split("/")[1]
        + "/"
        + dt()[0].split("/")[2]
    )
    return a


tomorrow = str(dt_tom())
today = str(dt()[0])

C = """
•➵💞࿐ 𝐇𝐚𝐩𝐩𝐲 𝐜𝐨𝐮𝐩𝐥𝐞 𝐨𝐟 𝐭𝐡𝐞 𝐝𝐚𝐲
╭──────────────
┊•➢ {} + ( PGM🎀😶 (https://t.me/Chalnayaaaaaarr) + 花火 (https://t.me/zd_sr07) + ゼロツー (https://t.me/wewewe_x) ) = 💞
╰───•➢♡
╭──────────────
┊•➢ 𝗡𝗲𝘄 𝗰𝗼𝘂𝗽𝗹𝗲 𝗼𝗳 𝘁𝗵𝗲 𝗱𝗮𝘆 𝗺𝗮𝘆𝗯𝗲
┊ 𝗰𝗵𝗼𝘀𝗲𝗻 𝗮𝘁 12AM {}
╰───•➢♡
"""
CAP = """
•➵💞࿐ 𝐇𝐚𝐩𝐩𝐲 𝐜𝐨𝐮𝐩𝐥𝐞 𝐨𝐟 𝐭𝐡𝐞 𝐝𝐚𝐲
╭──────────────
┊•➢ {} + {} = 💞
╰───•➢♡
╭──────────────
┊•➢ 𝗡𝗲𝘄 𝗰𝗼𝘂𝗽𝗹𝗲 𝗼𝗳 𝘁𝗵𝗲 𝗱𝗮𝘆 𝗺𝗮𝘆𝗯𝗲
┊ 𝗰𝗵𝗼𝘀𝗲𝗻 𝗮𝘁 12AM {}
╰───•➢♡
"""

CAP2 = """
•➵💞࿐ 𝐇𝐚𝐩𝐩𝐲 𝐜𝐨𝐮𝐩𝐥𝐞 𝐨𝐟 𝐭𝐡𝐞 𝐝𝐚𝐲
╭──────────────
┊{} (tg://openmessage?user_id={}) + {} (tg://openmessage?user_id={}) = 💞\n
╰───•➢♡
╭──────────────
┊•➢ 𝗡𝗲𝘄 𝗰𝗼𝘂𝗽𝗹𝗲 𝗼𝗳 𝘁𝗵𝗲 𝗱𝗮𝘆 𝗺𝗮𝘆𝗯𝗲
┊ 𝗰𝗵𝗼𝘀𝗲𝗻 𝗮𝘁 12AM {}
╰───•➢♡
"""


@app.on_message(filters.command(["couple", "couples", "shipping"]) & ~filters.private)
async def nibba_nibbi(_, message):
    COUPLES_PIC = random.choice(ADDITIONAL_IMAGES)  # Move inside the command function
    try:
        chat_id = message.chat.id
        is_selected = await get_couple(chat_id, today)
        if not is_selected:
            list_of_users = []
            async for i in _.get_chat_members(message.chat.id, limit=50):
                if not i.user.is_bot:
                    list_of_users.append(i.user.id)
            if len(list_of_users) < 2:
                return await message.reply_text("Not enough users in the group.")
            c1_id = random.choice(list_of_users)
            c2_id = random.choice(list_of_users)
            while c1_id == c2_id:
                c1_id = random.choice(list_of_users)
            c1_mention = (await _.get_users(c1_id)).mention
            c2_mention = (await _.get_users(c2_id)).mention
            await _.send_photo(
                message.chat.id,
                photo=COUPLES_PIC,
                caption=CAP.format(c1_mention, c2_mention, tomorrow),
            )

            couple = {"c1_id": c1_id, "c2_id": c2_id}
            await save_couple(chat_id, today, couple)

        elif is_selected:
            c1_id = int(is_selected["c1_id"])
            c2_id = int(is_selected["c2_id"])

            c1_name = (await _.get_users(c1_id)).first_name
            c2_name = (await _.get_users(c2_id)).first_name
            print(c1_id, c2_id, c1_name, c2_name)
            couple_selection_message = f"""•➵💞࿐ 𝐇𝐚𝐩𝐩𝐲 𝐜𝐨𝐮𝐩𝐥𝐞 𝐨𝐟 𝐭𝐡𝐞 𝐝𝐚𝐲
╭──────────────
┊•➢ [{c1_name}](tg://openmessage?user_id={c1_id}) + [{c2_name}](tg://openmessage?user_id={c2_id}) = 💞
╰───•➢♡
╭──────────────
┊•➢ 𝗡𝗲𝘄 𝗰𝗼𝘂𝗽𝗹𝗲 𝗼𝗳 𝘁𝗵𝗲 𝗱𝗮𝘆 𝗺𝗮𝘆𝗯𝗲
┊ 𝗰𝗵𝗼𝘀𝗲𝗻 𝗮𝘁 12AM {tomorrow}
╰───•➢♡"""
            await _.send_photo(
                message.chat.id, photo=COUPLES_PIC, caption=couple_selection_message
            )
    except Exception as e:
        print(e)
        await message.reply_text(str(e))
