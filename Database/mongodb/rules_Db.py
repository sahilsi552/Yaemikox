import threading

from .afk_db import dbnames as db

db_rules=db['rules']



INSERTION_LOCK = threading.RLock()

def set_rules(chat_id, rules_text):
    with INSERTION_LOCK:
        rules = db_rules.find_one({"chat_id": str(chat_id)})
        if not rules:
            rules = {"chat_id": str(chat_id), "rules": rules_text}
        else:
            rules["rules"] = rules_text

        db_rules.update_one(
            {"chat_id": str(chat_id)},
            {"$set": rules},
            upsert=True
        )

def get_rules(chat_id):
    rules = db_rules.find_one({"chat_id": str(chat_id)})
    if rules:
        return rules["rules"]
    return ""

def num_chats():
    return len(db_rules.distinct("chat_id"))

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        db_rules.update_one(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )