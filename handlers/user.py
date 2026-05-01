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
    get_top
)

router = Router()


@router.message(Command("start"))
async def start(msg: Message):
    register_user(msg.from_user.id, msg.from_user.username)

    await msg.answer(
        "🌙 Nyx Coin бот активний!\n\n"
        "/balance — баланс\n"
        "/daily — щоденний бонус\n"
        "/top — топ\n"
        "/shop — магазин\n"
        "/stars — купити NC за ⭐"
    )


@router.message(Command("balance"))
async def balance(msg: Message):
    register_user(msg.from_user.id, msg.from_user.username)
    await msg.answer(f"💰 Твій баланс: {get_balance(msg.from_user.id)} NC")


@router.message(Command("daily"))
async def daily(msg: Message):
    user_id = msg.from_user.id

    register_user(user_id, msg.from_user.username)

    if not can_daily(user_id):
        await msg.answer("⏳ Ти вже забирав бонус сьогодні.")
        return

    add_balance(user_id, DAILY_REWARD)
    set_daily(user_id)

    await msg.answer(f"🎁 Ти отримав {DAILY_REWARD} NC!")


@router.message(Command("top"))
async def top(msg: Message):
    rows = get_top()

    if not rows:
        await msg.answer("🏆 Топ поки порожній.")
        return

    text = "🏆 Топ Nyx Coin:\n\n"

    for i, row in enumerate(rows, 1):
        username, user_id, balance = row
        name = f"@{username}" if username else f"ID: {user_id}"
        text += f"{i}. {name} — {balance} NC\n"

    await msg.answer(text)


@router.message(Command("give"))
async def give(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Тільки адмін.")
        return

    args = msg.text.split()

    if len(args) != 3:
        await msg.answer("❌ Використання: /give user_id сума")
        return

    try:
        user_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await msg.answer("❌ user_id і сума мають бути числами.")
        return

    if amount <= 0:
        await msg.answer("❌ Сума має бути більше 0.")
        return

    register_user(user_id, None)
    add_balance(user_id, amount)

    await msg.answer(f"✅ Видано {amount} NC користувачу {user_id}.")