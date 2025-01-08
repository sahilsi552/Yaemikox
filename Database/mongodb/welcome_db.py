import random
import threading
from typing import Union
from pymongo import MongoClient, ASCENDING
from Mikobot.plugins.helper_funcs.msg_types import Types

from .afk_db import dbnames as db
welcome_collection = db['welcome_pref']
welcome_buttons = db['welcome_buttons']
goodbye_buttons = db['goodbye_buttons']
welcome_mutesdb = db['welcome_mutesdb']
welcome_mute_users = db['welcome_mute_users']
clean_servicesdb = db['clean_servicesdb']
raid_mode = db['raid_mode']

# Create indexes
welcome_collection.create_index([("chat_id", ASCENDING)], unique=True)
welcome_buttons.create_index([("chat_id", ASCENDING)])
goodbye_buttons.create_index([("chat_id", ASCENDING)])
welcome_mutesdb.create_index([("chat_id", ASCENDING)], unique=True)
welcome_mute_users.create_index([("user_id", ASCENDING), ("chat_id", ASCENDING)], unique=True)
clean_servicesdb.create_index([("chat_id", ASCENDING)], unique=True)
raid_mode.create_index([("chat_id", ASCENDING)], unique=True)

DEFAULT_WELCOME = "ʜᴇʏ {first}, ʜᴏᴡ ᴀʀᴇ ʏᴏᴜ?"
DEFAULT_GOODBYE = "ɴɪᴄᴇ ᴋɴᴏᴡɪɴɢ ʏᴀ!"

DEFAULT_WELCOME_MESSAGES = [
    "{first} ɪs ʜᴇʀᴇ!",
    "ʀᴇᴀᴅʏ ᴘʟᴀʏᴇʀ {first}",
    "ᴡᴇʟᴄᴏᴍᴇ ʙʀᴏ {first}",
]

DEFAULT_GOODBYE_MESSAGES = [
    "{first} ᴡɪʟʟ ʙᴇ ᴍɪssᴇᴅ.",
    "{first} ᴡʜᴇɴ ʙᴀᴄᴋ ?.",
]

INSERTION_LOCK = threading.RLock()
WELC_BTN_LOCK = threading.RLock()
LEAVE_BTN_LOCK = threading.RLock()
WM_LOCK = threading.RLock()
CS_LOCK = threading.RLock()
RAID_LOCK = threading.RLock()

def welcome_mutes(chat_id):
    with WM_LOCK:
        chat = welcome_mutesdb.find_one({"chat_id": str(chat_id)})
        return chat["welcomemutes"] if chat else False

def set_welcome_mutes(chat_id, welcomemutes):
    with WM_LOCK:
        welcome_mutesdb.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"welcomemutes": welcomemutes}},
            upsert=True
        )

def set_human_checks(user_id, chat_id):
    with INSERTION_LOCK:
        welcome_mute_users.update_one(
            {"user_id": user_id, "chat_id": str(chat_id)},
            {"$set": {"human_check": True}},
            upsert=True
        )

def get_human_checks(user_id, chat_id):
    with INSERTION_LOCK:
        user = welcome_mute_users.find_one({"user_id": user_id, "chat_id": str(chat_id)})
        return user["human_check"] if user else None

def get_welc_mutes_pref(chat_id):
    chat = welcome_mutesdb.find_one({"chat_id": str(chat_id)})
    return chat["welcomemutes"] if chat else False

def get_welc_pref(chat_id):
    chat = welcome_collection.find_one({"chat_id": str(chat_id)})
    if chat:
        return (
            chat.get("should_welcome", True),
            chat.get("custom_welcome", DEFAULT_WELCOME),
            chat.get("custom_content"),
            chat.get("welcome_type", Types.TEXT.value),
        )
    return True, DEFAULT_WELCOME, None, Types.TEXT.value

def get_gdbye_pref(chat_id):
    chat = welcome_collection.find_one({"chat_id": str(chat_id)})
    if chat:
        return (
            chat.get("should_goodbye", True),
            chat.get("custom_leave", DEFAULT_GOODBYE),
            chat.get("leave_type", Types.TEXT.value),
        )
    return True, DEFAULT_GOODBYE, Types.TEXT.value

def set_clean_welcome(chat_id, clean_welcome):
    with INSERTION_LOCK:
        welcome_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"clean_welcome": int(clean_welcome)}},
            upsert=True
        )

