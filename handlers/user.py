from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import DAILY_REWARD, ADMIN_IDS
from database import (
    register_user,
    get_balance,
    add_balance,
    can_daily,
    set_daily,
    get_top,
    get_logs,
    get_top_donates,
    get_active_emoji,
    get_active_role
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("start"))
async def start_cmd(message: Message):
    register_user(message.from_user.id, message.from_user.username)

    await message.answer(
        "🌙 Nyx Coin бот активний!\n\n"
        "/profile — профіль\n"
        "/balance — баланс\n"
        "/daily — щоденний бонус\n"
        "/top — топ по NC\n"
        "/shop — магазин\n"
        "/stars — купити NC за ⭐\n"
        "/topdonate — топ донатерів"
    )


@router.message(Command("profile"))
async def profile_cmd(message: Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username)

    balance = get_balance(user_id)
    emoji = get_active_emoji(user_id)
    role = get_active_role(user_id)

    emoji_text = emoji if emoji else "немає"
    role_text = "⭐ BASIC VIP" if role == "basic" else "немає"

    await message.answer(
        f"👤 Профіль\n\n"
        f"💰 Баланс: {balance} NC\n"
        f"😊 Emoji статус: {emoji_text}\n"
        f"⭐ Роль: {role_text}"
    )


@router.message(Command("balance"))
async def balance_cmd(message: Message):
    register_user(message.from_user.id, message.from_user.username)

    balance = get_balance(message.from_user.id)
    await message.answer(f"💰 Твій баланс: {balance} NC")


@router.message(Command("daily"))
async def daily_cmd(message: Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username)

    if not can_daily(user_id):
        await message.answer("⏳ Ти вже забирав бонус сьогодні.")
        return

    role = get_active_role(user_id)

    reward = DAILY_REWARD
    if role == "basic":
        reward = int(DAILY_REWARD * 1.1)

    add_balance(user_id, reward)
    set_daily(user_id)

    if role == "basic":
        await message.answer(f"🎁 Ти отримав {reward} NC!\n⭐ BASIC VIP бонус: +10%")
    else:
        await message.answer(f"🎁 Ти отримав {reward} NC!")


@router.message(Command("top"))
async def top_cmd(message: Message):
    rows = get_top()

    if not rows:
        await message.answer("🏆 Топ поки порожній.")
        return

    text = "🏆 Топ Nyx Coin:\n\n"

    for i, row in enumerate(rows, start=1):
        username, user_id, balance = row

        name = f"@{username}" if username else f"ID:{user_id}"
        emoji = get_active_emoji(user_id)
        role = get_active_role(user_id)

        emoji_prefix = f"{emoji} " if emoji else ""
        role_prefix = "⭐ [VIP] " if role == "basic" else ""

        text += f"{i}. {emoji_prefix}{role_prefix}{name} — {balance} NC\n"

    await message.answer(text)


@router.message(Command("give"))
async def give_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Тільки адмін.")
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer("❌ Використання: /give user_id сума")
        return

    try:
        user_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ user_id і сума мають бути числами.")
        return

    if amount <= 0:
        await message.answer("❌ Сума має бути більше 0.")
        return

    register_user(user_id, None)
    add_balance(user_id, amount)

    await message.answer(f"✅ Видано {amount} NC користувачу {user_id}.")


@router.message(Command("logs"))
async def logs_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Тільки адмін.")
        return

    rows = get_logs(15)

    if not rows:
        await message.answer("📊 Логів поки нема.")
        return

    text = "📊 Останні дії:\n\n"

    for row in rows:
        username, user_id, action, amount, item, created_at = row
        name = f"@{username}" if username else f"ID:{user_id}"
        text += f"{name} | {action} | {amount} | {item} | {created_at}\n"

    await message.answer(text)


@router.message(Command("topdonate"))
async def topdonate_cmd(message: Message):
    rows = get_top_donates()

    if not rows:
        await message.answer("💎 Донатів поки нема.")
        return

    text = "💎 Топ донатерів:\n\n"

    for i, row in enumerate(rows, start=1):
        username, user_id, total = row
        name = f"@{username}" if username else f"ID:{user_id}"
        text += f"{i}. {name} — {total}⭐\n"

    await message.answer(text)