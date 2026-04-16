from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram import Bot

from config import CHAT_ID, SPAM_LIMIT, SPAM_WINDOW
from db import (
    add_wl,
    del_wl,
    get_ban_logs,
    get_join_logs,
    get_mute_logs,
    get_raid_events,
    get_wl,
)
from keyboards import panel_kb
from services import anti_raid

router = Router()


async def reply_temp(message: types.Message, bot: Bot, text: str, delay: int = 8):
    msg = await message.answer(text)
    import asyncio
    asyncio.create_task(auto_delete(bot, msg.chat.id, msg.message_id, delay))


async def auto_delete(bot: Bot, chat_id: int, message_id: int, delay: int):
    import asyncio
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass


def allowed(uid: int) -> bool:
    return uid in anti_raid.admins


@router.message(Command("panel"))
async def panel(message: types.Message):
    if message.chat.id != CHAT_ID or not allowed(message.from_user.id):
        return
    await message.answer("⚙️ Панель", reply_markup=panel_kb())


@router.message(Command("status"))
async def status_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    await message.answer(
        f"raid={anti_raid.raid_mode}\n"
        f"strict={anti_raid.strict_mode}\n"
        f"lockdown={anti_raid.lockdown_mode}\n"
        f"pending={len(anti_raid.pending)}\n"
        f"admins={len(anti_raid.admins)}\n"
        f"spam={SPAM_LIMIT}/{SPAM_WINDOW}s"
    )


@router.message(Command("raid"))
async def raid_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    text = (message.text or "").lower()
    if "on" in text:
        await anti_raid.enable_raid("manual")
        await reply_temp(message, bot, "🚨 RAID MODE ON", 8)
    elif "off" in text:
        await anti_raid.disable_raid()
        await reply_temp(message, bot, "✅ RAID MODE OFF", 8)
    else:
        await reply_temp(message, bot, f"raid={anti_raid.raid_mode}", 8)


@router.message(Command("strict"))
async def strict_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    anti_raid.strict_mode = not anti_raid.strict_mode
    await reply_temp(message, bot, f"strict={anti_raid.strict_mode}", 8)


@router.message(Command("lockdown"))
async def lockdown_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    text = (message.text or "").lower()
    if "on" in text:
        await anti_raid.enable_lockdown("manual")
        await reply_temp(message, bot, "🔒 LOCKDOWN MODE ON", 10)
    elif "off" in text:
        await anti_raid.disable_lockdown()
        await reply_temp(message, bot, "✅ LOCKDOWN MODE OFF", 10)
    else:
        await reply_temp(message, bot, f"lockdown={anti_raid.lockdown_mode}", 8)


@router.message(Command("syncadmins"))
async def sync_admins(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    await load_admins(bot)
    await reply_temp(message, bot, "✅ Адміни оновлені", 8)


async def load_admins(bot: Bot):
    members = await bot.get_chat_administrators(CHAT_ID)
    anti_raid.admins = {m.user.id for m in members}
    from db import add_wl
    for m in members:
        add_wl(m.user.id)


@router.message(Command("logs"))
async def logs_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    rows = get_join_logs(15)
    if not rows:
        await reply_temp(message, bot, "Логів немає", 8)
        return

    text = "\n".join([f"{r['user_id']} | {r['entry_type']} | {r['invite']}" for r in rows])
    await message.answer(text[:4000])


@router.message(Command("mutes"))
async def mutes_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    rows = get_mute_logs(15)
    if not rows:
        await reply_temp(message, bot, "Мутів немає", 8)
        return

    text = "\n".join([f"{r['user_id']} | {r['reason']}" for r in rows])
    await message.answer(text[:4000])


@router.message(Command("bans"))
async def bans_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    rows = get_ban_logs(15)
    if not rows:
        await reply_temp(message, bot, "Банів немає", 8)
        return

    text = "\n".join([f"{r['user_id']} | {r['reason']}" for r in rows])
    await message.answer(text[:4000])


@router.message(Command("raidevents"))
async def raid_events_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    rows = get_raid_events(15)
    if not rows:
        await reply_temp(message, bot, "Рейд подій немає", 8)
        return

    text = "\n".join([f"{r['event_type']} | {r['reason']}" for r in rows])
    await message.answer(text[:4000])


@router.message(Command("wl"))
async def wl_cmd(message: types.Message, bot: Bot):
    if message.chat.id != CHAT_ID:
        return
    if not allowed(message.from_user.id):
        await reply_temp(message, bot, "❌ Нема доступу", 5)
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await reply_temp(message, bot, "/wl add 123\n/wl del 123\n/wl list", 8)
        return

    action = parts[1].lower()
    if action == "list":
        wl = get_wl()
        await message.answer("\n".join(map(str, wl[:100])) if wl else "Whitelist порожній")
        return

    if len(parts) < 3:
        await reply_temp(message, bot, "Вкажи user_id", 8)
        return

    try:
        uid = int(parts[2])
    except ValueError:
        await reply_temp(message, bot, "user_id має бути числом", 8)
        return

    if action == "add":
        add_wl(uid)
        await reply_temp(message, bot, f"✅ Додано {uid}", 8)
    elif action == "del":
        del_wl(uid)
        await reply_temp(message, bot, f"✅ Видалено {uid}", 8)