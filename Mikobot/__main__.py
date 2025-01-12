
import asyncio
import contextlib
import importlib
import json
import re
import time
import traceback
from platform import python_version
from random import choice

import psutil
import pyrogram
import telegram
import telethon
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import (
    BadRequest,
    ChatMigrated,
    Forbidden,
    NetworkError,
    TelegramError,
    TimedOut,
)
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown


from Mikobot import (
    BOT_NAME,
    BOT_USERNAME,
    LOGGER,
    OWNER_ID,
    SUPPORT_CHAT,
    TOKEN,
    StartTime,
    app,
    dispatcher,
    function,
    loop,
    tbot,
)
from Mikobot.plugins import ALL_MODULES
from Mikobot.plugins.helper_funcs.chat_status import is_user_admin
from Mikobot.plugins.helper_funcs.misc import paginate_modules
from Infamous.karma import START_IMG,GROUP_START_BTN
from Mikobot.plugins.rules import send_rules
# <=======================================================================================================>

PYTHON_VERSION = python_version()
PTB_VERSION = telegram.__version__
PYROGRAM_VERSION = pyrogram.__version__
TELETHON_VERSION = telethon.__version__


# <============================================== FUNCTIONS =========================================================>
def get_readable_time(seconds: int) -> str:
    if seconds < 0:
        raise ValueError("Time in seconds must be non-negative.")

    # Time units and their divisors
    time_units = [(60, "s"), (60, "m"), (24, "h"), (None, "days")]
    time_list = []

    for divisor, suffix in time_units:
        if divisor:
            seconds, value = divmod(seconds, divisor)
        else:
            value = seconds  # Remaining seconds represent days

        if value > 0 or time_list:  # Avoid leading zeros
            time_list.append(f"{value}{suffix}")

        if seconds == 0:
            break

    # Reverse the time_list for natural ordering and join elements
    ping_time = ", ".join(time_list[::-1])
    return ping_time


IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

PM_START_TEXT = """ 
Hello {}🥀.

๏ This is {}🖤!
➻ The most comprehensive Telegram bot for managing and protecting group chats from spammers and rule-breakers.

──────────────────
๏ Click the help button to learn about my modules and commands.

bot_uptime = int(time.time() - boot)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    UP = get_readable_time((bot_uptime))
    CPU = f"{cpu}%"
    RAM = f"{mem}%"
    DISK = f"{disk}%"
"""
def private_panel():
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕",
                url=f"https://t.me/{BOT_USERNAME}?startgroup=s&admin=delete_messages+manage_video_chats+pin_messages+invite_users",
            )
        ],
        [
            InlineKeyboardButton(text="📚 ʜᴇʟᴘ",callback_data="extra_command_handler"),
        ],
        [
              InlineKeyboardButton(text="ꜱᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{SUPPORT_CHAT}"),
            InlineKeyboardButton(text="ᴜᴘᴅᴀᴛᴇꜱ", url=f"https://t.me/{SUPPORT_CHAT}"),
        ],
    ]
    return buttons

HELP_STRINGS = f"""
» *{BOT_NAME} ๏ Click on the help button to get information about my modules and commands.
➻ You can also use the buttons below to get started*"""

