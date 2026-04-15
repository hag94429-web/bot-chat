import asyncio
import time
import os
from collections import defaultdict, deque

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from dotenv import load_dotenv

from db import *

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

router = Router()

# -------- SETTINGS --------
WARNING = 3
RAID = 5
TIME_WINDOW = 10

OUR_LIMIT = 5
TOP_LIMIT = 3

SPAM_LIMIT = 6
SPAM_TIME = 4

CAPTCHA_TIME = 60
RAID_COOLDOWN = 120

OUR_LINK_PART = os.getenv("OUR_LINK_PART", "")

# -------- STATE --------
joins = deque()
invites = defaultdict(deque)
msgs = defaultdict(deque)

raid_mode = False
strict_mode = False
last_raid = 0

pending = {}
admins = set()

# -------- UTILS --------
def now(): return time.time()

def clean(q, t):
    while q and now() - q[0] > t:
        q.popleft()

def add_join():
    joins.append(now())
    clean(joins, TIME_WINDOW)
    return len(joins)

def add_inv(link):
    invites[link].append(now())
    clean(invites[link], TIME_WINDOW)
    return len(invites[link])

def get_type(link):
    if not link:
        return "external", TOP_LIMIT
    if OUR_LINK_PART and OUR_LINK_PART in link:
        return "our", OUR_LIMIT
    return "external", TOP_LIMIT

# -------- ADMIN --------
async def load_admins(bot):
    global admins
    a = await bot.get_chat_administrators(CHAT_ID)
    admins = {m.user.id for m in a}

    for m in a:
        add_wl(m.user.id)

# -------- CAPTCHA --------
def kb(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я не бот", callback_data=f"ok:{uid}")]
    ])

# -------- PANEL --------
def panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 RAID ON", callback_data="raid_on"),
         InlineKeyboardButton(text="✅ RAID OFF", callback_data="raid_off")],
        [InlineKeyboardButton(text="⛔ STRICT", callback_data="strict"),
         InlineKeyboardButton(text="📊 STATUS", callback_data="status")],
        [InlineKeyboardButton(text="👑 SYNC ADMINS", callback_data="sync")],
        [InlineKeyboardButton(text="📜 LOGS", callback_data="logs")]
    ])

# -------- JOIN --------
@router.message(F.new_chat_members)
async def join(message: types.Message, bot: Bot):
    global raid_mode, last_raid

    for u in message.new_chat_members:
        if is_wl(u.id):
            continue

        link = message.invite_link.invite_link if message.invite_link else "unknown"

        g = add_join()
        c = add_inv(link)
        typ, limit = get_type(link)

        log_join(u.id, link)

        if g >= RAID or c >= limit:
            raid_mode = True
            last_raid = now()

        if typ != "our" and c >= limit:
            try:
                await bot.revoke_chat_invite_link(message.chat.id, link)
            except:
                pass

        if raid_mode:

            if strict_mode:
                await bot.ban_chat_member(message.chat.id, u.id)
                return

            await bot.restrict_chat_member(
                message.chat.id,
                u.id,
                ChatPermissions(can_send_messages=False)
            )

            await message.answer(
                f"{u.first_name}, підтверди що ти не бот",
                reply_markup=kb(u.id)
            )

            pending[u.id] = True
            asyncio.create_task(timeout(bot, message.chat.id, u.id))

# -------- CAPTCHA --------
@router.callback_query(F.data.startswith("ok:"))
async def ok(call: types.CallbackQuery, bot: Bot):
    uid = int(call.data.split(":")[1])

    if call.from_user.id != uid:
        return

    pending.pop(uid, None)

    await bot.restrict_chat_member(
        call.message.chat.id,
        uid,
        ChatPermissions(can_send_messages=True)
    )

    await call.message.edit_text("✅ доступ відкрито")

async def timeout(bot, chat, uid):
    await asyncio.sleep(CAPTCHA_TIME)

    if uid in pending:
        pending.pop(uid)
        await bot.ban_chat_member(chat, uid)

# -------- СПАМ --------
@router.message()
async def spam(message: types.Message, bot: Bot):
    uid = message.from_user.id

    if is_wl(uid):
        return

    if message.text and message.text.startswith("/"):
        return

    msgs[uid].append(now())
    clean(msgs[uid], SPAM_TIME)

    if len(msgs[uid]) >= SPAM_LIMIT:
        await bot.restrict_chat_member(
            message.chat.id,
            uid,
            ChatPermissions(can_send_messages=False)
        )

@router.message(Command("panel"))
async def panel(message: types.Message):
    await message.answer(
        f"test\n"
        f"your_id={message.from_user.id}\n"
        f"admins={admins}",
        reply_markup=panel_kb()
    )
# -------- AUTO RAID OFF --------
async def loop():
    global raid_mode
    while True:
        await asyncio.sleep(10)
        if raid_mode and now() - last_raid > RAID_COOLDOWN:
            raid_mode = False

# -------- START --------
async def main():
    init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await load_admins(bot)
    asyncio.create_task(loop())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())