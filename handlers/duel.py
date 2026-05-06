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
    add_duel_log
)

router = Router()

active_duels = {}
DUEL_COOLDOWN = 45
duel_cooldowns = {}

DUEL_FEE_PERCENT = 10


def duel_keyboard(duel_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Прийняти", callback_data=f"duel_accept:{duel_id}")
    kb.button(text="❌ Відхилити", callback_data=f"duel_decline:{duel_id}")
    kb.adjust(2)
    return kb.as_markup()


@router.message(Command("duel"))
async def duel_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    register_user(user_id, username, message.from_user.full_name)

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
        await message.answer("⏳ Дуель можна створювати раз на 45 секунд.")
        return

    if get_balance(user_id) < bet:
        await message.answer("❌ У тебе недостатньо NC.")
        return

    if get_balance(opponent_id) < bet:
        await message.answer("❌ У суперника недостатньо NC або він ще не користувався ботом.")
        return

    duel_id = f"{user_id}_{opponent_id}_{now}"

    active_duels[duel_id] = {
        "challenger_id": user_id,
        "challenger_name": f"@{username}" if username else f"ID:{user_id}",
        "opponent_id": opponent_id,
        "bet": bet,
        "created_at": now
    }

    duel_cooldowns[user_id] = now

    await message.answer(
        f"⚔️ Дуель!\n\n"
        f"👤 Викликає: @{username if username else user_id}\n"
        f"🎯 Суперник ID: {opponent_id}\n"
        f"💰 Ставка: {bet} NC\n\n"
        f"Суперник має натиснути ✅ Прийняти.",
        reply_markup=duel_keyboard(duel_id)
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

    bank = bet * 2
    fee = bank * DUEL_FEE_PERCENT // 100
    prize = bank - fee

    add_balance(winner_id, prize)
    add_duel_log(challenger_id, opponent_id, winner_id, bet, fee)

    active_duels.pop(duel_id, None)

    await msg.edit_text(
        f"🏆 Дуель завершена!\n\n"
        f"👑 Переможець: ID:{winner_id}\n"
        f"💰 Виграш: {prize} NC\n"
        f"🪙 Комісія бота: {fee} NC"
    )

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
