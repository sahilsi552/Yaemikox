

import threading
from pymongo import MongoClient

from .afk_db import dbnames as db
permissions=db['permissions']

PERM_LOCK = threading.RLock()
RESTR_LOCK = threading.RLock()

def init_permissions(chat_id, reset=False):
    with PERM_LOCK:
        if reset:
            permissions.delete_one({"chat_id": str(chat_id)})
        perm = {
            "chat_id": str(chat_id),
            "audio": False,
            "voice": False,
            "contact": False,
            "video": False,
            "document": False,
            "photo": False,
            "sticker": False,
            "gif": False,
            "url": False,
            "bots": False,
            "forward": False,
            "game": False,
            "location": False,
            "rtl": False,
            "button": False,
            "egame": False,
            "inline": False
        }
        permissions.update_one({"chat_id": str(chat_id)}, {"$set": perm}, upsert=True)
        return perm

def init_restrictions(chat_id, reset=False):
    with RESTR_LOCK:
        if reset:
            db.restrictions.delete_one({"chat_id": str(chat_id)})
        restr = {
            "chat_id": str(chat_id),
            "messages": False,
            "media": False,
            "other": False,
            "preview": False
        }
        db.restrictions.update_one({"chat_id": str(chat_id)}, {"$set": restr}, upsert=True)
        return restr

def update_lock(chat_id, lock_type, locked):
    with PERM_LOCK:
        curr_perm = permissions.find_one({"chat_id": str(chat_id)})
        if not curr_perm:
            curr_perm = init_permissions(chat_id)

        curr_perm[lock_type] = locked
        permissions.update_one({"chat_id": str(chat_id)}, {"$set": curr_perm}, upsert=True)

def update_restriction(chat_id, restr_type, locked):
    with RESTR_LOCK:
        curr_restr = db.restrictions.find_one({"chat_id": str(chat_id)})
        if not curr_restr:
            curr_restr = init_restrictions(chat_id)

        if restr_type == "all":
            curr_restr["messages"] = locked
            curr_restr["media"] = locked
            curr_restr["other"] = locked
            curr_restr["preview"] = locked
        else:
            curr_restr[restr_type] = locked

        db.restrictions.update_one({"chat_id": str(chat_id)}, {"$set": curr_restr}, upsert=True)

def is_locked(chat_id, lock_type):
    curr_perm = permissions.find_one({"chat_id": str(chat_id)})
    if not curr_perm:
        return False
    return curr_perm.get(lock_type, False)

def is_restr_locked(chat_id, lock_type):
    curr_restr = db.restrictions.find_one({"chat_id": str(chat_id)})
    if not curr_restr:
        return False
    if lock_type == "all":
        return curr_restr["messages"] and curr_restr["media"] and curr_restr["other"] and curr_restr["preview"]
    return curr_restr.get(lock_type, False)

def get_locks(chat_id):
    return permissions.find_one({"chat_id": str(chat_id)})

def get_restr(chat_id):
    return db.restrictions.find_one({"chat_id": str(chat_id)})

def migrate_chat(old_chat_id, new_chat_id):
    with PERM_LOCK:
        permissions.update_one(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )

    with RESTR_LOCK:
        db.restrictions.update_one(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )