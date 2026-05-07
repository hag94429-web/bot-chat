import asyncio
import random
import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import (
    register_user,
    get_balance,
    add_balance,
    spend_balance,
    add_duel_log,
    get_duel_logs
)

from utils import auto_delete

router = Router()

active_duels = {}
duel_cooldowns = {}

DUEL_COOLDOWN = 30
DUEL_TIMEOUT = 60
DUEL_FEE_PERCENT = 10


def user_name(user_id, username=None, full_name=None):
    if username:
        return f"@{username}"
    if full_name:
        return full_name
    return f"ID:{user_id}"


def duel_keyboard(duel_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Прийняти", callback_data=f"duel_accept:{duel_id}")
    kb.button(text="❌ Відхилити", callback_data=f"duel_decline:{duel_id}")
    kb.adjust(2)
    return kb.as_markup()


def rematch_keyboard(challenger_id, opponent_id, bet):
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🔁 Реванш",
        callback_data=f"duel_rematch:{challenger_id}:{opponent_id}:{bet}"
    )
    kb.adjust(1)
    return kb.as_markup()


async def auto_cleanup_duel(duel_id, message):
    await asyncio.sleep(DUEL_TIMEOUT)

    if duel_id in active_duels:
        active_duels.pop(duel_id, None)

        try:
            await message.edit_text(
                "❌ Дуель скасована.\n\n"
                "⏳ Час на прийняття вийшов."
            )
        except Exception:
            pass


async def start_duel_message(message, challenger_id, challenger_name, opponent_id, bet):
    now = int(time.time())
    duel_id = f"{challenger_id}_{opponent_id}_{now}"

    active_duels[duel_id] = {
        "challenger_id": challenger_id,
        "challenger_name": challenger_name,
        "opponent_id": opponent_id,
        "bet": bet,
        "created_at": now
    }

    duel_msg = await message.answer(
        f"⚔️ Дуель!\n\n"
        f"👤 Викликає: {challenger_name}\n"
        f"🎯 Суперник ID: {opponent_id}\n"
        f"💰 Ставка: {bet} NC\n\n"
        f"⏳ Час на прийняття: {DUEL_TIMEOUT} сек.",
        reply_markup=duel_keyboard(duel_id)
    )

    asyncio.create_task(auto_cleanup_duel(duel_id, duel_msg))


@router.message(Command("duel"))
async def duel_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    register_user(user_id, username, full_name)

    args = message.text.split()

    if len(args) != 3:
        await message.answer("❌ Використання: /duel user_id сума")
        return

    try:
        opponent_id = int(args[1])
        bet = int(args[2])
    except ValueError:
        await message.answer("❌ user_id і сума мають бути числами.")
        return

    if opponent_id == user_id:
        await message.answer("❌ Не можна викликати самого себе.")
        return

    if bet < 50:
        await message.answer("❌ Мінімальна ставка: 50 NC.")
        return

    now = int(time.time())
    last = duel_cooldowns.get(user_id, 0)

    if now - last < DUEL_COOLDOWN:
        await message.answer("⏳ Дуель можна створювати раз на 30 секунд.")
        return

    if get_balance(user_id) < bet:
        await message.answer("❌ У тебе недостатньо NC.")
        return

    if get_balance(opponent_id) < bet:
        await message.answer("❌ У суперника недостатньо NC або він ще не користувався ботом.")
        return

    duel_cooldowns[user_id] = now

    challenger_name = user_name(user_id, username, full_name)

    await start_duel_message(
        message,
        user_id,
        challenger_name,
        opponent_id,
        bet
    )


