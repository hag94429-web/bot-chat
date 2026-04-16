import time
from db import ensure_user, get_user, increment_user_messages, set_user_trust


def now_ts() -> int:
    return int(time.time())


def touch_user(uid: int):
    ensure_user(uid, now_ts())
    increment_user_messages(uid)

    user = get_user(uid)
    if not user:
        return

    messages_count = user["messages_count"]
    if messages_count >= 20 and user["trust_level"] != "trusted":
        set_user_trust(uid, "trusted")
    elif messages_count >= 5 and user["trust_level"] == "new":
        set_user_trust(uid, "regular")


def get_trust(uid: int) -> str:
    user = get_user(uid)
    if not user:
        return "new"
    return user["trust_level"]