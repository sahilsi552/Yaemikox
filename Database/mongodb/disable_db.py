import threading
from pymongo import MongoClient

from .afk_db import dbnames as db
disabled_commandsdb= db['disabled_commands']
DISABLE_INSERTION_LOCK = threading.RLock()
DISABLED = {}

def disable_command(chat_id, disable):
    with DISABLE_INSERTION_LOCK:
        disabled = disabled_commandsdb.find_one({"chat_id": str(chat_id), "command": disable})

        if not disabled:
            DISABLED.setdefault(str(chat_id), set()).add(disable)

            disabled = {"chat_id": str(chat_id), "command": disable}
            disabled_commandsdb.insert_one(disabled)
            return True
        return False

def enable_command(chat_id, enable):
    with DISABLE_INSERTION_LOCK:
        result = disabled_commandsdb.delete_one({"chat_id": str(chat_id), "command": enable})

        if result.deleted_count > 0:
            if enable in DISABLED.get(str(chat_id)):  # sanity check
                DISABLED.setdefault(str(chat_id), set()).remove(enable)
            return True
        return False

def is_command_disabled(chat_id, cmd):
    return str(cmd).lower() in DISABLED.get(str(chat_id), set())

def get_all_disabled(chat_id):
    return DISABLED.get(str(chat_id), set())

def num_chats():
    return len(disabled_commandsdb.distinct("chat_id"))

def num_disabled():
    return disabled_commandsdb.count_documents({})

def migrate_chat(old_chat_id, new_chat_id):
    with DISABLE_INSERTION_LOCK:
        disabled_commandsdb.update_many(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )

        if str(old_chat_id) in DISABLED:
            DISABLED[str(new_chat_id)] = DISABLED.get(str(old_chat_id), set())

def __load_disabled_commands():
    global DISABLED
    all_chats = disabled_commandsdb.find()
    for chat in all_chats:
        DISABLED.setdefault(chat["chat_id"], set()).add(chat["command"])

__load_disabled_commands()