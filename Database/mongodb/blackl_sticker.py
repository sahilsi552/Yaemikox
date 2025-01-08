from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import threading

from .afk_db import dbnames as db
stickers_collection = db['stickers']

# Create indexes
stickers_collection.create_index([("chat_id", 1), ("trigger", 1)], unique=True)
stickers_collection.create_index([("chat_id", 1), ("type", 1)], unique=True)

STICKERS_FILTER_INSERTION_LOCK = threading.RLock()
STICKSET_FILTER_INSERTION_LOCK = threading.RLock()

CHAT_STICKERS = {}
CHAT_BLSTICK_BLACKLISTS = {}

def add_to_stickers(chat_id, trigger):
    with STICKERS_FILTER_INSERTION_LOCK:
        try:
            stickers_collection.insert_one({
                "chat_id": str(chat_id),
                "trigger": trigger,
                "type": "filter"
            })
            if str(chat_id) not in CHAT_STICKERS:
                CHAT_STICKERS[str(chat_id)] = set()
            CHAT_STICKERS[str(chat_id)].add(trigger)
        except DuplicateKeyError:
            pass  # The document already exists

def rm_from_stickers(chat_id, trigger):
    with STICKERS_FILTER_INSERTION_LOCK:
        result = stickers_collection.delete_one({
            "chat_id": str(chat_id),
            "trigger": trigger,
            "type": "filter"
        })
        if result.deleted_count > 0:
            if trigger in CHAT_STICKERS.get(str(chat_id), set()):
                CHAT_STICKERS[str(chat_id)].remove(trigger)
            return True
        return False

def get_chat_stickers(chat_id):
    return CHAT_STICKERS.get(str(chat_id), set())

def num_stickers_filters():
    return stickers_collection.count_documents({"type": "filter"})

def num_stickers_chat_filters(chat_id):
    return stickers_collection.count_documents({"chat_id": str(chat_id), "type": "filter"})

def num_stickers_filter_chats():
    return len(stickers_collection.distinct("chat_id", {"type": "filter"}))

def set_blacklist_strength(chat_id, blacklist_type, value):
    with STICKSET_FILTER_INSERTION_LOCK:
        stickers_collection.update_one(
            {"chat_id": str(chat_id), "type": "setting"},
            {"$set": {"blacklist_type": int(blacklist_type), "value": str(value)}},
            upsert=True
        )
        CHAT_BLSTICK_BLACKLISTS[str(chat_id)] = {
            "blacklist_type": int(blacklist_type),
            "value": value,
        }

def get_blacklist_setting(chat_id):
    setting = CHAT_BLSTICK_BLACKLISTS.get(str(chat_id))
    if setting:
        return setting["blacklist_type"], setting["value"]
    return 1, "0"

def __load_CHAT_STICKERS():
    global CHAT_STICKERS
    for doc in stickers_collection.find({"type": "filter"}):
        chat_id = doc["chat_id"]
        if chat_id not in CHAT_STICKERS:
            CHAT_STICKERS[chat_id] = set()
        CHAT_STICKERS[chat_id].add(doc["trigger"])

def __load_chat_stickerset_blacklists():
    global CHAT_BLSTICK_BLACKLISTS
    for doc in stickers_collection.find({"type": "setting"}):
        CHAT_BLSTICK_BLACKLISTS[doc["chat_id"]] = {
            "blacklist_type": doc["blacklist_type"],
            "value": doc["value"],
        }

def migrate_chat(old_chat_id, new_chat_id):
    with STICKERS_FILTER_INSERTION_LOCK:
        stickers_collection.update_many(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )

__load_CHAT_STICKERS()
__load_chat_stickerset_blacklists()