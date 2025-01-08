import threading
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId

from .afk_db import dbnames as db
gbanned_users = db['gbanned_users']
gban_settings = db['gban_settings']

# Create indexes
gbanned_users.create_index([("user_id", ASCENDING)], unique=True)
gban_settings.create_index([("chat_id", ASCENDING)], unique=True)

GBANNED_USERS_LOCK = threading.RLock()
GBAN_SETTING_LOCK = threading.RLock()
GBANNED_LIST = set()
GBANSTAT_LIST = set()

def gban_user(user_id, name, reason=None):
    with GBANNED_USERS_LOCK:
        gbanned_users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "reason": reason}},
            upsert=True
        )
        __load_gbanned_userid_list()

def update_gban_reason(user_id, name, reason=None):
    with GBANNED_USERS_LOCK:
        user = gbanned_users.find_one({"user_id": user_id})
        if not user:
            return None
        old_reason = user.get("reason")
        gbanned_users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "reason": reason}}
        )
        return old_reason

def ungban_user(user_id):
    with GBANNED_USERS_LOCK:
        gbanned_users.delete_one({"user_id": user_id})
        __load_gbanned_userid_list()

def is_user_gbanned(user_id):
    return user_id in GBANNED_LIST

def get_gbanned_user(user_id):
    return gbanned_users.find_one({"user_id": user_id})

def get_gban_list():
    return list(gbanned_users.find({}, {"_id": 0}))

def enable_gbans(chat_id):
    with GBAN_SETTING_LOCK:
        gban_settings.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"setting": True}},
            upsert=True
        )
        if str(chat_id) in GBANSTAT_LIST:
            GBANSTAT_LIST.remove(str(chat_id))

def disable_gbans(chat_id):
    with GBAN_SETTING_LOCK:
        gban_settings.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"setting": False}},
            upsert=True
        )
        GBANSTAT_LIST.add(str(chat_id))

def does_chat_gban(chat_id):
    return str(chat_id) not in GBANSTAT_LIST

def num_gbanned_users():
    return len(GBANNED_LIST)

def __load_gbanned_userid_list():
    global GBANNED_LIST
    GBANNED_LIST = set(user["user_id"] for user in gbanned_users.find({}, {"user_id": 1}))

def __load_gban_stat_list():
    global GBANSTAT_LIST
    GBANSTAT_LIST = set(
        chat["chat_id"] for chat in gban_settings.find({"setting": False}, {"chat_id": 1})
    )

def migrate_chat(old_chat_id, new_chat_id):
    with GBAN_SETTING_LOCK:
        gban_settings.update_one(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )

# Create in memory userid to avoid disk access
__load_gbanned_userid_list()
__load_gban_stat_list()

