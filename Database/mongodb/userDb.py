import threading
from pymongo import MongoClient

from .afk_db import dbnames as db

from Mikobot import dispatcher
users_db = db["users"]
INSERTION_LOCK = threading.RLock()

def ensure_bot_in_db():
    with INSERTION_LOCK:
        bot = {"user_id": dispatcher.bot.id, "username": dispatcher.bot.username}
        users_db.update_one({"user_id": dispatcher.bot.id}, {"$set": bot}, upsert=True)

def update_user(user_id, username, chat_id=None, chat_name=None):
    with INSERTION_LOCK:
        user = users_db.find_one({"user_id": user_id})
        if not user:
            user = {"user_id": user_id, "username": username}
            users_db.insert_one(user)
        else:
            users_db.update_one({"user_id": user_id}, {"$set": {"username": username}})

        if not chat_id or not chat_name:
            return

        chat = db.chats.find_one({"chat_id": str(chat_id)})
        if not chat:
            chat = {"chat_id": str(chat_id), "chat_name": chat_name}
            db.chats.insert_one(chat)
        else:
            db.chats.update_one({"chat_id": str(chat_id)}, {"$set": {"chat_name": chat_name}})

        member = db.chat_members.find_one({"chat": str(chat_id), "user": user_id})
        if not member:
            chat_member = {"chat": str(chat_id), "user": user_id}
            db.chat_members.insert_one(chat_member)

def get_userid_by_name(username):
    return list(users_db.find({"username": {"$regex": f"^{username}$", "$options": "i"}}))

def get_name_by_userid(user_id):
    return users_db.find_one({"user_id": int(user_id)})

def get_chat_members(chat_id):
    return list(db.chat_members.find({"chat": str(chat_id)}))

def get_all_chats():
    return list(db.chats.find())

def get_all_users():
    return list(users_db.find())

def get_user_num_chats(user_id):
    return db.chat_members.count_documents({"user": int(user_id)})

def get_user_com_chats(user_id):
    chat_members = list(db.chat_members.find({"user": int(user_id)}))
    return [i["chat"] for i in chat_members]

def num_chats():
    return db.chats.count_documents({})

def num_users():
    return users_db.count_documents({})

def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        db.chats.update_one({"chat_id": str(old_chat_id)}, {"$set": {"chat_id": str(new_chat_id)}})
        db.chat_members.update_many({"chat": str(old_chat_id)}, {"$set": {"chat": str(new_chat_id)}})

ensure_bot_in_db()

def del_user(user_id):
    with INSERTION_LOCK:
        result = users_db.delete_one({"user_id": user_id})
        if result.deleted_count > 0:
            db.chat_members.delete_many({"user": user_id})
            return True
    return False

def rem_chat(chat_id):
    with INSERTION_LOCK:
        result = db.chats.delete_one({"chat_id": str(chat_id)})
        if result.deleted_count == 0:
            return False
        db.chat_members.delete_many({"chat": str(chat_id)})