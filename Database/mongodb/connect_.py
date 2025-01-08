import threading
import time
from typing import Union
from pymongo import MongoClient
from pymongo.collection import Collection

from .afk_db import dbnames as db

chat_access_settings: Collection = db['chat_access_settings']
connections: Collection = db['connections']
connection_history: Collection = db['connection_history']

# Create indexes
chat_access_settings.create_index('chat_id', unique=True)
connections.create_index('user_id', unique=True)
connection_history.create_index([('user_id', 1), ('chat_id', 1)], unique=True)

CHAT_ACCESS_LOCK = threading.RLock()
CONNECTION_INSERTION_LOCK = threading.RLock()
CONNECTION_HISTORY_LOCK = threading.RLock()

HISTORY_CONNECT = {}

def allow_connect_to_chat(chat_id: Union[str, int]) -> bool:
    chat_setting = chat_access_settings.find_one({'chat_id': str(chat_id)})
    return chat_setting['allow_connect_to_chat'] if chat_setting else False

def set_allow_connect_to_chat(chat_id: Union[int, str], setting: bool):
    with CHAT_ACCESS_LOCK:
        chat_access_settings.update_one(
            {'chat_id': str(chat_id)},
            {'$set': {'allow_connect_to_chat': setting}},
            upsert=True
        )

def connect(user_id: int, chat_id: str):
    with CONNECTION_INSERTION_LOCK:
        connections.update_one(
            {'user_id': user_id},
            {'$set': {'chat_id': str(chat_id)}},
            upsert=True
        )
        return True

def get_connected_chat(user_id: int):
    return connections.find_one({'user_id': user_id})

def curr_connection(chat_id: str):
    return connections.find_one({'chat_id': str(chat_id)})

def disconnect(user_id: int):
    with CONNECTION_INSERTION_LOCK:
        result = connections.delete_one({'user_id': user_id})
        return result.deleted_count > 0

def add_history_conn(user_id: int, chat_id: str, chat_name: str):
    global HISTORY_CONNECT
    with CONNECTION_HISTORY_LOCK:
        conn_time = int(time.time())
        if user_id in HISTORY_CONNECT:
            count = connection_history.count_documents({'user_id': user_id})
            if count >= 5:
                oldest = connection_history.find_one(
                    {'user_id': user_id},
                    sort=[('conn_time', 1)]
                )
                if oldest:
                    connection_history.delete_one({'_id': oldest['_id']})
                    HISTORY_CONNECT[user_id].pop(min(HISTORY_CONNECT[user_id].keys()))

        connection_history.update_one(
            {'user_id': user_id, 'chat_id': str(chat_id)},
            {'$set': {
                'chat_name': chat_name,
                'conn_time': conn_time
            }},
            upsert=True
        )

        if user_id not in HISTORY_CONNECT:
            HISTORY_CONNECT[user_id] = {}
        HISTORY_CONNECT[user_id][conn_time] = {
            'chat_name': chat_name,
            'chat_id': str(chat_id)
        }

def get_history_conn(user_id: int):
    if user_id not in HISTORY_CONNECT:
        HISTORY_CONNECT[user_id] = {}
    return HISTORY_CONNECT[user_id]

def clear_history_conn(user_id: int):
    global HISTORY_CONNECT
    connection_history.delete_many({'user_id': user_id})
    HISTORY_CONNECT[user_id] = {}
    return True

def __load_user_history():
    global HISTORY_CONNECT
    HISTORY_CONNECT = {}
    for doc in connection_history.find():
        user_id = doc['user_id']
        if user_id not in HISTORY_CONNECT:
            HISTORY_CONNECT[user_id] = {}
        HISTORY_CONNECT[user_id][doc['conn_time']] = {
            'chat_name': doc['chat_name'],
            'chat_id': doc['chat_id']
        }

__load_user_history()

