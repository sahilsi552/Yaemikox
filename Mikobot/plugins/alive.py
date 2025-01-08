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
from Mikobot import BOT_NAME, app, StartTime
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

# <=======================================================================================================>

BINGSEARCH_URL = "https://sugoi-api.vercel.app/search"
NEWS_URL = "https://sugoi-api.vercel.app/news?keyword={}"
# <=======================================================================================================>


# <================================================ FUNCTION =======================================================>
@app.on_message(filters.command("alive"))
async def alive(_, message: Message):
    library_versions = {
        "Pᴛʙ": telegram.__version__,
        "Tᴇʟᴇᴛʜᴏɴ": telethon.__version__,
        "Pʏʀᴏɢʀᴀᴍ": pyrogram.__version__,
    }

    library_versions_text = "\n".join(
        [f"❒ **{key}:** `{value}`" for key, value in library_versions.items()]
    )

    caption = f"""**HEY, I AM {BOT_NAME}**

━━━━ 🌟✿🌟 ━━━━

{library_versions_text}

❒ **PYTHON:** `{version_info[0]}.{version_info[1]}.{version_info[2]}`
━━━━ 🌟✿🌟 ━━━━"""

    await message.reply_photo(
        HEY_IMG,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(ALIVE_BTN),
    )


# <=======================================================================================================>


# <================================================ NAME =======================================================>
__mod_name__ = "ALIVE"
# <================================================ END =======================================================>
# <============================================== IMPORTS =========================================================>


# <=======================================================================================================>


@app.on_message(filters.command("ping"))
async def ping_(client, message):
    try:
        start_time = time.perf_counter()
        response_message = await message.reply_text("Pinging...")
        elapsed_time = time.perf_counter() - start_time
        telegram_ping = f"{elapsed_time * 10:.3f} ms"  # Convert to milliseconds

        uptime = get_readable_time(int(time.time() - StartTime))

        await response_message.edit_text(
            f"<b>PONG</b>\n\n"
            f"<b>Time taken:</b> <code>{telegram_ping}</code>\n"
            f"<b>Uptime:</b> <code>{uptime}</code>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await message.reply_text(f"Error: {e}")

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