@router.callback_query(F.data.startswith("duel_accept:"))
async def duel_accept(callback: CallbackQuery):
    duel_id = callback.data.split(":")[1]

    if duel_id not in active_duels:
        await callback.answer("❌ Дуель вже неактивна.", show_alert=True)
        return

    duel = active_duels[duel_id]

    challenger_id = duel["challenger_id"]
    opponent_id = duel["opponent_id"]
    bet = duel["bet"]

    if callback.from_user.id != opponent_id:
        await callback.answer("❌ Це не твоя дуель.", show_alert=True)
        return

    opponent_name = user_name(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name
    )

    challenger_name = duel["challenger_name"]

    if get_balance(challenger_id) < bet:
        await callback.message.edit_text("❌ У того, хто викликав, вже недостатньо NC.")
        active_duels.pop(duel_id, None)
        return

    if get_balance(opponent_id) < bet:
        await callback.answer("❌ У тебе недостатньо NC.", show_alert=True)
        return

    spend_balance(challenger_id, bet)
    spend_balance(opponent_id, bet)

    msg = await callback.message.edit_text("⚔️ Дуель почалась...")

    frames = [
        "⚔️ ░░░░░░",
        "⚔️ ███░░░",
        "⚔️ ██████",
    ]

    for frame in frames:
        await asyncio.sleep(0.5)
        try:
            await msg.edit_text(frame)
        except Exception:
            pass

    winner_id = random.choice([challenger_id, opponent_id])
    winner_name = challenger_name if winner_id == challenger_id else opponent_name

    bank = bet * 2
    fee = bank * DUEL_FEE_PERCENT // 100
    prize = bank - fee

    add_balance(winner_id, prize)
    add_duel_log(challenger_id, opponent_id, winner_id, bet, fee)

    active_duels.pop(duel_id, None)

    await msg.edit_text(
        f"🏆 Дуель завершена!\n\n"
        f"⚔️ {challenger_name} vs {opponent_name}\n\n"
        f"👑 Переможець: {winner_name}\n"
        f"💰 Виграш: {prize} NC\n"
        f"🪙 Комісія бота: {fee} NC",
        reply_markup=rematch_keyboard(challenger_id, opponent_id, bet)
    )

    asyncio.create_task(auto_delete(msg, 45))

    await callback.answer()


@router.callback_query(F.data.startswith("duel_decline:"))
async def duel_decline(callback: CallbackQuery):
    duel_id = callback.data.split(":")[1]

    if duel_id not in active_duels:
        await callback.answer("❌ Дуель вже неактивна.", show_alert=True)
        return

    duel = active_duels[duel_id]

    if callback.from_user.id != duel["opponent_id"]:
        await callback.answer("❌ Це не твоя дуель.", show_alert=True)
        return

    active_duels.pop(duel_id, None)

    await callback.message.edit_text("❌ Дуель відхилено.")
    await callback.answer()


@router.callback_query(F.data.startswith("duel_rematch:"))
async def duel_rematch(callback: CallbackQuery):
    parts = callback.data.split(":")

    old_challenger_id = int(parts[1])
    old_opponent_id = int(parts[2])
    bet = int(parts[3])

    user_id = callback.from_user.id

    if user_id not in [old_challenger_id, old_opponent_id]:
        await callback.answer("❌ Реванш можуть створити тільки учасники дуелі.", show_alert=True)
        return

    if user_id == old_challenger_id:
        challenger_id = old_challenger_id
        opponent_id = old_opponent_id
    else:
        challenger_id = old_opponent_id
        opponent_id = old_challenger_id

    register_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name
    )

    challenger_name = user_name(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.full_name
    )

    now = int(time.time())
    last = duel_cooldowns.get(challenger_id, 0)

    if now - last < DUEL_COOLDOWN:
        await callback.answer("⏳ Реванш можна створювати раз на 30 секунд.", show_alert=True)
        return

    if get_balance(challenger_id) < bet:
        await callback.answer("❌ У тебе недостатньо NC для реваншу.", show_alert=True)
        return

    if get_balance(opponent_id) < bet:
        await callback.answer("❌ У суперника недостатньо NC для реваншу.", show_alert=True)
        return

    duel_cooldowns[challenger_id] = now

    duel_id = f"{challenger_id}_{opponent_id}_{now}"

    active_duels[duel_id] = {
        "challenger_id": challenger_id,
        "challenger_name": challenger_name,
        "opponent_id": opponent_id,
        "bet": bet,
        "created_at": now
    }

    duel_msg = await callback.message.answer(
        f"🔁 Реванш!\n\n"
        f"👤 Викликає: {challenger_name}\n"
        f"🎯 Суперник ID: {opponent_id}\n"
        f"💰 Ставка: {bet} NC\n\n"
        f"⏳ Час на прийняття: {DUEL_TIMEOUT} сек.",
        reply_markup=duel_keyboard(duel_id)
    )

    asyncio.create_task(auto_cleanup_duel(duel_id, duel_msg))

    await callback.answer("🔁 Реванш створено!")


@router.message(Command("duellogs"))
async def duel_logs_cmd(message: Message):
    rows = get_duel_logs(10)

    if not rows:
        await message.answer("⚔️ Логів дуелей поки нема.")
        return

    text = "⚔️ Останні дуелі:\n\n"

    for row in rows:
        challenger_id, opponent_id, winner_id, bet, fee, created_at = row

        text += (
            f"⚔️ ID:{challenger_id} vs ID:{opponent_id}\n"
            f"👑 Winner: ID:{winner_id}\n"
            f"💰 Bet: {bet} NC\n"
            f"🪙 Fee: {fee} NC\n"
            f"📅 {created_at}\n\n"
        )

    await message.answer(text)