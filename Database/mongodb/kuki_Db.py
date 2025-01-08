import threading
from pymongo import MongoClient

from .afk_db import dbnames as db

kuki_chats = db["kuki_chats"]

INSERTION_LOCK = threading.RLock()

def is_kuki(chat_id):
    chat = kuki_chats.find_one({"chat_id": str(chat_id)})
    return bool(chat)

def set_kuki(chat_id):
    with INSERTION_LOCK:
        kukichat = kuki_chats.find_one({"chat_id": str(chat_id)})
        if not kukichat:
            kuki_chats.insert_one({"chat_id": str(chat_id)})

def rem_kuki(chat_id):
    with INSERTION_LOCK:
        kuki_chats.delete_one({"chat_id": str(chat_id)})