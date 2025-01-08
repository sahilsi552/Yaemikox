import threading
from pymongo import MongoClient

from .afk_db import dbnames as db

collection = db['blacklistusers']

BLACKLIST_LOCK = threading.RLock()
BLACKLIST_USERS = set()


def blacklist_user(user_id, reason=None):
    with BLACKLIST_LOCK:
        user = collection.find_one({"user_id": str(user_id)})
        if not user:
            collection.insert_one({"user_id": str(user_id), "reason": reason})
        else:
            collection.update_one({"user_id": str(user_id)}, {"reason": reason})

        __load_blacklist_userid_list()


def unblacklist_user(user_id):
    with BLACKLIST_LOCK:
        collection.delete_one({"user_id": str(user_id)})
        __load_blacklist_userid_list()


def get_reason(user_id):
    user = collection.find_one({"user_id": str(user_id)})
    return user["reason"] if user else ""


def is_user_blacklisted(user_id):
    return user_id in BLACKLIST_USERS


def __load_blacklist_userid_list():
    global BLACKLIST_USERS
    BLACKLIST_USERS = {int(x["user_id"]) for x in collection.find()}
    

__load_blacklist_userid_list()