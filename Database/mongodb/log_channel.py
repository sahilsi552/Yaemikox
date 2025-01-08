import threading
import typing
from pymongo import MongoClient

from .afk_db import dbnames as db
log_channel_setting=db['log_channel_setting']

LOGS_INSERTION_LOCK = threading.RLock()
LOG_SETTING_LOCK = threading.RLock()
CHANNELS = {}

class LogChannelSettings:
    def __init__(self, chat_id: int, log_join: bool, log_leave: bool, log_warn: bool, log_action: bool, log_report: bool):
        self.chat_id = chat_id
        self.log_warn = log_warn
        self.log_joins = log_join
        self.log_leave = log_leave
        self.log_report = log_report
        self.log_action = log_action

    def toggle_warn(self) -> bool:
        self.log_warn = not self.log_warn
        log_channel_setting.update_one({"chat_id": self.chat_id}, {"$set": {"log_warn": self.log_warn}})
        return self.log_warn

    def toggle_joins(self) -> bool:
        self.log_joins = not self.log_joins
        log_channel_setting.update_one({"chat_id": self.chat_id}, {"$set": {"log_joins": self.log_joins}})
        return self.log_joins

    def toggle_leave(self) -> bool:
        self.log_leave = not self.log_leave
        log_channel_setting.update_one({"chat_id": self.chat_id}, {"$set": {"log_leave": self.log_leave}})
        return self.log_leave

    def toggle_report(self) -> bool:
        self.log_report = not self.log_report
        log_channel_setting.update_one({"chat_id": self.chat_id}, {"$set": {"log_report": self.log_report}})
        return self.log_report

    def toggle_action(self) -> bool:
        self.log_action = not self.log_action
        log_channel_setting.update_one({"chat_id": self.chat_id}, {"$set": {"log_action": self.log_action}})
        return self.log_action

def get_chat_setting(chat_id: int) -> typing.Optional[LogChannelSettings]:
    with LOG_SETTING_LOCK:
        setting = log_channel_setting.find_one({"chat_id": chat_id})
        if setting:
            return LogChannelSettings(
                chat_id=setting["chat_id"],
                log_join=setting["log_joins"],
                log_leave=setting["log_leave"],
                log_warn=setting["log_warn"],
                log_action=setting["log_action"],
                log_report=setting["log_report"]
            )
        return None

def set_chat_setting(setting: LogChannelSettings):
    with LOGS_INSERTION_LOCK:
        log_channel_setting.update_one(
            {"chat_id": setting.chat_id},
            {"$set": {
                "log_warn": setting.log_warn,
                "log_action": setting.log_action,
                "log_report": setting.log_report,
                "log_joins": setting.log_joins,
                "log_leave": setting.log_leave
            }},
            upsert=True
        )

def set_chat_log_channel(chat_id, log_channel):
    with LOGS_INSERTION_LOCK:
        log_channel_setting.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"log_channel": log_channel}},
            upsert=True
        )
        CHANNELS[str(chat_id)] = log_channel

def get_chat_log_channel(chat_id):
    return CHANNELS.get(str(chat_id))

def stop_chat_logging(chat_id):
    with LOGS_INSERTION_LOCK:
        result = log_channel_setting.find_one_and_delete({"chat_id": str(chat_id)})
        if result:
            if str(chat_id) in CHANNELS:
                del CHANNELS[str(chat_id)]
            return result["log_channel"]

def num_logchannels():
    return len(log_channel_setting.distinct("chat_id"))

def migrate_chat(old_chat_id, new_chat_id):
    with LOGS_INSERTION_LOCK:
        log_channel_setting.update_one(
            {"chat_id": str(old_chat_id)},
            {"$set": {"chat_id": str(new_chat_id)}}
        )
        if str(old_chat_id) in CHANNELS:
            CHANNELS[str(new_chat_id)] = CHANNELS.get(str(old_chat_id))

def __load_log_channels():
    global CHANNELS
    all_chats = log_channel_setting.find()
    CHANNELS = {chat["chat_id"]: chat["log_channel"] for chat in all_chats}

__load_log_channels()