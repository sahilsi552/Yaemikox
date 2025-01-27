import ast
import threading
from pymongo import MongoClient
from telegram.error import BadRequest, Forbidden
from Mikobot import dispatcher

from .afk_db import dbnames as db
fed_db= db['feds']
chat_feds = db['chat_feds']
bans_feds = db['bans_feds']
feds_subs = db['feds_subs']

FEDS_LOCK = threading.RLock()
CHAT_FEDS_LOCK = threading.RLock()
FEDS_SETTINGS_LOCK = threading.RLock()
FEDS_SUBSCRIBER_LOCK = threading.RLock()

FEDERATION_BYNAME = {}
FEDERATION_BYOWNER = {}
FEDERATION_BYFEDID = {}

FEDERATION_CHATS = {}
FEDERATION_CHATS_BYID = {}

FEDERATION_BANNED_FULL = {}
FEDERATION_BANNED_USERID = {}

FEDERATION_NOTIFICATION = {}
FEDS_SUBSCRIBER = {}
MYFEDS_SUBSCRIBER = {}



def get_fed_info(fed_id):
    return FEDERATION_BYFEDID.get(str(fed_id), False)

def get_fed_id(chat_id):
    get = FEDERATION_CHATS.get(str(chat_id))
    return get["fid"] if get else False

def get_fed_name(chat_id):
    get = FEDERATION_CHATS.get(str(chat_id))
    return get["chat_name"] if get else False

def get_user_fban(fed_id, user_id):
    user_info = FEDERATION_BANNED_FULL.get(fed_id, {}).get(user_id)
    if not user_info:
        return None, None, None
    return user_info["first_name"], user_info["reason"], user_info["time"]

def get_user_admin_fed_name(user_id):
    user_feds = []
    for f in FEDERATION_BYFEDID:
        if int(user_id) in ast.literal_eval(FEDERATION_BYFEDID[f]["fusers"])["members"]:
            user_feds.append(FEDERATION_BYFEDID[f]["fname"])
    return user_feds

def get_user_owner_fed_name(user_id):
    user_feds = []
    for f in FEDERATION_BYFEDID:
        if int(user_id) == int(FEDERATION_BYFEDID[f]["fusers"]["owner"]):
            user_feds.append(FEDERATION_BYFEDID[f]["fname"])
    return user_feds

def get_user_admin_fed_full(user_id):
    user_feds = []
    for f in FEDERATION_BYFEDID:
        if int(user_id) in ast.literal_eval(ast.literal_eval(FEDERATION_BYFEDID[f]["fusers"])["members"]):
            user_feds.append({"fed_id": f, "fed": FEDERATION_BYFEDID[f]})
    return user_feds

def get_user_owner_fed_full(user_id):
    user_feds = []
    for f in FEDERATION_BYFEDID:
        if int(user_id) == int(ast.literal_eval(FEDERATION_BYFEDID[f]["fusers"])["owner"]):
            user_feds.append({"fed_id": f, "fed": FEDERATION_BYFEDID[f]})
    return user_feds

def get_user_fbanlist(user_id):
    user_name = ""
    fedname = []
    for x in FEDERATION_BANNED_FULL:
        if user_id in FEDERATION_BANNED_FULL[x]:
            if user_name == "":
                user_name = FEDERATION_BANNED_FULL[x][user_id].get("first_name")
            fedname.append([x, FEDERATION_BANNED_FULL[x][user_id].get("reason")])
    return user_name, fedname

