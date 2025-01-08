import threading
from pymongo import MongoClient, ASCENDING
from Mikobot import DB_NAME
from .afk_db import dbnames

blacklist_collection = dbnames['blacklist']
blacklist_settings_collection = dbnames['blacklist_settings']

BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()
BLACKLIST_SETTINGS_INSERTION_LOCK = threading.RLock()

CHAT_BLACKLISTS = {}
CHAT_SETTINGS_BLACKLISTS = {}

def add_to_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = {
            "chat_id": str(chat_id),
            "trigger": trigger
        }
        blacklist_collection.update_one(
            {"chat_id": str(chat_id), "trigger": trigger},
            {"$set": blacklist_filt},
            upsert=True
        )
        global CHAT_BLACKLISTS
        if CHAT_BLACKLISTS.get(str(chat_id), set()) == set():
            CHAT_BLACKLISTS[str(chat_id)] = {trigger}
        else:
            CHAT_BLACKLISTS.get(str(chat_id), set()).add(trigger)

def rm_from_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        result = blacklist_collection.delete_one({"chat_id": str(chat_id), "trigger": trigger})
        if result.deleted_count > 0:
            if trigger in CHAT_BLACKLISTS.get(str(chat_id), set()):  # sanity check
                CHAT_BLACKLISTS.get(str(chat_id), set()).remove(trigger)
            return True
        return False

def get_chat_blacklist(chat_id):
    return CHAT_BLACKLISTS.get(str(chat_id), set())

def num_blacklist_filters():
    return blacklist_collection.count_documents({})

def num_blacklist_chat_filters(chat_id):
    return blacklist_collection.count_documents({"chat_id": str(chat_id)})

def num_blacklist_filter_chats():
    return len(blacklist_collection.distinct("chat_id"))

def set_blacklist_strength(chat_id, blacklist_type, value):
    with BLACKLIST_SETTINGS_INSERTION_LOCK:
        global CHAT_SETTINGS_BLACKLISTS
        curr_setting = {
            "chat_id": str(chat_id),
            "blacklist_type": int(blacklist_type),
            "value": str(value)
        }
        blacklist_settings_collection.update_one(
            {"chat_id": str(chat_id)},
            {"$set": curr_setting},
            upsert=True
        )
        CHAT_SETTINGS_BLACKLISTS[str(chat_id)] = {
            "blacklist_type": int(blacklist_type),
            "value": value
        }

def get_blacklist_setting(chat_id):
    setting = CHAT_SETTINGS_BLACKLISTS.get(str(chat_id))
    if setting:
        return setting["blacklist_type"], setting["value"]
    return 1, "0"

def __load_chat_blacklists():
    global CHAT_BLACKLISTS
    chats = blacklist_collection.distinct("chat_id")
    for chat_id in chats:
        CHAT_BLACKLISTS[chat_id] = set()
    all_filters = blacklist_collection.find()
    for filt in all_filters:
        CHAT_BLACKLISTS[filt["chat_id"]].add(filt["trigger"])

def __load_chat_settings_blacklists():
    global CHAT_SETTINGS_BLACKLISTS
    chats_settings = blacklist_settings_collection.find()
    for setting in chats_settings:
        CHAT_SETTINGS_BLACKLISTS[setting["chat_id"]] = {
            "blacklist_type": setting["blacklist_type"],
            "value": setting["value"]
        }

def migrate_chat(old_chat_id, new_chat_id):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_collection.update_many(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )

__load_chat_blacklists()
__load_chat_settings_blacklists()