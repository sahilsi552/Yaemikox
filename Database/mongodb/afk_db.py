from Database.mongodb.db import dbname
import threading
from datetime import datetime
from pymongo import MongoClient

from Mikobot import DB_NAME, MONGO_DB_URI

syncmongo = MongoClient(MONGO_DB_URI)
dbnames = syncmongo[DB_NAME]

usersdb = dbname.users
cleandb = dbname.cleanmode
cleanmode = {}
afk_db = dbnames.afk_user  

INSERTION_LOCK = threading.RLock()
AFK_USERS = {}

async def is_cleanmode_on(chat_id: int) -> bool:
    mode = cleanmode.get(chat_id)
    if not mode:
        user = await cleandb.find_one({"chat_id": chat_id})
        if not user:
            cleanmode[chat_id] = True
            return True
        cleanmode[chat_id] = False
        return False
    return mode


async def cleanmode_on(chat_id: int):
    cleanmode[chat_id] = True
    user = await cleandb.find_one({"chat_id": chat_id})
    if user:
        return await cleandb.delete_one({"chat_id": chat_id})


async def cleanmode_off(chat_id: int):
    cleanmode[chat_id] = False
    user = await cleandb.find_one({"chat_id": chat_id})
    if not user:
        return await cleandb.insert_one({"chat_id": chat_id})

def is_afk(user_id):
    return user_id in AFK_USERS


def check_afk_status(user_id):
    user_data = afk_db.find_one({"user_id": user_id})
    return user_data


def set_afk(user_id, reason=""):
    with INSERTION_LOCK:
        curr = afk_db.find_one({"user_id": user_id})
        now = datetime.now()

        if not curr:
            curr = {
                "user_id": user_id,
                "reason": reason,
                "is_afk": True,
                "time": now
            }
            afk_db.insert_one(curr)
        else:
            curr["is_afk"] = True
            curr["reason"] = reason
            curr["time"] = now
            afk_db.replace_one({"user_id": user_id}, curr)

        AFK_USERS[user_id] = {"reason": reason, "time": now}


def rm_afk(user_id):
    with INSERTION_LOCK:
        curr = afk_db.find_one({"user_id": user_id})
        if curr:
            if user_id in AFK_USERS:  # sanity check
                del AFK_USERS[user_id]

            afk_db.delete_one({"user_id": user_id})
            return True
        return False


def toggle_afk(user_id, reason=""):
    with INSERTION_LOCK:
        curr = afk_db.find_one({"user_id": user_id})
        now = datetime.now()

        if not curr:
            curr = {
                "user_id": user_id,
                "reason": reason,
                "is_afk": True,
                "time": now
            }
            afk_db.insert_one(curr)
        else:
            curr["is_afk"] = not curr["is_afk"]
            if curr["is_afk"]:  # if toggled to AFK
                curr["reason"] = reason
                curr["time"] = now

            afk_db.replace_one({"user_id": user_id}, curr)

        
def __load_afk_users():
    global AFK_USERS
    all_afk = afk_db.find({"is_afk": True})
    AFK_USERS = {
        user["user_id"]: {"reason": user["reason"], "time": user["time"]}
        for user in all_afk
    }

__load_afk_users()