def new_fed(owner_id, fed_name, fed_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        fed = {
            "owner_id": str(owner_id),
            "fed_name": fed_name,
            "fed_id": str(fed_id),
            "fed_rules": "Rules is not set in this federation.",
            "fed_log": None,
            "fed_users": str({"owner": str(owner_id), "members": "[]"})
        }
        fed_db.insert_one(fed)
        FEDERATION_BYOWNER[str(owner_id)] = {
            "fid": str(fed_id),
            "fname": fed_name,
            "frules": "Rules is not set in this federation.",
            "flog": None,
            "fusers": str({"owner": str(owner_id), "members": "[]"})
        }
        FEDERATION_BYFEDID[str(fed_id)] = {
            "owner": str(owner_id),
            "fname": fed_name,
            "frules": "Rules is not set in this federation.",
            "flog": None,
            "fusers": str({"owner": str(owner_id), "members": "[]"})
        }
        FEDERATION_BYNAME[fed_name] = {
            "fid": str(fed_id),
            "owner": str(owner_id),
            "frules": "Rules is not set in this federation.",
            "flog": None,
            "fusers": str({"owner": str(owner_id), "members": "[]"})
        }
        return fed

def del_fed(fed_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME, FEDERATION_CHATS, FEDERATION_CHATS_BYID, FEDERATION_BANNED_USERID, FEDERATION_BANNED_FULL
        getcache = FEDERATION_BYFEDID.get(fed_id)
        if getcache is None:
            return False
        # Variables
        getfed = FEDERATION_BYFEDID.get(fed_id)
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        # Delete from cache
        FEDERATION_BYOWNER.pop(owner_id)
        FEDERATION_BYFEDID.pop(fed_id)
        FEDERATION_BYNAME.pop(fed_name)
        if FEDERATION_CHATS_BYID.get(fed_id):
            for x in FEDERATION_CHATS_BYID[fed_id]:
                chat_feds.delete_one({"chat_id": str(x)})
                FEDERATION_CHATS.pop(x)
            FEDERATION_CHATS_BYID.pop(fed_id)
        # Delete fedban users
        getall = FEDERATION_BANNED_USERID.get(fed_id)
        if getall:
            for x in getall:
                bans_feds.delete_one({"fed_id": fed_id, "user_id": str(x)})
        if FEDERATION_BANNED_USERID.get(fed_id):
            FEDERATION_BANNED_USERID.pop(fed_id)
        if FEDERATION_BANNED_FULL.get(fed_id):
            FEDERATION_BANNED_FULL.pop(fed_id)
        # Delete fedsubs
        getall = MYFEDS_SUBSCRIBER.get(fed_id)
        if getall:
            for x in getall:
                feds_subs.delete_one({"fed_id": fed_id, "fed_subs": str(x)})
        if FEDS_SUBSCRIBER.get(fed_id):
            FEDS_SUBSCRIBER.pop(fed_id)
        if MYFEDS_SUBSCRIBER.get(fed_id):
            MYFEDS_SUBSCRIBER.pop(fed_id)
        # Delete from database
        fed_db.delete_one({"fed_id": fed_id})
        return True

def rename_fed(fed_id, owner_id, newname):
    with FEDS_LOCK:
        global FEDERATION_BYFEDID, FEDERATION_BYOWNER, FEDERATION_BYNAME
        fed = fed_db.find_one({"fed_id": fed_id})
        if not fed:
            return False
        fed_db.update_one({"fed_id": fed_id}, {"$set": {"fed_name": newname}})
        # Update the dicts
        oldname = FEDERATION_BYFEDID[str(fed_id)]["fname"]
        tempdata = FEDERATION_BYNAME[oldname]
        FEDERATION_BYNAME.pop(oldname)
        FEDERATION_BYOWNER[str(owner_id)]["fname"] = newname
        FEDERATION_BYFEDID[str(fed_id)]["fname"] = newname
        FEDERATION_BYNAME[newname] = tempdata
        return True

def chat_join_fed(fed_id, chat_name, chat_id):
    with FEDS_LOCK:
        global FEDERATION_CHATS, FEDERATION_CHATS_BYID
        r = {"chat_id": chat_id, "chat_name": chat_name, "fed_id": fed_id}
        chat_feds.insert_one(r)
        FEDERATION_CHATS[str(chat_id)] = {"chat_name": chat_name, "fid": fed_id}
        checkid = FEDERATION_CHATS_BYID.get(fed_id)
        if checkid is None:
            FEDERATION_CHATS_BYID[fed_id] = []
        FEDERATION_CHATS_BYID[fed_id].append(str(chat_id))
        return r

def search_fed_by_name(fed_name):
    return FEDERATION_BYNAME.get(fed_name, False)

def search_user_in_fed(fed_id, user_id):
    getfed = FEDERATION_BYFEDID.get(fed_id)
    if getfed is None:
        return False
    getfed = ast.literal_eval(getfed["fusers"])["members"]
    return user_id in ast.literal_eval(getfed)

def user_demote_fed(fed_id, user_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        fed_rules = getfed["frules"]
        fed_log = getfed["flog"]
        # Temp set
        try:
            members = ast.literal_eval(ast.literal_eval(getfed["fusers"])["members"])
        except ValueError:
            return False
        members.remove(user_id)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]["fusers"] = str({"owner": str(owner_id), "members": str(members)})
        FEDERATION_BYFEDID[str(fed_id)]["fusers"] = str({"owner": str(owner_id), "members": str(members)})
        FEDERATION_BYNAME[fed_name]["fusers"] = str({"owner": str(owner_id), "members": str(members)})
        # Set on database
        fed_db.update_one({"fed_id": fed_id}, {"$set": {"fed_users": str({"owner": str(owner_id), "members": str(members)})}})
        return True

def user_join_fed(fed_id, user_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        fed_rules = getfed["frules"]
        fed_log = getfed["flog"]
        # Temp set
        members = ast.literal_eval(ast.literal_eval(getfed["fusers"])["members"])
        members.append(user_id)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]["fusers"] = str({"owner": str(owner_id), "members": str(members)})
        FEDERATION_BYFEDID[str(fed_id)]["fusers"] = str({"owner": str(owner_id), "members": str(members)})
        FEDERATION_BYNAME[fed_name]["fusers"] = str({"owner": str(owner_id), "members": str(members)})
        # Set on database
        fed_db.update_one({"fed_id": fed_id}, {"$set": {"fed_users": str({"owner": str(owner_id), "members": str(members)})}})
        __load_all_feds_chats()
        return True

def chat_leave_fed(chat_id):
    with FEDS_LOCK:
        global FEDERATION_CHATS, FEDERATION_CHATS_BYID
        # Set variables
        fed_info = FEDERATION_CHATS.get(str(chat_id))
        if fed_info is None:
            return False
        fed_id = fed_info["fid"]
        # Delete from cache
        FEDERATION_CHATS.pop(str(chat_id))
        FEDERATION_CHATS_BYID[str(fed_id)].remove(str(chat_id))
        # Delete from db
        chat_feds.delete_one({"chat_id": str(chat_id)})
        return True

def all_fed_chats(fed_id):
    return FEDERATION_CHATS_BYID.get(fed_id, [])

def all_fed_users(fed_id):
    getfed = FEDERATION_BYFEDID.get(str(fed_id))
    if getfed is None:
        return False
    fed_owner = getfed["fusers"]["owner"]
    fed_admins = getfed["fusers"]["members"]
    fed_admins.append(fed_owner)
    return fed_admins

def all_fed_members(fed_id):
    getfed = FEDERATION_BYFEDID.get(str(fed_id))
    return getfed["fusers"]["members"]

def set_frules(fed_id, rules):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        fed_members = getfed["fusers"]
        fed_rules = str(rules)
        fed_log = getfed["flog"]
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]["frules"] = fed_rules
        FEDERATION_BYFEDID[str(fed_id)]["frules"] = fed_rules
        FEDERATION_BYNAME[fed_name]["frules"] = fed_rules
        # Set on database
        fed_db.update_one({"fed_id": fed_id}, {"$set": {"fed_rules": fed_rules}})
        return True

def get_frules(fed_id):
    return FEDERATION_BYFEDID[str(fed_id)]["frules"]

def fban_user(fed_id, user_id, first_name, last_name, user_name, reason, time):
    with FEDS_LOCK:
        bans_feds.delete_many({"fed_id": fed_id, "user_id": str(user_id)})
        r = {
            "fed_id": str(fed_id),
            "user_id": str(user_id),
            "first_name": first_name,
            "last_name": last_name,
            "user_name": user_name,
            "reason": reason,
            "time": time
        }
        bans_feds.insert_one(r)
        __load_all_feds_banned()
        return r

def multi_fban_user(multi_fed_id, multi_user_id, multi_first_name, multi_last_name, multi_user_name, multi_reason):
    counter = 0
    time = 0
    for x in range(len(multi_fed_id)):
        fed_id = multi_fed_id[x]
        user_id = multi_user_id[x]
        first_name = multi_first_name[x]
        last_name = multi_last_name[x]
        user_name = multi_user_name[x]
        reason = multi_reason[x]
        bans_feds.delete_many({"fed_id": fed_id, "user_id": str(user_id)})
        r = {
            "fed_id": str(fed_id),
            "user_id": str(user_id),
            "first_name": first_name,
            "last_name": last_name,
            "user_name": user_name,
            "reason": reason,
            "time": time
        }
        bans_feds.insert_one(r)
        counter += 1
    __load_all_feds_banned()
    return counter

def un_fban_user(fed_id, user_id):
    with FEDS_LOCK:
        bans_feds.delete_many({"fed_id": fed_id, "user_id": str(user_id)})
        __load_all_feds_banned()
        return True

def get_fban_user(fed_id, user_id):
    list_fbanned = FEDERATION_BANNED_USERID.get(fed_id)
    if list_fbanned is None:
        FEDERATION_BANNED_USERID[fed_id] = []
    if user_id in FEDERATION_BANNED_USERID[fed_id]:
        r = bans_feds.find_one({"fed_id": fed_id, "user_id": str(user_id)})
        return True, r["reason"], r["time"]
    else:
        return False, None, None

def get_all_fban_users(fed_id):
    return FEDERATION_BANNED_USERID.get(fed_id, [])

def get_all_fban_users_target(fed_id, user_id):
    list_fbanned = FEDERATION_BANNED_FULL.get(fed_id)
    if list_fbanned is None:
        FEDERATION_BANNED_FULL[fed_id] = []
        return False
    return list_fbanned.get(str(user_id))

def get_all_fban_users_global():
    total = []
    for x in FEDERATION_BANNED_USERID:
        total.extend(FEDERATION_BANNED_USERID[x])
    return total

def get_all_feds_users_global():
    return list(FEDERATION_BYFEDID.values())

def search_fed_by_id(fed_id):
    return FEDERATION_BYFEDID.get(fed_id, False)

def user_feds_report(user_id: int) -> bool:
    return FEDERATION_NOTIFICATION.get(str(user_id), True)

def set_feds_setting(user_id: int, setting: bool):
    with FEDS_SETTINGS_LOCK:
        global FEDERATION_NOTIFICATION
        db.feds_settings.update_one({"user_id": user_id}, {"$set": {"should_report": setting}}, upsert=True)
        FEDERATION_NOTIFICATION[str(user_id)] = setting

async def get_fed_log(fed_id):
    fed_setting = FEDERATION_BYFEDID.get(str(fed_id))
    if fed_setting is None:
        return False
    if fed_setting.get("flog") is None:
        return False
    try:
        await dispatcher.bot.get_chat(fed_setting.get("flog"))
    except (BadRequest, Forbidden):
        set_fed_log(fed_id, None)
        return False
    return fed_setting.get("flog")


def set_fed_log(fed_id, chat_id):
    with FEDS_LOCK:
        global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        fed_members = getfed["fusers"]
        fed_rules = getfed["frules"]
        fed_log = str(chat_id)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]["flog"] = fed_log
        FEDERATION_BYFEDID[str(fed_id)]["flog"] = fed_log
        FEDERATION_BYNAME[fed_name]["flog"] = fed_log
        # Set on database
        db.federations.update_one(
            {"fed_id": str(fed_id)},
            {"$set": {"fed_log": fed_log}},
            upsert=True
        )
        return True

