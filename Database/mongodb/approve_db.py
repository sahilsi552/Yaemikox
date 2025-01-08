import threading
from .afk_db import dbnames
approvals_collection = dbnames['approval']  # Collection name

APPROVE_INSERTION_LOCK = threading.RLock()


class Approval:
    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = user_id

    def __repr__(self):
        return "<Approval %s>" % self.user_id


def approve(chat_id, user_id):
    with APPROVE_INSERTION_LOCK:
        approve_user = Approval(chat_id, user_id)
        approvals_collection.insert_one({'chat_id': approve_user.chat_id, 'user_id': approve_user.user_id})


def is_approved(chat_id, user_id):
    try:
        return approvals_collection.find_one({'chat_id': str(chat_id), 'user_id': user_id}) is not None
    finally:
        pass  # No explicit session to close in PyMongo


def disapprove(chat_id, user_id):
    with APPROVE_INSERTION_LOCK:
        result = approvals_collection.delete_one({'chat_id': str(chat_id), 'user_id': user_id})
        return result.deleted_count > 0


def list_approved(chat_id):
    try:
        return list(approvals_collection.find({'chat_id': str(chat_id)}).sort('user_id', 1))
    finally:
        pass  # No explicit session to close in PyMongo
