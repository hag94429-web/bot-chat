import asyncio
import logging
import os
import time
from collections import defaultdict, deque

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from dotenv import load_dotenv

from db import add_wl, del_wl, get_logs, get_wl, init_db, is_wl, log_join

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", "0"))
OUR_LINK_PART = os.getenv("OUR_LINK_PART", "").strip()

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")
if not CHAT_ID:
    raise ValueError("CHAT_ID not set")

router = Router()

# -------- SETTINGS --------
WARNING = 3
RAID = 5
TIME_WINDOW = 10

OUR_LIMIT = 5
TOP_LIMIT = 3

SPAM_LIMIT = 12
SPAM_TIME = 5

CAPTCHA_TIME = 60
RAID_COOLDOWN = 120

# -------- STATE --------
joins = deque()
invites = defaultdict(deque)
msgs = defaultdict(deque)

raid_mode = False
strict_mode = False
last_raid = 0.0

pending = {}
admins = set()


# -------- UTILS --------
def now() -> float:
    return time.time()


def clean(q, t: int):
    while q and now() - q[0] > t:
        q.popleft()


def add_join() -> int:
    joins.append(now())
    clean(joins, TIME_WINDOW)
    return len(joins)


def add_inv(link: str) -> int:
    invites[link].append(now())
    clean(invites[link], TIME_WINDOW)
    return len(invites[link])


def get_type(link: str):
    if not link or link == "unknown":
        return "external", TOP_LIMIT

    if OUR_LINK_PART and OUR_LINK_PART in link:
        return "our", OUR_LIMIT

    return "external", TOP_LIMIT


def panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚨 RAID ON", callback_data="raid_on"),
                InlineKeyboardButton(text="✅ RAID OFF", callback_data="raid_off"),
            ],
            [
                InlineKeyboardButton(text="⛔ STRICT", callback_data="strict"),
                InlineKeyboardButton(text="📊 STATUS", callback_data="status"),
            ],
            [
                InlineKeyboardButton(text="👑 SYNC ADMINS", callback_data="sync"),
            ],
            [
                InlineKeyboardButton(text="📜 LOGS", callback_data="logs"),
            ],
        ]
    )


def captcha_kb(uid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я не бот", callback_data=f"ok:{uid}")]
        ]
    )


# -------- ADMIN --------
async def load_admins(bot: Bot):
    global admins

    members = await bot.get_chat_administrators(CHAT_ID)
    admins = {m.user.id for m in members}

    for m in members:
        add_wl(m.user.id)

    logging.info("Loaded admins: %s", admins)


# -------- PANEL COMMANDS --------
@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.chat.id != CHAT_ID:
        return

    if message.from_user.id not in admins:
        await message.answer("❌ Нема доступу")
        return

    await message.answer("⚙️ Панель", reply_markup=panel_kb())


@router.message(Command("status"))
async def status_cmd(message: types.Message):
    if message.chat.id != CHAT_ID:
        return

    if message.from_user.id not in admins:
        await message.answer("❌ Нема доступу")
        return

    await message.answer(
        f"raid={raid_mode}\n"
        f"strict={strict_mode}\n"
        f"pending={len(pending)}\n"
        f"admins={len(admins)}\n"
        f"spam={SPAM_LIMIT}/{SPAM_TIME}s"
    )


@router.message(Command("raid"))
async def raid_cmd(message: types.Message):
    global raid_mode, last_raid

    if message.chat.id != CHAT_ID:
        return

    if message.from_user.id not in admins:
        await message.answer("❌ Нема доступу")
        return

    text = (message.text or "").lower()

    if "on" in text:
        raid_mode = True
        last_raid = now()
        await message.answer("🚨 RAID MODE ON")
    elif "off" in text:
        raid_mode = False
        await message.answer("✅ RAID MODE OFF")
    else:
        await message.answer(f"raid={raid_mode}")


@router.message(Command("strict"))
async def strict_cmd(message: types.Message):
    global strict_mode

    if message.chat.id != CHAT_ID:
        return

    if message.from_user.id not in admins:
        await message.answer("❌ Нема доступу")
        return

    strict_mode = not strict_mode
    await message.answer(f"strict={strict_mode}")