def subs_fed(fed_id, my_fed):
    check = get_spec_subs(fed_id, my_fed)
    if check:
        return False
    with FEDS_SUBSCRIBER_LOCK:
        db.fed_subs.update_one(
            {"fed_id": fed_id, "fed_subs": my_fed},
            {"$set": {"fed_id": fed_id, "fed_subs": my_fed}},
            upsert=True
        )
        global FEDS_SUBSCRIBER, MYFEDS_SUBSCRIBER
        # Temporary Data For Subbed Feds
        if FEDS_SUBSCRIBER.get(fed_id, set()) == set():
            FEDS_SUBSCRIBER[fed_id] = {my_fed}
        else:
            FEDS_SUBSCRIBER.get(fed_id, set()).add(my_fed)
        # Temporary data for Fed Subs
        if MYFEDS_SUBSCRIBER.get(my_fed, set()) == set():
            MYFEDS_SUBSCRIBER[my_fed] = {fed_id}
        else:
            MYFEDS_SUBSCRIBER.get(my_fed, set()).add(fed_id)
        return True

def unsubs_fed(fed_id, my_fed):
    with FEDS_SUBSCRIBER_LOCK:
        result = db.fed_subs.delete_one({"fed_id": fed_id, "fed_subs": my_fed})
        if result.deleted_count > 0:
            if my_fed in FEDS_SUBSCRIBER.get(fed_id, set()):  # sanity check
                FEDS_SUBSCRIBER.get(fed_id, set()).remove(my_fed)
            if fed_id in MYFEDS_SUBSCRIBER.get(my_fed, set()):  # sanity check
                MYFEDS_SUBSCRIBER.get(my_fed, set()).remove(fed_id)
            return True
        return False

