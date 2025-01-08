import threading
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
from Mikobot.plugins.helper_funcs.msg_types import Types

from .afk_db import dbnames as db

notes_collection = db['notes']
buttons_collection = db['buttons']

# Create indexes
notes_collection.create_index([("chat_id", ASCENDING), ("name", ASCENDING)], unique=True)
buttons_collection.create_index([("chat_id", ASCENDING), ("note_name", ASCENDING)])

NOTES_INSERTION_LOCK = threading.RLock()
BUTTONS_INSERTION_LOCK = threading.RLock()

def add_note_to_db(chat_id, note_name, note_data, msgtype, buttons=None, file=None):
    if not buttons:
        buttons = []

    with NOTES_INSERTION_LOCK:
        chat_id = str(chat_id)
        note = {
            "chat_id": chat_id,
            "name": note_name,
            "value": note_data or "",
            "msgtype": msgtype.value,
            "file": file,
            "is_reply": False,
            "has_buttons": bool(buttons)
        }

        notes_collection.update_one(
            {"chat_id": chat_id, "name": note_name},
            {"$set": note},
            upsert=True
        )

        buttons_collection.delete_many({"chat_id": chat_id, "note_name": note_name})

        for b_name, url, same_line in buttons:
            add_note_button_to_db(chat_id, note_name, b_name, url, same_line)

def get_note(chat_id, note_name):
    return notes_collection.find_one(
        {"chat_id": str(chat_id), "name": {"$regex": f"^{note_name}$", "$options": "i"}}
    )

def rm_note(chat_id, note_name):
    with NOTES_INSERTION_LOCK:
        chat_id = str(chat_id)
        note = notes_collection.find_one_and_delete(
            {"chat_id": chat_id, "name": {"$regex": f"^{note_name}$", "$options": "i"}}
        )
        if note:
            with BUTTONS_INSERTION_LOCK:
                buttons_collection.delete_many({"chat_id": chat_id, "note_name": note_name})
            return True
        return False

def get_all_chat_notes(chat_id):
    return list(notes_collection.find({"chat_id": str(chat_id)}).sort("name", ASCENDING))

def add_note_button_to_db(chat_id, note_name, b_name, url, same_line):
    with BUTTONS_INSERTION_LOCK:
        button = {
            "chat_id": str(chat_id),
            "note_name": note_name,
            "name": b_name,
            "url": url,
            "same_line": same_line
        }
        buttons_collection.insert_one(button)

def get_buttons(chat_id, note_name):
    return list(buttons_collection.find(
        {"chat_id": str(chat_id), "note_name": note_name}
    ).sort("_id", ASCENDING))

def num_notes():
    return notes_collection.count_documents({})

def num_chats():
    return len(notes_collection.distinct("chat_id"))

def migrate_chat(old_chat_id, new_chat_id):
    with NOTES_INSERTION_LOCK:
        old_chat_id, new_chat_id = str(old_chat_id), str(new_chat_id)
        notes_collection.update_many(
            {"chat_id": old_chat_id},
            {"$set": {"chat_id": new_chat_id}}
        )
        
        with BUTTONS_INSERTION_LOCK:
            buttons_collection.update_many(
                {"chat_id": old_chat_id},
                {"$set": {"chat_id": new_chat_id}}
            )

