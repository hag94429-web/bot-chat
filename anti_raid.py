import time
from collections import defaultdict, deque

from aiogram import Bot
from aiogram.types import ChatPermissions

from config import (
    ADS_LIMIT,
    CAPTCHA_TIMEOUT,
    DUPLICATE_TEXT_LIMIT,
    DUPLICATE_TEXT_WINDOW,
    EXTERNAL_LIMIT,
    FRIENDS_LIMIT,
    FRIENDS_LINK,
    RAID_COOLDOWN,
    RAID_JOIN_THRESHOLD,
    RAID_MESSAGE_LIMIT,
    RAID_MESSAGE_WINDOW,
    TOP_LIMIT,
    TOP_LINK,
    ADS_LINK,
    WARNING_JOIN_THRESHOLD,
    JOIN_WINDOW,
)
from db import log_ban, log_mute, log_raid_event

joins = deque()
invite_joins = defaultdict(deque)
recent_messages = deque()
duplicate_texts = defaultdict(deque)

raid_mode = False
strict_mode = False
lockdown_mode = False
last_raid = 0.0

pending = {}
admins = set()


def now() -> float:
    return time.time()


def clean(q, window: int):
    while q and now() - q[0] > window:
        q.popleft()


def add_join() -> int:
    joins.append(now())
    clean(joins, JOIN_WINDOW)
    return len(joins)


def add_invite_join(link: str) -> int:
    invite_joins[link].append(now())
    clean(invite_joins[link], JOIN_WINDOW)
    return len(invite_joins[link])


def add_message_raid_point() -> int:
    recent_messages.append(now())
    clean(recent_messages, RAID_MESSAGE_WINDOW)
    return len(recent_messages)


def add_duplicate_text(text: str) -> int:
    key = (text or "").strip().lower()[:250]
    if not key:
        return 0
    duplicate_texts[key].append(now())
    clean(duplicate_texts[key], DUPLICATE_TEXT_WINDOW)
    return len(duplicate_texts[key])


def get_type(link: str):
    if not link or link == "unknown":
        return "external", EXTERNAL_LIMIT

    if FRIENDS_LINK and FRIENDS_LINK in link:
        return "friends", FRIENDS_LIMIT

    if TOP_LINK and TOP_LINK in link:
        return "top", TOP_LIMIT

    if ADS_LINK and ADS_LINK in link:
        return "ads", ADS_LIMIT

    return "external", EXTERNAL_LIMIT


async def enable_raid(reason: str):
    global raid_mode, last_raid
    raid_mode = True
    last_raid = now()
    log_raid_event("raid_on", reason)


async def disable_raid():
    global raid_mode
    raid_mode = False
    log_raid_event("raid_off", "cooldown")


async def enable_lockdown(reason: str):
    global lockdown_mode, raid_mode, strict_mode, last_raid
    lockdown_mode = True
    raid_mode = True
    strict_mode = True
    last_raid = now()
    log_raid_event("lockdown_on", reason)


async def disable_lockdown():
    global lockdown_mode, raid_mode, strict_mode
    lockdown_mode = False
    raid_mode = False
    strict_mode = False
    log_raid_event("lockdown_off", "manual")


async def maybe_disable_raid():
    global raid_mode
    if raid_mode and now() - last_raid > RAID_COOLDOWN and not lockdown_mode:
        await disable_raid()


async def mute_user(bot: Bot, chat_id: int, user_id: int, reason: str, seconds: int = 3600):
    try:
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            ChatPermissions(can_send_messages=False),
            until_date=int(now()) + seconds,
        )
        log_mute(user_id, reason)
    except Exception:
        pass


async def unmute_user(bot: Bot, chat_id: int, user_id: int):
    try:
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            ChatPermissions(can_send_messages=True)
        )
    except Exception:
        pass


async def ban_user(bot: Bot, chat_id: int, user_id: int, reason: str):
    try:
        await bot.ban_chat_member(chat_id, user_id)
        log_ban(user_id, reason)
    except Exception:
        pass


def need_captcha(global_join_count: int, invite_count: int, limit: int) -> bool:
    if lockdown_mode:
        return False
    if raid_mode:
        return True
    if global_join_count >= WARNING_JOIN_THRESHOLD:
        return True
    if invite_count >= max(2, limit - 1):
        return True
    return False


def should_enable_raid_by_messages() -> bool:
    return len(recent_messages) >= RAID_MESSAGE_LIMIT


def should_enable_lockdown_by_duplicates(duplicate_count: int) -> bool:
    return duplicate_count >= DUPLICATE_TEXT_LIMIT