def get_all_subs(fed_id):
    return FEDS_SUBSCRIBER.get(fed_id, set())

def get_spec_subs(fed_id, fed_target):
    if FEDS_SUBSCRIBER.get(fed_id, set()) == set():
        return {}
    else:
        return FEDS_SUBSCRIBER.get(fed_id, fed_target)

def get_mysubs(my_fed):
    return list(MYFEDS_SUBSCRIBER.get(my_fed))

def get_subscriber(fed_id):
    return FEDS_SUBSCRIBER.get(fed_id, set())

def __load_all_feds():
    global FEDERATION_BYOWNER, FEDERATION_BYFEDID, FEDERATION_BYNAME
    feds = db.federations.find()
    for x in feds:
        # Fed by Owner
        FEDERATION_BYOWNER[str(x["owner_id"])] = {
            "fid": str(x["fed_id"]),
            "fname": x["fed_name"],
            "frules": x["fed_rules"],
            "flog": x["fed_log"],
            "fusers": str(x["fed_users"]),
        }
        # Fed By FedId
        FEDERATION_BYFEDID[str(x["fed_id"])] = {
            "owner": str(x["owner_id"]),
            "fname": x["fed_name"],
            "frules": x["fed_rules"],
            "flog": x["fed_log"],
            "fusers": str(x["fed_users"]),
        }
        # Fed By Name
        FEDERATION_BYNAME[x["fed_name"]] = {
            "fid": str(x["fed_id"]),
            "owner": str(x["owner_id"]),
            "frules": x["fed_rules"],
            "flog": x["fed_log"],
            "fusers": str(x["fed_users"]),
        }

