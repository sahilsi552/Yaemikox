import threading
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from Mikobot.plugins.helper_funcs.msg_types import Types

from .afk_db import dbnames as db
custom_filters = db['custom_filters']
buttonsdb = db['buttonsdb']

# Create indexes
custom_filters.create_index([("chat_id", 1), ("keyword", 1)], unique=True)
buttonsdb.create_index([("chat_id", 1), ("keyword", 1)])

CUST_FILT_LOCK = threading.RLock()
BUTTON_LOCK = threading.RLock()
CHAT_FILTERS = {}

def get_all_filters():
    return list(custom_filters.find())

def add_filter(
    chat_id,
    keyword,
    reply,
    is_sticker=False,
    is_document=False,
    is_image=False,
    is_audio=False,
    is_voice=False,
    is_video=False,
    buttons=None
):
    global CHAT_FILTERS

    if buttons is None:
        buttons = []

    with CUST_FILT_LOCK:
        chat_id = str(chat_id)
        custom_filters.delete_one({"chat_id": chat_id, "keyword": keyword})
        buttonsdb.delete_many({"chat_id": chat_id, "keyword": keyword})

        filt = {
            "chat_id": chat_id,
            "keyword": keyword,
            "reply": reply,
            "is_sticker": is_sticker,
            "is_document": is_document,
            "is_image": is_image,
            "is_audio": is_audio,
            "is_voice": is_voice,
            "is_video": is_video,
            "has_buttons": bool(buttons),
            "has_markdown": True
        }

        custom_filters.insert_one(filt)

        if chat_id not in CHAT_FILTERS:
            CHAT_FILTERS[chat_id] = []
        if keyword not in CHAT_FILTERS[chat_id]:
            CHAT_FILTERS[chat_id].append(keyword)
            CHAT_FILTERS[chat_id].sort(key=lambda x: (-len(x), x))

    for b_name, url, same_line in buttons:
        add_note_button_to_db(chat_id, keyword, b_name, url, same_line)

def new_add_filter(
    chat_id, keyword, reply_text, file_type, file_id, buttons, media_spoiler
):
    global CHAT_FILTERS

    if buttons is None:
        buttons = []

    with CUST_FILT_LOCK:
        chat_id = str(chat_id)
        custom_filters.delete_one({"chat_id": chat_id, "keyword": keyword})
        buttonsdb.delete_many({"chat_id": chat_id, "keyword": keyword})

        filt = {
            "chat_id": chat_id,
            "keyword": keyword,
            "reply": "there is should be a new reply",
            "is_sticker": False,
            "is_document": False,
            "is_image": False,
            "is_audio": False,
            "is_voice": False,
            "is_video": False,
            "has_buttons": bool(buttons),
            "reply_text": reply_text,
            "file_type": file_type.value,
            "file_id": file_id
        }

        custom_filters.insert_one(filt)

        if chat_id not in CHAT_FILTERS:
            CHAT_FILTERS[chat_id] = []
        if keyword not in CHAT_FILTERS[chat_id]:
            CHAT_FILTERS[chat_id].append(keyword)
            CHAT_FILTERS[chat_id].sort(key=lambda x: (-len(x), x))

    for b_name, url, same_line in buttons:
        add_note_button_to_db(chat_id, keyword, b_name, url, same_line)

def remove_filter(chat_id, keyword):
    global CHAT_FILTERS
    with CUST_FILT_LOCK:
        chat_id = str(chat_id)
        filt = custom_filters.find_one_and_delete({"chat_id": chat_id, "keyword": keyword})
        if filt:
            if chat_id in CHAT_FILTERS and keyword in CHAT_FILTERS[chat_id]:
                CHAT_FILTERS[chat_id].remove(keyword)
            buttonsdb.delete_many({"chat_id": chat_id, "keyword": keyword})
            return True
        return False

def get_chat_triggers(chat_id):
    return set(CHAT_FILTERS.get(str(chat_id), []))

def get_chat_filters(chat_id):
    return list(custom_filters.find({"chat_id": str(chat_id)}).sort([("keyword", 1)]))

def get_filter(chat_id, keyword):
    return custom_filters.find_one({"chat_id": str(chat_id), "keyword": keyword})

def add_note_button_to_db(chat_id, keyword, b_name, url, same_line):
    with BUTTON_LOCK:
        button = {
            "chat_id": str(chat_id),
            "keyword": keyword,
            "name": b_name,
            "url": url,
            "same_line": same_line
        }
        buttonsdb.insert_one(button)

def get_buttons(chat_id, keyword):
    return list(buttonsdb.find({"chat_id": str(chat_id), "keyword": keyword}).sort("_id", 1))

def num_filters():
    return custom_filters.count_documents({})

def num_chats():
    return len(custom_filters.distinct("chat_id"))

def __load_chat_filters():
    global CHAT_FILTERS
    CHAT_FILTERS = {}
    all_filters = list(custom_filters.find())
    for x in all_filters:
        chat_id = x['chat_id']
        if chat_id not in CHAT_FILTERS:
            CHAT_FILTERS[chat_id] = []
        CHAT_FILTERS[chat_id].append(x['keyword'])
    
    for chat_id, keywords in CHAT_FILTERS.items():
        CHAT_FILTERS[chat_id] = sorted(set(keywords), key=lambda x: (-len(x), x))

def __migrate_filters():
    all_filters = list(custom_filters.find())
    for x in all_filters:
        if x.get('is_document'):
            file_type = Types.DOCUMENT
        elif x.get('is_image'):
            file_type = Types.PHOTO
        elif x.get('is_video'):
            file_type = Types.VIDEO
        elif x.get('is_sticker'):
            file_type = Types.STICKER
        elif x.get('is_audio'):
            file_type = Types.AUDIO
        elif x.get('is_voice'):
            file_type = Types.VOICE
        else:
            file_type = Types.TEXT

        print(str(x['chat_id']), x['keyword'], x['reply'], file_type.value)
        if file_type == Types.TEXT:
            filt = {
                "chat_id": str(x['chat_id']),
                "keyword": x['keyword'],
                "reply": x['reply'],
                "file_type": file_type.value,
                "file_id": None
            }
        else:
            filt = {
                "chat_id": str(x['chat_id']),
                "keyword": x['keyword'],
                "reply": None,
                "file_type": file_type.value,
                "file_id": x['reply']
            }
        
        custom_filters.update_one({"_id": x["_id"]}, {"$set": filt}, upsert=True)

def migrate_chat(old_chat_id, new_chat_id):
    with CUST_FILT_LOCK:
        old_chat_id, new_chat_id = str(old_chat_id), str(new_chat_id)
        custom_filters.update_many(
            {"chat_id": old_chat_id},
            {"$set": {"chat_id": new_chat_id}}
        )
        buttonsdb.update_many(
            {"chat_id": old_chat_id},
            {"$set": {"chat_id": new_chat_id}}
        )
        if old_chat_id in CHAT_FILTERS:
            CHAT_FILTERS[new_chat_id] = CHAT_FILTERS.pop(old_chat_id)

__load_chat_filters()