DONATE_STRING = """ʜᴇʏ ʙᴀʙʏ,
  ʜᴀᴩᴩʏ ᴛᴏ ʜᴇᴀʀ ᴛʜᴀᴛ ʏᴏᴜ ᴡᴀɴɴᴀ ᴅᴏɴᴀᴛᴇ.

ʏᴏᴜ ᴄᴀɴ ᴅɪʀᴇᴄᴛʟʏ ᴄᴏɴᴛᴀᴄᴛ ᴍʏ ᴅᴇᴠᴇʟᴏᴘᴇʀ @sahil30 ғᴏʀ ᴅᴏɴᴀᴛɪɴɢ just type ``` /pay 30 ```."""
for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Mikobot.plugins." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
async def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    await dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    message = update.effective_message
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                
                await send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower()=="mainhelp":
                await update.effective_message.reply_text(
    "𝙎𝙚𝙡𝙚𝙘𝙩 𝙩𝙝𝙚 𝙨𝙚𝙘𝙩𝙞𝙤𝙣 𝙩𝙝𝙖𝙩 𝙮𝙤𝙪 𝙬𝙖𝙣𝙩 𝙩𝙤 𝙤𝙥𝙚𝙣",
    reply_markup=InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ᴍᴀɴᴀɢᴇᴍᴇɴᴛ", callback_data="help_back"),
                InlineKeyboardButton("ᴍᴜꜱɪᴄ", callback_data="Music_"),
            ],
            [
                InlineKeyboardButton("ʙᴀꜱɪᴄ", callback_data="basic_command"),
                InlineKeyboardButton("ᴀᴅᴠᴀɴᴄᴇ", callback_data="advanced_command"),
            ],
            [
                InlineKeyboardButton("ᴇxᴘᴇʀᴛ", callback_data="expert_command"),
                InlineKeyboardButton("ʜᴏᴍᴇ", callback_data="Miko_back"),
            ],
        ]
    )
)

            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                await send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="◁", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower() == "markdownhelp":
                IMPORTED["exᴛʀᴀs"].markdown_help_sender(update)
            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)
                    
            elif args[0].lower().startwith("rules_"):
                chat_id = args[0].split("_", 1)[1]
                await send_rules(update, chat_id)
                

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                await IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            start=private_panel()
            await update.effective_message.reply_text(
                PM_START_TEXT.format(escape_markdown(first_name),BOT_NAME),
                reply_markup=InlineKeyboardMarkup(start),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False,
            )
    else:
        await message.reply_photo(
            photo=str(choice(START_IMG)),
            reply_markup=InlineKeyboardMarkup(GROUP_START_BTN),
            caption="<b>I am Alive!</b>\n\n<b>Since​:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )


async def extra_command_handlered(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
       [
                        InlineKeyboardButton("ᴍᴀɴᴀɢᴇᴍᴇɴᴛ", callback_data="help_back"),
                        InlineKeyboardButton("ᴍᴜꜱɪᴄ", callback_data="Music_"),
                    ],
                    [
                        InlineKeyboardButton("ʙᴀꜱɪᴄ", callback_data="basic_command"),
                        InlineKeyboardButton("ᴀᴅᴠᴀɴᴄᴇ", callback_data="advanced_command"),
                    ],
                    [
                        InlineKeyboardButton("ᴇxᴘᴇʀᴛ",callback_data="expert_command"),
                       
                        InlineKeyboardButton("ʜᴏᴍᴇ", callback_data="Miko_back"),
                    ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.effective_chat.type == "private":
        await update.message.reply_text(
        "𝙎𝙚𝙡𝙚𝙘𝙩 𝙩𝙝𝙚 𝙨𝙚𝙘𝙩𝙞𝙤𝙣 𝙩𝙝𝙖𝙩 𝙮𝙤𝙪 𝙬𝙖𝙣𝙩 𝙩𝙤 𝙤𝙥𝙚𝙣",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    else:
        await update.message.reply_text("Contact me in PM for help!",reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Click me for help",url=f"https://t.me/{BOT_USERNAME}?start=mainhelp")
            ]
            ]
        ))


async def extra_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "extra_command_handler":
        await query.answer()  # Use 'await' for asynchronous calls
        await query.message.edit_text(
            "𝙎𝙚𝙡𝙚𝙘𝙩 𝙩𝙝𝙚 𝙨𝙚𝙘𝙩𝙞𝙤𝙣 𝙩𝙝𝙖𝙩 𝙮𝙤𝙪 𝙬𝙖𝙣𝙩 𝙩𝙤 𝙤𝙥𝙚𝙣",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("ᴍᴀɴᴀɢᴇᴍᴇɴᴛ", callback_data="help_back"),
                        InlineKeyboardButton("ᴍᴜꜱɪᴄ", callback_data="Music_"),
                    ],
                    [
                        InlineKeyboardButton("ʙᴀꜱɪᴄ", callback_data="basic_command"),
                        InlineKeyboardButton("ᴀᴅᴠᴀɴᴄᴇ", callback_data="advanced_command"),
                    ],
                    [
                        InlineKeyboardButton("ᴇxᴘᴇʀᴛ",callback_data="expert_command"),
                       
                        InlineKeyboardButton("ʜᴏᴍᴇ", callback_data="Miko_back"),
                    ],
                ]
            ),
            parse_mode="Markdown",  # Added this line to explicitly specify Markdown parsing
        )