def __load_all_feds_chats():
    global FEDERATION_CHATS, FEDERATION_CHATS_BYID
    qall = chat_feds.find()
    FEDERATION_CHATS = {}
    FEDERATION_CHATS_BYID = {}
    for x in qall:
        # Federation Chats
        FEDERATION_CHATS[x["chat_id"]] = {"chat_name": x["chat_name"], "fid": x["fed_id"]}
        # Federation Chats By ID
        if x["fed_id"] not in FEDERATION_CHATS_BYID:
            FEDERATION_CHATS_BYID[x["fed_id"]] = []
        FEDERATION_CHATS_BYID[x["fed_id"]].append(x["chat_id"])

def __load_all_feds_banned():
    global FEDERATION_BANNED_USERID, FEDERATION_BANNED_FULL
    FEDERATION_BANNED_USERID = {}
    FEDERATION_BANNED_FULL = {}
    qall = bans_feds.find()
    for x in qall:
        if x["fed_id"] not in FEDERATION_BANNED_USERID:
            FEDERATION_BANNED_USERID[x["fed_id"]] = []
        if int(x["user_id"]) not in FEDERATION_BANNED_USERID[x["fed_id"]]:
            FEDERATION_BANNED_USERID[x["fed_id"]].append(int(x["user_id"]))
        if x["fed_id"] not in FEDERATION_BANNED_FULL:
            FEDERATION_BANNED_FULL[x["fed_id"]] = {}
        FEDERATION_BANNED_FULL[x["fed_id"]][x["user_id"]] = {
            "first_name": x["first_name"],
            "last_name": x["last_name"],
            "user_name": x["user_name"],
            "reason": x["reason"],
            "time": x["time"],
        }

def __load_all_feds_settings():
    global FEDERATION_NOTIFICATION
    getuser = db.feds_settings.find()
    for x in getuser:
        FEDERATION_NOTIFICATION[str(x["user_id"])] = x["should_report"]

def __load_feds_subscriber():
    global FEDS_SUBSCRIBER
    global MYFEDS_SUBSCRIBER
    feds = db.fed_subs.distinct("fed_id")
    for fed_id in feds:
        FEDS_SUBSCRIBER[fed_id] = []
        MYFEDS_SUBSCRIBER[fed_id] = []

    all_fedsubs = db.fed_subs.find()
    for x in all_fedsubs:
        FEDS_SUBSCRIBER[x["fed_id"]].append(x["fed_subs"])
        try:
            MYFEDS_SUBSCRIBER[x["fed_subs"]].append(x["fed_id"])
        except KeyError:
            db.fed_subs.delete_one({"fed_id": x["fed_id"], "fed_subs": x["fed_subs"]})

    FEDS_SUBSCRIBER = {x: set(y) for x, y in FEDS_SUBSCRIBER.items()}
    MYFEDS_SUBSCRIBER = {x: set(y) for x, y in MYFEDS_SUBSCRIBER.items()}

__load_all_feds()
__load_all_feds_chats()
__load_all_feds_banned()
__load_all_feds_settings()
__load_feds_subscriber()