def get_clean_pref(chat_id):
    chat = welcome_collection.find_one({"chat_id": str(chat_id)})
    return chat.get("clean_welcome", False) if chat else False

def set_welc_preference(chat_id, should_welcome):
    with INSERTION_LOCK:
        welcome_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"should_welcome": should_welcome}},
            upsert=True
        )

def set_gdbye_preference(chat_id, should_goodbye):
    with INSERTION_LOCK:
        welcome_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"should_goodbye": should_goodbye}},
            upsert=True
        )

def set_custom_welcome(chat_id, custom_content, custom_welcome, welcome_type, buttons=None):
    if buttons is None:
        buttons = []

    with INSERTION_LOCK:
        welcome_collection.update_one(
            {"chat_id": str(chat_id)},
            {
                "$set": {
                    "custom_content": custom_content,
                    "custom_welcome": custom_welcome or DEFAULT_WELCOME,
                    "welcome_type": welcome_type.value,
                }
            },
            upsert=True
        )

        with WELC_BTN_LOCK:
            welcome_buttons.delete_many({"chat_id": str(chat_id)})
            for b_name, url, same_line in buttons:
                welcome_buttons.insert_one({
                    "chat_id": str(chat_id),
                    "name": b_name,
                    "url": url,
                    "same_line": same_line
                })

def get_custom_welcome(chat_id):
    chat = welcome_collection.find_one({"chat_id": str(chat_id)})
    return chat.get("custom_welcome", DEFAULT_WELCOME) if chat else DEFAULT_WELCOME

def set_custom_gdbye(chat_id, custom_goodbye, goodbye_type, buttons=None):
    if buttons is None:
        buttons = []

    with INSERTION_LOCK:
        welcome_collection.update_one(
            {"chat_id": str(chat_id)},
            {
                "$set": {
                    "custom_leave": custom_goodbye or DEFAULT_GOODBYE,
                    "leave_type": goodbye_type.value,
                }
            },
            upsert=True
        )

        with LEAVE_BTN_LOCK:
            goodbye_buttons.delete_many({"chat_id": str(chat_id)})
            for b_name, url, same_line in buttons:
                goodbye_buttons.insert_one({
                    "chat_id": str(chat_id),
                    "name": b_name,
                    "url": url,
                    "same_line": same_line
                })

def get_custom_gdbye(chat_id):
    chat = welcome_collection.find_one({"chat_id": str(chat_id)})
    return chat.get("custom_leave", DEFAULT_GOODBYE) if chat else DEFAULT_GOODBYE

def get_welc_buttons(chat_id):
    return list(welcome_buttons.find({"chat_id": str(chat_id)}).sort("_id", 1))

def get_gdbye_buttons(chat_id):
    return list(goodbye_buttons.find({"chat_id": str(chat_id)}).sort("_id", 1))

def clean_service(chat_id: Union[str, int]) -> bool:
    chat_setting = clean_servicesdb.find_one({"chat_id": str(chat_id)})
    return chat_setting["clean_service"] if chat_setting else False

def set_clean_service(chat_id: Union[int, str], setting: bool):
    with CS_LOCK:
        clean_servicesdb.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"clean_service": setting}},
            upsert=True
        )

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        welcome_collection.update_many(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )
        welcome_buttons.update_many(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )
        goodbye_buttons.update_many(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )

def getRaidStatus(chat_id):
    chat = raid_mode.find_one({"chat_id": str(chat_id)})
    if chat:
        return chat["status"], chat["time"], chat["acttime"]
    return False, 21600, 3600  # default

def setRaidStatus(chat_id, status, time=21600, acttime=3600):
    with RAID_LOCK:
        raid_mode.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"status": status, "time": time, "acttime": acttime}},
            upsert=True
        )

def toggleRaidStatus(chat_id):
    with RAID_LOCK:
        chat = raid_mode.find_one({"chat_id": str(chat_id)})
        new_status = not chat["status"] if chat else True
        raid_mode.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {
                "status": new_status,
                "time": chat.get("time", 21600) if chat else 21600,
                "acttime": chat.get("acttime", 3600) if chat else 3600
            }},
            upsert=True
        )
        return new_status

def _ResetRaidOnRestart():
    with RAID_LOCK:
        raid_mode.update_many({}, {"$set": {"status": False}})

# Reset raid status on restart
_ResetRaidOnRestart()