@router.message(Command("syncadmins"))
async def sync_admins(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return

    if message.from_user.id not in admins:
        await message.answer("❌ Нема доступу")
        return

    await load_admins(bot)
    await message.answer("✅ Адміни оновлені")


@router.message(Command("logs"))
async def logs_cmd(message: types.Message):
    if message.chat.id != CHAT_ID:
        return

    if message.from_user.id not in admins:
        await message.answer("❌ Нема доступу")
        return

    logs = get_logs(15)
    if not logs:
        await message.answer("Логів немає")
        return

    text = "\n".join([f"{u} | {l}" for u, l in logs])
    await message.answer(text[:4000])


@router.message(Command("wl"))
async def wl_cmd(message: types.Message):
    if message.chat.id != CHAT_ID:
        return

    if message.from_user.id not in admins:
        await message.answer("❌ Нема доступу")
        return

    parts = (message.text or "").split()

    if len(parts) < 2:
        await message.answer("/wl add 123\n/wl del 123\n/wl list")
        return

    action = parts[1].lower()

    if action == "list":
        wl = get_wl()
        if not wl:
            await message.answer("Whitelist порожній")
            return
        await message.answer("\n".join(map(str, wl[:100])))
        return

    if len(parts) < 3:
        await message.answer("Вкажи user_id")
        return

    try:
        uid = int(parts[2])
    except ValueError:
        await message.answer("user_id має бути числом")
        return

    if action == "add":
        add_wl(uid)
        await message.answer(f"✅ Додано {uid}")
    elif action == "del":
        del_wl(uid)
        await message.answer(f"✅ Видалено {uid}")
    else:
        await message.answer("/wl add 123\n/wl del 123\n/wl list")


# -------- PANEL ACTIONS --------
@router.callback_query(F.data.in_(["raid_on", "raid_off", "strict", "status", "sync", "logs"]))
async def panel_actions(call: types.CallbackQuery, bot: Bot):
    global raid_mode, strict_mode, last_raid

    if call.message.chat.id != CHAT_ID:
        await call.answer()
        return

    if call.from_user.id not in admins:
        await call.answer("Нема доступу", show_alert=True)
        return

    if call.data == "raid_on":
        raid_mode = True
        last_raid = now()
        await call.message.edit_text(
            f"raid={raid_mode}\nstrict={strict_mode}",
            reply_markup=panel_kb()
        )

    elif call.data == "raid_off":
        raid_mode = False
        await call.message.edit_text(
            f"raid={raid_mode}\nstrict={strict_mode}",
            reply_markup=panel_kb()
        )

    elif call.data == "strict":
        strict_mode = not strict_mode
        await call.message.edit_text(
            f"raid={raid_mode}\nstrict={strict_mode}",
            reply_markup=panel_kb()
        )

    elif call.data == "sync":
        await load_admins(bot)
        await call.message.edit_text(
            "✅ Адміни оновлені",
            reply_markup=panel_kb()
        )

    elif call.data == "status":
        await call.message.edit_text(
            f"raid={raid_mode}\n"
            f"strict={strict_mode}\n"
            f"pending={len(pending)}\n"
            f"admins={len(admins)}\n"
            f"spam={SPAM_LIMIT}/{SPAM_TIME}s",
            reply_markup=panel_kb()
        )

    elif call.data == "logs":
        logs = get_logs(15)
        text = "\n".join([f"{u} | {l}" for u, l in logs]) or "нема логів"
        await call.message.edit_text(text[:4000], reply_markup=panel_kb())

    await call.answer()


# -------- JOIN --------
@router.message(F.chat.id == CHAT_ID, F.new_chat_members)
async def join_handler(message: types.Message, bot: Bot):
    global raid_mode, last_raid

    for u in message.new_chat_members:
        if u.is_bot:
            continue

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

        if typ != "our" and c >= limit and link != "unknown":
            try:
                await bot.revoke_chat_invite_link(message.chat.id, link)
            except Exception:
                pass

        if raid_mode or g >= WARNING:
            if strict_mode:
                try:
                    await bot.ban_chat_member(message.chat.id, u.id)
                except Exception:
                    pass
                continue

            try:
                await bot.restrict_chat_member(
                    message.chat.id,
                    u.id,
                    ChatPermissions(can_send_messages=False)
                )
            except Exception:
                continue

            await message.answer(
                f"{u.first_name}, підтверди що ти не бот",
                reply_markup=captcha_kb(u.id)
            )

            pending[u.id] = True
            asyncio.create_task(timeout(bot, message.chat.id, u.id))


# -------- CAPTCHA --------
@router.callback_query(F.data.startswith("ok:"))
async def ok(call: types.CallbackQuery, bot: Bot):
    try:
        uid = int(call.data.split(":")[1])
    except Exception:
        await call.answer("Помилка", show_alert=True)
        return

    if call.from_user.id != uid:
        await call.answer("Це не твоя кнопка", show_alert=True)
        return

    pending.pop(uid, None)

    try:
        await bot.restrict_chat_member(
            call.message.chat.id,
            uid,
            ChatPermissions(can_send_messages=True)
        )
    except Exception:
        pass

    try:
        await call.message.edit_text("✅ доступ відкрито")
    except Exception:
        pass

    await call.answer("Підтверджено")


async def timeout(bot: Bot, chat: int, uid: int):
    await asyncio.sleep(CAPTCHA_TIME)

    if uid in pending:
        pending.pop(uid, None)
        try:
            await bot.ban_chat_member(chat, uid)
        except Exception:
            pass


# -------- SPAM --------
@router.message(F.chat.id == CHAT_ID)
async def spam_handler(message: types.Message, bot: Bot):
    uid = message.from_user.id

    if is_wl(uid):
        return

    if message.text and message.text.startswith("/"):
        return

    if uid in pending:
        try:
            await message.delete()
        except Exception:
            pass
        return

    msgs[uid].append(now())
    clean(msgs[uid], SPAM_TIME)

    if len(msgs[uid]) >= SPAM_LIMIT:
        try:
            await bot.restrict_chat_member(
                message.chat.id,
                uid,
                ChatPermissions(can_send_messages=False)
            )
        except Exception:
            pass


# -------- AUTO RAID OFF --------
async def raid_loop():
    global raid_mode

    while True:
        await asyncio.sleep(10)
        if raid_mode and now() - last_raid > RAID_COOLDOWN:
            raid_mode = False


# -------- START --------
async def main():
    init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    await load_admins(bot)
    asyncio.create_task(raid_loop())

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())