async def Music_button(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""ʜᴇʀᴇ ɪꜱ ʜᴇʟᴘ ᴍᴇɴᴜ ꜰᴏʀ ᴍᴜꜱɪᴄ """,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴀᴅᴍɪɴ", callback_data="Music_admin"
                        ),
                        InlineKeyboardButton(
                            text="ᴀᴜᴛʜ", callback_data="Music_auth"
                        ),
                        InlineKeyboardButton(
                            text="ᴄ-ᴘʟᴀʏ", callback_data="Music_c-play" )
                    ],
                    [
                        InlineKeyboardButton(
                            text="ʟᴏᴏᴘ", callback_data="Music_loop"
                        ),
                        InlineKeyboardButton(
                            text="ᴘɪɴɢ", callback_data="Music_ping"
                        ),
                        InlineKeyboardButton(
                            text="ᴘʟᴀʏ", callback_data="Music_play")
                    ],
                    [
                        InlineKeyboardButton(
                            text="ꜱʜᴜꜰꜰʟᴇ", callback_data="Music_shuffle"
                        ),
                        InlineKeyboardButton(
                            text="ꜱᴇᴇᴋ", callback_data="Music_seek"
                        ),
                        InlineKeyboardButton(
                            text="ꜱᴏɴɢ", callback_data="Music_song")
                    ],
                    [
                        InlineKeyboardButton(
                            text="ꜱᴘᴇᴇᴅ", callback_data="Music_speed"
                        ),
                        InlineKeyboardButton(
                            text="ᴍᴏᴅᴇ", callback_data="Music_mode"
                        ),
                        InlineKeyboardButton(
                            text="ᴏᴛʜᴇʀ", callback_data="Music_other")
                    ],
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="extra_command_handler")
                    ],
                ]
            ),)
        
async def Music_about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "Music_":
        await query.message.edit_text(
            """
 ʜᴇʀᴇ ɪꜱ ʜᴇʟᴘ ᴍᴇɴᴜ ꜰᴏʀ ᴍᴜꜱɪᴄ 
""",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴀᴅᴍɪɴ", callback_data="Music_admin"
                        ),
                        InlineKeyboardButton(
                            text="ᴀᴜᴛʜ", callback_data="Music_auth"
                        ),
                        InlineKeyboardButton(
                            text="ᴄ-ᴘʟᴀʏ", callback_data="Music_c-play" )
                    ],
                    [
                        InlineKeyboardButton(
                            text="ʟᴏᴏᴘ", callback_data="Music_loop"
                        ),
                        InlineKeyboardButton(
                            text="ᴘɪɴɢ", callback_data="Music_ping"
                        ),
                        InlineKeyboardButton(
                            text="ᴘʟᴀʏ", callback_data="Music_play")
                    ],
                    [
                        InlineKeyboardButton(
                            text="ꜱʜᴜꜰꜰʟᴇ", callback_data="Music_shuffle"
                        ),
                        InlineKeyboardButton(
                            text="ꜱᴇᴇᴋ", callback_data="Music_seek"
                        ),
                        InlineKeyboardButton(
                            text="ꜱᴏɴɢ", callback_data="Music_song")
                    ],
                    [
                        InlineKeyboardButton(
                            text="ꜱᴘᴇᴇᴅ", callback_data="Music_speed"
                        ),
                        InlineKeyboardButton(
                            text="ᴍᴏᴅᴇ", callback_data="Music_mode"
                        ),
                        InlineKeyboardButton(
                            text="ᴏᴛʜᴇʀ", callback_data="Music_other")
                    ],
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="extra_command_handler")
                    ],
                ]
            ),
        )
    elif query.data == "Music_admin":
        await query.message.edit_text(
            """*» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅꜱ «*
ᴊᴜsᴛ ᴀᴅᴅ *ᴄ* ɪɴ ᴛʜᴇ sᴛᴀʀᴛɪɴɢ ᴏғ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ᴜsᴇ ᴛʜᴇᴍ ғᴏʀ ᴄʜᴀɴɴᴇʟ.

/pause : ᴩᴀᴜsᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ.

/resume : ʀᴇsᴜᴍᴇ ᴛʜᴇ ᴩᴀᴜsᴇᴅ sᴛʀᴇᴀᴍ.

/skip : sᴋɪᴩ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ ᴀɴᴅ sᴛᴀʀᴛ sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ɴᴇxᴛ ᴛʀᴀᴄᴋ ɪɴ ǫᴜᴇᴜᴇ.

/end ᴏʀ /stop : ᴄʟᴇᴀʀs ᴛʜᴇ ǫᴜᴇᴜᴇ ᴀɴᴅ ᴇɴᴅ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ.

/player : ɢᴇᴛ ᴀ ɪɴᴛᴇʀᴀᴄᴛɪᴠᴇ ᴩʟᴀʏᴇʀ ᴩᴀɴᴇʟ.

/queue : sʜᴏᴡs ᴛʜᴇ ǫᴜᴇᴜᴇᴅ ᴛʀᴀᴄᴋs ʟɪsᴛ.
""",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"
                        ),
                       
                    ]
                ]
            ),
        )
    elif query.data == "Music_back":
        first_name = update.effective_user.first_name
        await query.message.edit_text(PM_START_TEXT.format(escape_markdown(first_name), BOT_NAME),
            reply_markup=InlineKeyboardMarkup(buttons),

            timeout=60,

        )
    elif query.data == "Music_auth":
        await query.message.edit_text(
            """*» Auth Users «*
ᴀᴜᴛʜ ᴜsᴇʀs ᴄᴀɴ ᴜsᴇ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ɪɴ ᴛʜᴇ ʙᴏᴛ ᴡɪᴛʜᴏᴜᴛ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.

/auth [ᴜsᴇʀɴᴀᴍᴇ/ᴜsᴇʀ_ɪᴅ] : ᴀᴅᴅ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴜᴛʜ ʟɪsᴛ ᴏғ ᴛʜᴇ ʙᴏᴛ.

/unauth [ᴜsᴇʀɴᴀᴍᴇ/ᴜsᴇʀ_ɪᴅ] : ʀᴇᴍᴏᴠᴇ ᴀ ᴀᴜᴛʜ ᴜsᴇʀs ғʀᴏᴍ ᴛʜᴇ ᴀᴜᴛʜ ᴜsᴇʀs ʟɪsᴛ.

/authusers : sʜᴏᴡs ᴛʜᴇ ʟɪsᴛ ᴏғ ᴀᴜᴛʜ ᴜsᴇʀs ᴏғ ᴛʜᴇ ɢʀᴏᴜᴩ.
""",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"
                        ),
                        
                    ]
                ]
            ),
        )
    elif query.data == "Music_c-play":
        await query.message.edit_text(
            """*» channel-play ᴄᴏᴍᴍᴀɴᴅꜱ «*
ʏᴏᴜ ᴄᴀɴ sᴛʀᴇᴀᴍ ᴀᴜᴅɪᴏ/ᴠɪᴅᴇᴏ ɪɴ ᴄʜᴀɴɴᴇʟ.

/cplay : sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴀᴜᴅɪᴏ ᴛʀᴀᴄᴋ ᴏɴ ᴄʜᴀɴɴᴇʟ's ᴠɪᴅᴇᴏᴄʜᴀᴛ.

/cvplay : sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴠɪᴅᴇᴏ ᴛʀᴀᴄᴋ ᴏɴ ᴄʜᴀɴɴᴇʟ's ᴠɪᴅᴇᴏᴄʜᴀᴛ.

/cplayforce or /cvplayforce : sᴛᴏᴩs ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ᴀɴᴅ sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛʀᴀᴄᴋ.

/channelplay [ᴄʜᴀᴛ ᴜsᴇʀɴᴀᴍᴇ ᴏʀ ɪᴅ] ᴏʀ [ᴅɪsᴀʙʟᴇ] : ᴄᴏɴɴᴇᴄᴛ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴀ ɢʀᴏᴜᴩ ᴀɴᴅ sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʀᴀᴄᴋs ʙʏ ᴛʜᴇ ʜᴇʟᴩ ᴏғ ᴄᴏᴍᴍᴀɴᴅs sᴇɴᴛ ɪɴ ɢʀᴏᴜᴩ.
""",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"
                        ),
                       
                    ]
                ]
            ),
        )
    elif query.data == "Music_loop":
        await query.message.edit_text(f"*»loop ᴄᴏᴍᴍᴀɴᴅꜱ «*"
            f"""
/play or /vplay or /cplay  - ʙᴏᴛ ᴡɪʟʟ ꜱᴛᴀʀᴛ ᴘʟᴀʏɪɴɢ ʏᴏᴜʀ ɢɪᴠᴇɴ ϙᴜᴇʀʏ on ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴏʀ ꜱᴛʀᴇᴀᴍ ʟɪᴠᴇ ʟɪɴᴋꜱ ᴏɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛꜱ.
ʟᴏᴏᴘ sᴛʀᴇᴀᴍ :

sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ ɪɴ ʟᴏᴏᴘ

/loop [enable/disable] : ᴇɴᴀʙʟᴇs/ᴅɪsᴀʙʟᴇs ʟᴏᴏᴘ ғᴏʀ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ

/loop [1, 2, 3, ...] : ᴇɴᴀʙʟᴇs ᴛʜᴇ ʟᴏᴏᴘ ғᴏʀ ᴛʜᴇ ɢɪᴠᴇɴ ᴠᴀʟᴜᴇ.
""",
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                  
                    ]
                ]
            ),
        ) 
    elif query.data == "Music_ping":
        await query.message.edit_text(
         f"""                    
  ᴘɪɴɢ & sᴛᴀᴛs :

/start : sᴛᴀʀᴛs ᴛʜᴇ ᴍᴜsɪᴄ ʙᴏᴛ.

/help : ɢᴇᴛ ʜᴇʟᴩ ᴍᴇɴᴜ ᴡɪᴛʜ ᴇxᴩʟᴀɴᴀᴛɪᴏɴ ᴏғ ᴄᴏᴍᴍᴀɴᴅs.

/mping : sʜᴏᴡs ᴛʜᴇ ᴩɪɴɢ ᴀɴᴅ sʏsᴛᴇᴍ sᴛᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.

/mstats : sʜᴏᴡs ᴛʜᴇ ᴏᴠᴇʀᴀʟʟ sᴛᴀᴛs ᴏғ ᴛʜᴇ ʙᴏᴛ.

/topusers : ᴍᴏꜱᴛ Qᴜᴇʀɪᴇꜱ ʙʏ ᴜꜱᴇʀꜱ
 
/trend : ᴍᴏꜱᴛ ᴘʟᴀʏᴇᴅ ꜱᴏɴɢꜱ ɪɴ ᴄᴜʀʀᴇɴᴛ ᴡᴇᴇᴋ  
""",
        
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                       
                    ]
                ]
            ),
        ) 
    elif query.data == "Music_play":
        await query.message.edit_text(PLAYFORCE,
        
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                      
                    ]
                ]
            ),
        ) 
    elif query.data == "Music_shuffle":
        await query.message.edit_text(QUEUE,
        
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                       
                    ]
                ]
            ),
        ) 
    elif query.data == "Music_seek":
        await query.message.edit_text(SEEKBACK,
        
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                       
                    ]
                ]
            ),
        )
    elif query.data == "Music_song":
        await query.message.edit_text(SONG,
        
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                      
                    ]
                ]
            ),
        )
    elif query.data == "Music_speed":
        await query.message.edit_text("music mode text hereeeee"
 """*»sᴘᴇᴇᴅ ᴄᴏᴍᴍᴀɴᴅꜱ «*
sᴘᴇᴇᴅ ᴄᴏᴍᴍᴀɴᴅs :

ʏᴏᴜ ᴄᴀɴ ᴄᴏɴᴛʀᴏʟ ᴛʜᴇ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ᴏғ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ. [ᴀᴅᴍɪɴs ᴏɴʟʏ]

/speed or /playback : ғᴏʀ ᴀᴅᴊᴜsᴛɪɴɢ ᴛʜᴇ ᴀᴜᴅɪᴏ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ɪɴ ɢʀᴏᴜᴘ.

/cspeed or /cplayback : ғᴏʀ ᴀᴅᴊᴜsᴛɪɴɢ ᴛʜᴇ ᴀᴜᴅɪᴏ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ɪɴ ᴄʜᴀɴɴᴇʟ.
""",
        
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                      
                    ]
                ]
            ),
        )
    elif query.data == "Music_mode":
         await query.message.edit_text("music mode text hereeeee"
 """*» ᴄʜᴀɴɢᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴄᴏᴍᴍᴀɴᴅꜱ «*
ᴄʜᴀɴɢᴇ ꜱᴇᴛᴛɪɴɢꜱ :

/playmode : ꜰᴏʀ ᴄʜᴀɴɢᴇ ᴘʟᴀʏᴍᴏᴅᴇ ɪɴ ɢʀᴏᴜᴘꜱ ʙᴇᴛᴡᴇᴇɴ ᴍᴇᴍʙᴇʀꜱ ᴀɴᴅ ᴀᴅᴍɪɴꜱ

/msettings : ꜰᴏʀ ᴄʜᴀɴɢᴇ ᴀᴜᴛʜ ᴜꜱᴇʀꜱ ᴀɴᴅ ʟᴀɴɢᴜᴀɢᴇ 

/reload : ʀᴇʟᴏᴀᴅ ᴀᴅᴍɪɴ ᴄᴀᴄʜᴇꜱ
/mreboot : ʀᴇꜱᴛᴀʀᴛ ʙᴏᴛ ꜰᴏʀ ʏᴏᴜʀ ɢʀᴏᴜᴘ
/language : ᴄʜᴀɴɢᴇ ʟᴀɴɢᴜᴀɢᴇ ꜰᴏʀ ʏᴏᴜʀ ᴄʜᴀᴛ [Same : /lang /setlang ]
/vclogger : ᴅɪꜱᴀʙʟᴇ/ᴇɴᴀʙʟᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛ ʟᴏɢꜱ
""",
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                      
                    ]
                ]
            ),
        )
    elif query.data == "Music_other":
        await query.message.edit_text("music other text here"
"""*» ᴄᴏᴍᴍᴀɴᴅꜱ «*
ᴊᴜsᴛ ᴀᴅᴅ *ᴄ* ɪɴ ᴛʜᴇ sᴛᴀʀᴛɪɴɢ ᴏғ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ᴜsᴇ ᴛʜᴇᴍ ғᴏʀ ᴄʜᴀɴɴᴇʟ.

[Only for SUDO] :
/gcast [MSG or reply to MSG] : Broadcast a MSG. 
[>> details /broadcastinfo]
/blacklistchat [ChatID] : Blacklist a chat.
/whitelistchat [ChatID] : Whitelist a chat.
/blacklistedchat : List of Blacklisted chats.
/block [Username or Reply] : Block the user access.
/unblock [Username or Reply] : Unblock the user access.
/blockedusers : List of blocked users.
/logs : Get logs of bot.
/logger [on/off] : Logging activities in log group.
/maintenance [on/off] : Maintenance mode of bot...
/addfreechat : free from autoend/autoleave 
/rmfreechat : remove a free chat
/freechats : list of free chats 
/setassist chat_id assist_id : renew assistant
/sysinfo : system realtime info
/spt : speedtest
/getinfo [ID] : info of a chat 
/gban /ungban /forcegban & /gbanlist are generic
/msbanall  ok: ban all
/activevc: list of active vc
/autorestart: automatic restart 4am(ist)
more cmd get help with cmd /autoend, /autoleave, /directplay
""",                                
        
          reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="⬅️ ʙᴀᴄᴋ", callback_data="Music_"),
                      
                    ]
                ]
            ),
        )

async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("AI", callback_data="ai_handler"),
            InlineKeyboardButton("IMAGEGEN", callback_data="more_aihandlered"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🧠 *Here are the options for* :",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def ai_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "ai_command_handler":
        await query.answer()
        await query.message.edit_text(
            "🧠 *Here are the options for* :",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("AI", callback_data="ai_handler"),
                        InlineKeyboardButton(
                            "IMAGEGEN", callback_data="more_aihandlered"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "» 𝘽𝘼𝘾𝙆 «", callback_data="extra_command_handler"
                        ),
                    ],
                ]
            ),
            parse_mode="Markdown",
        )


async def ai_handler_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "ai_handler":
        await query.answer()
        await query.message.edit_text(
            "All Commands:\n"
            "➽ /askgpt <write query>: A chatbot using GPT for responding to user queries.\n\n"
            "➽ /palm <write prompt>: Performs a Palm search using a chatbot.\n\n"
            "➽ /upscale <reply to image>: Upscales your image quality.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "More Image Gen ➪", callback_data="more_ai_handler"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "⇦ BACK", callback_data="ai_command_handler"
                        ),
                    ],
                ],
            ),
            parse_mode="Markdown",
        )


async def more_ai_handler_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "more_ai_handler":
        await query.answer()
        await query.message.edit_text(
            "*Here's more image gen related commands*:\n\n"
            "Command: /meinamix\n"
            "  • Description: Generates an image using the meinamix model.\n\n"
            "Command: /darksushi\n"
            "  • Description: Generates an image using the darksushi model.\n\n"
            "Command: /meinahentai\n"
            "  • Description: Generates an image using the meinahentai model.\n\n"
            "Command: /darksushimix\n"
            "  • Description: Generates an image using the darksushimix model.\n\n"
            "Command: /anylora\n"
            "  • Description: Generates an image using the anylora model.\n\n"
            "Command: /cetsumix\n"
            "  • Description: Generates an image using the cetsumix model.\n\n"
            "Command: /anything\n"
            "  • Description: Generates an image using the anything model.\n\n"
            "Command: /absolute\n"
            "  • Description: Generates an image using the absolute model.\n\n"
            "Command: /darkv2\n"
            "  • Description: Generates an image using the darkv2 model.\n\n"
            "Command: /creative\n"
            "  • Description: Generates an image using the creative model.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⇦ BACK", callback_data="ai_handler"),
                    ],
                ],
            ),
        )


async def more_aihandlered_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "more_aihandlered":
        await query.answer()
        await query.message.edit_text(
            "*Here's more image gen related commands*:\n\n"
            "*Command*: /meinamix\n"
            "  • Description: Generates an image using the meinamix model.\n\n"
            "*Command*: /darksushi\n"
            "  • Description: Generates an image using the darksushi model.\n\n"
            "*Command*: /meinahentai\n"
            "  • Description: Generates an image using the meinahentai model.\n\n"
            "*Command*: /darksushimix\n"
            "  • Description: Generates an image using the darksushimix model.\n\n"
            "*Command*: /anylora\n"
            "  • Description: Generates an image using the anylora model.\n\n"
            "*Command*: /cetsumix\n"
            "  • Description: Generates an image using the cetsumix model.\n\n"
            "*Command*: /anything\n"
            "  • Description: Generates an image using the anything model.\n\n"
            "*Command*: /absolute\n"
            "  • Description: Generates an image using the absolute model.\n\n"
            "*Command*: /darkv2\n"
            "  • Description: Generates an image using the darkv2 model.\n\n"
            "*Command*: /creative\n"
            "  • Description: Generates an image using the creative model.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⇦ BACK", callback_data="ai_command_handler"
                        ),
                    ],
                ],
            ),
        )

async def main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data=="basic_command":
        await query.message.edit_text("""Bᴀsɪᴄ Cᴏᴍᴍᴀɴᴅs.
👮🏻Aᴠᴀɪʟᴀʙʟᴇ ᴛᴏ Aᴅᴍɪɴs & Mᴏᴅᴇʀᴀᴛᴏʀs.
🕵🏻Aᴠᴀɪʟᴀʙʟᴇ ᴛᴏ Aᴅᴍɪɴs.

👮🏻 /reload ᴜᴘᴅᴀᴛᴇs ᴛʜᴇ Aᴅᴍɪɴs ʟɪsᴛ ᴀɴᴅ ᴛʜᴇɪʀ ᴘʀɪᴠɪʟᴇɢᴇs.
🕵🏻 /settings ʟᴇᴛs ʏᴏᴜ ᴍᴀɴᴀɢᴇ ᴀʟʟ ᴛʜᴇ Bᴏᴛ sᴇᴛᴛɪɴɢs ɪɴ ᴀ ɢʀᴏᴜᴘ.
👮🏻 /ban ʟᴇᴛs ʏᴏᴜ ʙᴀɴ ᴀ ᴜsᴇʀ ғʀᴏᴍ ᴛʜᴇ ɢʀᴏᴜᴘ ᴡɪᴛʜᴏᴜᴛ ɢɪᴠɪɴɢ ʜɪᴍ ᴛʜᴇ ᴘᴏssɪʙɪʟɪᴛʏ ᴛᴏ Jᴏɪɴ ᴀɢᴀɪɴ ᴜsɪɴɢ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ɢʀᴏᴜᴘ.
👮🏻 /mute ᴘᴜᴛs ᴀ ᴜsᴇʀ ɪɴ ʀᴇᴀᴅ-ᴏɴʟʏ ᴍᴏᴅᴇ. Hᴇ ᴄᴀɴ ʀᴇᴀᴅ ʙᴜᴛ ʜᴇ ᴄᴀɴ'ᴛ sᴇɴᴅ ᴀɴʏ ᴍᴇssᴀɢᴇs.
👮🏻 /kick ʙᴀɴs ᴀ ᴜsᴇʀ ғʀᴏᴍ ᴛʜᴇ ɢʀᴏᴜᴘ, ɢɪᴠɪɴɢ ʜɪᴍ ᴛʜᴇ ᴘᴏssɪʙɪʟɪᴛʏ ᴛᴏ Jᴏɪɴ ᴀɢᴀɪɴ ᴡɪᴛʜ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ɢʀᴏᴜᴘ.
👮🏻 /unban ʟᴇᴛs ʏᴏᴜ ʀᴇᴍᴏᴠᴇ ᴀ ᴜsᴇʀ ғʀᴏᴍ ɢʀᴏᴜᴘ's ʙʟᴀᴄᴋʟɪsᴛ, ɢɪᴠɪɴɢ ᴛʜᴇᴍ ᴛʜᴇ ᴘᴏssɪʙɪʟɪᴛʏ ᴛᴏ Jᴏɪɴ ᴀɢᴀɪɴ ᴡɪᴛʜ ᴛʜᴇ ʟɪɴᴋ ᴏғ ᴛʜᴇ ɢʀᴏᴜᴘ.
👮🏻 /info ɢɪᴠᴇs ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴀ ᴜsᴇʀ.

◽️ /staff ɢɪᴠᴇs ᴛʜᴇ ᴄᴏᴍᴘʟᴇᴛᴇ Lɪsᴛ ᴏғ ɢʀᴏᴜᴘ Sᴛᴀғғ!.""",parse_mode="Markdown",
            
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="• ʙᴀᴄᴋ •", callback_data="extra_command_handler")
                    ]
                ]
            ),
            )
    elif query.data=="expert_command":
        await query.message.edit_text("""Exᴘᴇʀᴛ ᴄᴏᴍᴍᴀɴᴅs

👥 Aᴠᴀɪʟᴀʙʟᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs
👮🏻 Aᴠᴀɪʟᴀʙʟᴇ ᴛᴏ Aᴅᴍɪɴs & Mᴏᴅᴇʀᴀᴛᴏʀs.
🕵🏻 Aᴠᴀɪʟᴀʙʟᴇ ᴛᴏ Aᴅᴍɪɴs

🕵🏻  /unbanall ᴍᴇᴍʙᴇʀs ғʀᴏᴍ ʏᴏᴜʀ ɢʀᴏᴜᴘs
👮🏻  /unmuteall ᴜɴᴍᴜᴛᴇᴀʟʟ ᴀʟʟ ғʀᴏᴍ Yᴏᴜʀ Gʀᴏᴜᴘ

Pɪɴɴᴇᴅ Mᴇssᴀɢᴇs
🕵🏻  /pin [ᴍᴇssᴀɢᴇ] sᴇɴᴅs ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛʜʀᴏᴜɢʜ ᴛʜᴇ Bᴏᴛ ᴀɴᴅ ᴘɪɴs ɪᴛ.
🕵🏻  /pin ᴘɪɴs ᴛʜᴇ ᴍᴇssᴀɢᴇ ɪɴ ʀᴇᴘʟʏ
🕵🏻  /unpin ʀᴇᴍᴏᴠᴇs ᴛʜᴇ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇ.
🕵🏻  /adminlist ʟɪsᴛ ᴏғ ᴀʟʟ ᴛʜᴇ sᴘᴇᴄɪᴀʟ ʀᴏʟᴇs ᴀssɪɢɴᴇᴅ ᴛᴏ ᴜsᴇʀs.

◽️ /bug: (ᴍᴇssᴀɢᴇ) ᴛᴏ Sᴇɴᴅ ᴍᴇssᴀɢᴇ ᴀɴᴅ ᴇʀʀᴏʀs ᴡʜɪᴄʜ ʏᴏᴜ ᴀʀᴇ ғᴀᴄɪɴɢ 
ᴇx: /bug Hᴇʏ Tʜᴇʀᴇ Is ᴀ Sᴏᴍᴇᴛʜɪɴɢ Eʀʀᴏʀ @username ᴏғ ᴄʜᴀᴛ! .""",parse_mode="Markdown",
            
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="• ʙᴀᴄᴋ •", callback_data="extra_command_handler")
                    ]
                ]
            ),
            )
    elif query.data=="advanced_command":
        await query.message.edit_text("""Aᴅᴠᴀɴᴄᴇᴅ Cᴏᴍᴍᴀɴᴅs

👮🏻Aᴠᴀɪʟᴀʙʟᴇ ᴛᴏ Aᴅᴍɪɴs & Mᴏᴅᴇʀᴀᴛᴏʀs.
🕵🏻Aᴠᴀɪʟᴀʙʟᴇ ᴛᴏ Aᴅᴍɪɴs.
🛃 Aᴠᴀɪʟᴀʙʟᴇ ᴛᴏ Aᴅᴍɪɴs & Cʟᴇᴀɴᴇʀs

Wᴀʀɴ Mᴀɴᴀɢᴇᴍᴇɴᴛ
👮🏻  /warn ᴀᴅᴅs ᴀ ᴡᴀʀɴ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ
👮🏻  /unwarn ʀᴇᴍᴏᴠᴇs ᴀ ᴡᴀʀɴ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ
👮🏻  /warns ʟᴇᴛs ʏᴏᴜ sᴇᴇ ᴀɴᴅ ᴍᴀɴᴀɢᴇ ᴜsᴇʀ ᴡᴀʀɴs

🛃  /del ᴅᴇʟᴇᴛᴇs ᴛʜᴇ sᴇʟᴇᴄᴛᴇᴅ ᴍᴇssᴀɢᴇ
🛃  /purge ᴅᴇʟᴇᴛᴇs ғʀᴏᴍ ᴛʜᴇ sᴇʟᴇᴄᴛᴇᴅ ᴍᴇssᴀɢᴇ.""",parse_mode="Markdown",
            
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="• ʙᴀᴄᴋ •", callback_data="extra_command_handler")
                    ]
                ]
            ),
            )


async def anime_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    
    if query.data == "anime_command_handler":
        await query.answer()
        await query.message.edit_text(
            "⛩𝗔𝗻𝗶𝗺𝗲 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 :\n\n"
            "**╔ /anime: **fetches info on single anime (includes buttons to look up for prequels and sequels)\n"
            "**╠ /character: **fetches info on multiple possible characters related to query\n"
            "**╠ /manga: **fetches info on multiple possible mangas related to query\n"
            "**╠ /airing: **fetches info on airing data for anime\n"
            "**╠ /studio: **fetches info on multiple possible studios related to query\n"
            "**╠ /schedule: **fetches scheduled animes\n"
            "**╠ /browse: **get popular, trending or upcoming animes\n"
            "**╠ /top: **to retrieve top animes for a genre or tag\n"
            "**╠ /watch: **fetches watch order for anime series\n"
            "**╠ /fillers: **to get a list of anime fillers\n"
            "**╠ /gettags: **get a list of available tags\n"
            "**╠ /animequotes: **get random anime quotes\n"
            "**╚ /getgenres: **Get list of available Genres\n\n"
            "**⚙️ Group Settings:**\n"
            "**╔**\n"
            "**╠ /anisettings: **to toggle NSFW lock and airing notifications and other settings in groups (anime news)\n"
            "**╚**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("More Info", url="https://anilist.co/"),
                    ],
                    [
                        InlineKeyboardButton(
                            "» 𝘽𝘼𝘾𝙆 «", callback_data="extra_command_handler"
                        ),
                    ],
                ]
            ),
            parse_mode="Markdown",  # Added this line to explicitly specify Markdown parsing
        )
    


async def genshin_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "genshin_command_handler":
        await query.answer()
        await query.message.edit_text(
            "⛩ 𝗚𝗲𝗻𝘀𝗵𝗶𝗻 𝗜𝗺𝗽𝗮𝗰𝘁 ⛩\n\n"
            "*UNDER DEVELOPMENT*",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "More Info", url="https://genshin.mihoyo.com/"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "» 𝘽𝘼𝘾𝙆 «", callback_data="extra_command_handler"
                        ),
                    ],
                ]
            ),
            parse_mode="Markdown",  # Added this line to explicitly specify Markdown parsing
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    await context.bot.send_message(
        chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML
    )


# for test purposes
async def error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    error = context.error
    try:
        raise error
    except Forbidden:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "➲ *HELP SECTION OF* *{}* :\n".format(HELPABLE[module].__mod_name__)
                + HELPABLE[module].__help__
            )
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="◁", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        await context.bot.answer_callback_query(query.id)

    except BadRequest:
        pass


async def stats_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "insider_":
        uptime = get_readable_time((time.time() - StartTime))
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        text = f"""
𝙎𝙮𝙨𝙩𝙚𝙢 𝙨𝙩𝙖𝙩𝙨
➖➖➖➖➖➖
UPTIME ➼ {uptime}
CPU ➼ {cpu}%
RAM ➼ {mem}%
DISK ➼ {disk}%

PYTHON ➼ {PYTHON_VERSION}

PTB ➼ {PTB_VERSION}
TELETHON ➼ {TELETHON_VERSION}
PYROGRAM ➼ {PYROGRAM_VERSION}
"""
        await query.answer(text=text, show_alert=True)







async def Miko_about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "Miko_":
        uptime = get_readable_time((time.time() - StartTime))
        message_text = (
            f"➲ <b>Ai integration.</b>"
            f"\n➲ <b>Advance management capability.</b>"
            f"\n➲ <b>Anime bot functionality.</b>"
            f"\n\n<b>Click on the buttons below for getting help and info about</b> {BOT_NAME}."
        )
        await query.message.edit_text(
            text=message_text,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ABOUT", callback_data="Miko_support"
                        ),
                        InlineKeyboardButton(text="COMMAND", callback_data="help_back"),
                    ],
                    [
                        InlineKeyboardButton(text="INSIDER", callback_data="insider_"),
                    ],
                    [
                        InlineKeyboardButton(text="◁", callback_data="Miko_back"),
                    ],
                ]
            ),
        )
    elif query.data == "Miko_support":
        message_text = (
            "*Our bot leverages SQL, MongoDB, Telegram, MTProto for secure and efficient operations. It resides on a high-speed server, integrates numerous APIs, ensuring quick and versatile responses to user queries.*"
            f"\n\n*If you find any bug in {BOT_NAME} Please report it at the support chat.*"
        )
        await query.message.edit_text(
            text=message_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="SUPPORT", url=f"https://t.me/{SUPPORT_CHAT}"
                        ),
                        InlineKeyboardButton(
                            text="DEVELOPER", url=f"tg://user?id={OWNER_ID}"
                        ),
                    ],
                    [
                        InlineKeyboardButton(text="◁", callback_data="Miko_"),
                    ],
                ]
            ),
        )
    elif query.data == "Miko_back":
        first_name = update.effective_user.first_name
        button=private_panel()
        await query.message.edit_text(
            PM_START_TEXT.format(escape_markdown(first_name), BOT_NAME),
            reply_markup=InlineKeyboardMarkup(button),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            await update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="HELP",
                                url="https://t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        await update.effective_message.reply_text(
            "» *Choose an option for getting* [𝗵𝗲𝗹𝗽](https://telegra.ph/file/cce9038f6a9b88eb409b5.jpg)",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="OPEN IN PM",
                            url="https://t.me/{}?start=help".format(
                                context.bot.username
                            ),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="OPEN HERE",
                            callback_data="extra_command_handler",
                        )
                    ],
                ]
            ),
            parse_mode="Markdown",  # Added this line to explicitly specify Markdown parsing
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        await send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="◁", callback_data="help_back")]]
            ),
        )

    else:
        await send_help(chat.id, HELP_STRINGS)


async def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            await dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            await dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            await dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


async def settings_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            await query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="◁",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            await query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            await query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            await query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        await query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


async def get_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            await msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="SETTINGS",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        await send_settings(chat.id, user.id, True)


async def migrate_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, ᴛᴏ %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        with contextlib.suppress(KeyError, AttributeError):
            mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully Migrated!")
    raise ApplicationHandlerStop


# <=======================================================================================================>


# <=================================================== MAIN ====================================================>
def main():
    function(CommandHandler("start", start))

    function(CommandHandler("help", extra_command_handlered))
    function(CommandHandler("music", Music_button))
    function(CallbackQueryHandler(Music_about_callback, pattern=r"Music_",))
    function(CallbackQueryHandler(help_button, pattern=r"help_.*"))

    function(CommandHandler("settings", get_settings))
    function(CallbackQueryHandler(settings_button, pattern=r"stngs_"))

    function(CallbackQueryHandler(Miko_about_callback, pattern=r"Miko_"))
    function(CallbackQueryHandler(stats_back, pattern=r"insider_"))
    function(MessageHandler(filters.StatusUpdate.MIGRATE, migrate_chats))
    function(CallbackQueryHandler(ai_handler_callback, pattern=r"ai_handler"))
    function(CallbackQueryHandler(more_ai_handler_callback, pattern=r"more_ai_handler"))
    function(CallbackQueryHandler(main_callback, pattern=r".*_command$"))
    function(CallbackQueryHandler(ai_command_callback, pattern="ai_command_handler"))
    function(
        CallbackQueryHandler(anime_command_callback, pattern="anime_command_handler")
    )
    function(
        CallbackQueryHandler(more_aihandlered_callback, pattern="more_aihandlered")
    )
    function(
        CallbackQueryHandler(extra_command_callback, pattern="extra_command_handler")
    )

    function(CommandHandler("ai", ai_command))
    function(
        CallbackQueryHandler(
            genshin_command_callback, pattern="genshin_command_handler"
        )
    )

    dispatcher.add_error_handler(error_callback)

    LOGGER.info("Mikobot is starting >> Using long polling.")
    dispatcher.run_polling(timeout=15, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
        tbot.start(bot_token=TOKEN)
        app.start()
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        err = traceback.format_exc()
        LOGGER.info(err)
    # finally:
    #     try:
    #         if loop.is_running():
    #             loop.stop()
    #     finally:
    #         loop.close()
    #     LOGGER.info(
    #         "------------------------ Stopped Services ------------------------"
    #     )
# <==================================================== END ===================================================>
