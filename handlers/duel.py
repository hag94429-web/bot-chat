# =========================================================
# handlers/duel.py
# =========================================================

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
    get_duel_logs,
    add_duel_bet,
    get_duel_bets,
    delete_duel_bets,
    add_duel_win,
    add_duel_loss,
    get_equipped_weapon,
    get_duel_top,
    get_user_by_username
)

from data.weapons import WEAPONS
from utils import auto_delete

router = Router()

active_duels = {}
duel_cooldowns = {}

DUEL_COOLDOWN = 30
DUEL_TIMEOUT = 60

DUEL_FEE_PERCENT = 10
BET_FEE_PERCENT = 10
CRIT_BONUS = 15


def user_name(user_id, username=None, full_name=None):
    if username:
        return f"@{username}"

    if full_name:
        return full_name

    return f"ID:{user_id}"


def duel_keyboard(duel_id, challenger_id, opponent_id):
    kb = InlineKeyboardBuilder()

    kb.button(
        text="✅ Прийняти",
        callback_data=f"duel_accept:{duel_id}"
    )

    kb.button(
        text="❌ Відхилити",
        callback_data=f"duel_decline:{duel_id}"
    )

    kb.button(
        text="💸 100 NC на гравця 1",
        callback_data=f"duel_bet:{duel_id}:{challenger_id}:100"
    )

    kb.button(
        text="💸 100 NC на гравця 2",
        callback_data=f"duel_bet:{duel_id}:{opponent_id}:100"
    )

    kb.button(
        text="💰 500 NC на гравця 1",
        callback_data=f"duel_bet:{duel_id}:{challenger_id}:500"
    )

    kb.button(
        text="💰 500 NC на гравця 2",
        callback_data=f"duel_bet:{duel_id}:{opponent_id}:500"
    )

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

        delete_duel_bets(duel_id)

        try:
            await message.edit_text(
                "❌ Дуель скасована.\n\n"
                "⏳ Час на прийняття вийшов."
            )
        except:
            pass


async def start_duel_message(
    message,
    challenger_id,
    challenger_name,
    opponent_id,
    bet
):
    now = int(time.time())

    duel_id = f"{challenger_id}_{opponent_id}_{now}"

    active_duels[duel_id] = {
        "duel_id": duel_id,
        "challenger_id": challenger_id,
        "challenger_name": challenger_name,
        "opponent_id": opponent_id,
        "bet": bet,
        "created_at": now
    }

    duel_msg = await message.answer(
        f"⚔️ <b>ДУЕЛЬ</b>\n\n"

        f"👤 Гравець 1: {challenger_name}\n"
        f"👤 Гравець 2 ID: {opponent_id}\n"

        f"💰 Ставка: {bet} NC\n\n"

        f"💸 Можна ставити на переможця.\n"
        f"⏳ Час на прийняття: {DUEL_TIMEOUT} сек.",

        reply_markup=duel_keyboard(
            duel_id,
            challenger_id,
            opponent_id
        ),

        parse_mode="HTML"
    )

    asyncio.create_task(
        auto_cleanup_duel(
            duel_id,
            duel_msg
        )
    )


def apply_weapon_effect(owner_name, weapon, enemy_bonus):

    effect = weapon.get("effect")
    effect_chance = weapon.get("effect_chance", 0)
    effect_bonus = weapon.get("effect_bonus", 0)

    bonus = 0
    text = ""
    block_enemy_bonus = 0

    if random.randint(1, 100) > effect_chance:
        return bonus, text, block_enemy_bonus

    if effect == "crit":

        bonus += effect_bonus

        text = (
            f"\n🔥 {owner_name} "
            f"активував CRIT від {weapon['name']}! "
            f"(+{effect_bonus}%)"
        )

    elif effect == "heavy_hit":

        bonus += effect_bonus

        text = (
            f"\n🪓 {owner_name} "
            f"робить HEAVY HIT! "
            f"(+{effect_bonus}%)"
        )

    elif effect == "block":

        block_enemy_bonus = min(
            enemy_bonus,
            effect_bonus
        )

        text = (
            f"\n🛡 {owner_name} "
            f"блокує {block_enemy_bonus}% "
            f"бонусу суперника!"
        )

    elif effect == "dark_strike":

        bonus += effect_bonus

        text = (
            f"\n🌑 {owner_name} "
            f"активує DARK STRIKE! "
            f"(+{effect_bonus}%)"
        )

    return bonus, text, block_enemy_bonus


@router.message(Command("duel"))
async def duel_cmd(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    register_user(
        user_id,
        username,
        full_name
    )

    args = message.text.split()

    if len(args) != 3:

        await message.answer(
            "❌ Використання:\n"
            "/duel @username сума\n"
            "або\n"
            "/duel user_id сума"
        )

        return

    target = args[1]

    try:
        bet = int(args[2])

    except ValueError:

        await message.answer(
            "❌ Ставка має бути числом."
        )

        return

    if target.startswith("@"):

        user_row = get_user_by_username(target)

        if not user_row:

            await message.answer(
                "❌ Я не знаю цього користувача.\n\n"
                "Він має хоча б раз написати в чат."
            )

            return

        opponent_id = user_row[0]

    else:

        try:
            opponent_id = int(target)

        except ValueError:

            await message.answer(
                "❌ Використання:\n"
                "/duel @username сума\n"
                "або\n"
                "/duel user_id сума"
            )

            return

    if opponent_id == user_id:

        await message.answer(
            "❌ Не можна викликати самого себе."
        )

        return

    if bet < 50:

        await message.answer(
            "❌ Мінімальна ставка: 50 NC."
        )

        return

    now = int(time.time())

    last = duel_cooldowns.get(user_id, 0)

    if now - last < DUEL_COOLDOWN:

        await message.answer(
            "⏳ Дуель можна створювати раз на 30 секунд."
        )

        return

    if get_balance(user_id) < bet:

        await message.answer(
            "❌ У тебе недостатньо NC."
        )

        return

    if get_balance(opponent_id) < bet:

        await message.answer(
            "❌ У суперника недостатньо NC."
        )

        return

    duel_cooldowns[user_id] = now

    challenger_name = user_name(
        user_id,
        username,
        full_name
    )

    await start_duel_message(
        message,
        user_id,
        challenger_name,
        opponent_id,
        bet
    )

@router.callback_query(F.data.startswith("duel_bet:"))
async def duel_bet_button(callback: CallbackQuery):
    parts = callback.data.split(":")

    duel_id = parts[1]
    target_id = int(parts[2])
    amount = int(parts[3])

    user_id = callback.from_user.id
    username = callback.from_user.username

    register_user(user_id, username, callback.from_user.full_name)

    if duel_id not in active_duels:
        await callback.answer("❌ Дуель вже неактивна.", show_alert=True)
        return

    duel = active_duels[duel_id]

    if target_id not in [duel["challenger_id"], duel["opponent_id"]]:
        await callback.answer("❌ Невірний гравець.", show_alert=True)
        return

    if user_id in [duel["challenger_id"], duel["opponent_id"]]:
        await callback.answer("❌ Учасники не можуть ставити на свою дуель.", show_alert=True)
        return

    if not spend_balance(user_id, amount):
        await callback.answer("❌ Недостатньо NC.", show_alert=True)
        return

    add_duel_bet(
        duel_id,
        user_id,
        username,
        target_id,
        amount
    )

    await callback.answer(
        f"✅ Ставка прийнята: {amount} NC",
        show_alert=True
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
        await callback.message.edit_text("❌ У того хто викликав вже недостатньо NC.")
        active_duels.pop(duel_id, None)
        delete_duel_bets(duel_id)
        return

    if get_balance(opponent_id) < bet:
        await callback.answer("❌ У тебе недостатньо NC.", show_alert=True)
        return

    spend_balance(challenger_id, bet)
    spend_balance(opponent_id, bet)

    msg = await callback.message.edit_text("⚔️ Дуель почалась...")

    frames = [
        "⚔️ Гравці виходять на арену...",
        "⚔️ Перший удар...",
        "⚔️ Бій у самому розпалі...",
        "⚔️ Вирішальний момент..."
    ]

    for frame in frames:
        await asyncio.sleep(0.55)
        try:
            await msg.edit_text(frame)
        except:
            pass

    challenger_weapon_key = get_equipped_weapon(challenger_id)
    opponent_weapon_key = get_equipped_weapon(opponent_id)

    challenger_bonus = 0
    opponent_bonus = 0

    challenger_weapon_text = ""
    opponent_weapon_text = ""

    challenger_crit_text = ""
    opponent_crit_text = ""

    challenger_effect_text = ""
    opponent_effect_text = ""

    if challenger_weapon_key and challenger_weapon_key in WEAPONS:
        weapon = WEAPONS[challenger_weapon_key]
        challenger_bonus += weapon["win_bonus"]

        challenger_weapon_text = (
            f"\n{challenger_name} має {weapon['name']} "
            f"(+{weapon['win_bonus']}%)"
        )

        if random.randint(1, 100) <= weapon.get("crit_chance", 0):
            challenger_bonus += CRIT_BONUS
            challenger_crit_text = (
                f"\n🔥 {challenger_name} ловить CRITICAL HIT від {weapon['name']}!"
            )

    if opponent_weapon_key and opponent_weapon_key in WEAPONS:
        weapon = WEAPONS[opponent_weapon_key]
        opponent_bonus += weapon["win_bonus"]

        opponent_weapon_text = (
            f"\n{opponent_name} має {weapon['name']} "
            f"(+{weapon['win_bonus']}%)"
        )

        if random.randint(1, 100) <= weapon.get("crit_chance", 0):
            opponent_bonus += CRIT_BONUS
            opponent_crit_text = (
                f"\n🔥 {opponent_name} ловить CRITICAL HIT від {weapon['name']}!"
            )

    if challenger_weapon_key and challenger_weapon_key in WEAPONS:
        weapon = WEAPONS[challenger_weapon_key]

        bonus, text, block = apply_weapon_effect(
            challenger_name,
            weapon,
            opponent_bonus
        )

        challenger_bonus += bonus
        opponent_bonus -= block
        challenger_effect_text = text

    if opponent_weapon_key and opponent_weapon_key in WEAPONS:
        weapon = WEAPONS[opponent_weapon_key]

        bonus, text, block = apply_weapon_effect(
            opponent_name,
            weapon,
            challenger_bonus
        )

        opponent_bonus += bonus
        challenger_bonus -= block
        opponent_effect_text = text

    if challenger_bonus < 0:
        challenger_bonus = 0

    if opponent_bonus < 0:
        opponent_bonus = 0

    challenger_chance = 50 + challenger_bonus - opponent_bonus
    opponent_chance = 50 + opponent_bonus - challenger_bonus

    if challenger_chance < 25:
        challenger_chance = 25

    if opponent_chance < 25:
        opponent_chance = 25

    winner_id = random.choices(
        population=[challenger_id, opponent_id],
        weights=[challenger_chance, opponent_chance],
        k=1
    )[0]

    winner_name = challenger_name if winner_id == challenger_id else opponent_name

    if winner_id == challenger_id:
        fight_story = (
            f"⚔️ {opponent_name} починає атаку першим...\n"
            f"🛡 {challenger_name} витримує удар.\n"
            f"🔥 {challenger_name} знаходить момент для контратаки.\n"
            f"👑 {challenger_name} забирає перемогу!"
        )
    else:
        fight_story = (
            f"⚔️ {challenger_name} починає атаку першим...\n"
            f"🛡 {opponent_name} витримує удар.\n"
            f"🔥 {opponent_name} знаходить момент для контратаки.\n"
            f"👑 {opponent_name} забирає перемогу!"
        )

    if winner_id == challenger_id:
        add_duel_win(challenger_id)
        add_duel_loss(opponent_id)
    else:
        add_duel_win(opponent_id)
        add_duel_loss(challenger_id)

    bank = bet * 2
    fee = bank * DUEL_FEE_PERCENT // 100
    prize = bank - fee

    add_balance(winner_id, prize)

    add_duel_log(
        challenger_id,
        opponent_id,
        winner_id,
        bet,
        fee
    )

    bets = get_duel_bets(duel_id)

    total_bets_pool = sum(row[3] for row in bets)

    winner_bets = [
        row for row in bets
        if row[2] == winner_id
    ]

    winner_bets_sum = sum(row[3] for row in winner_bets)

    bet_text = ""

    if bets and winner_bets_sum > 0:
        bet_fee = total_bets_pool * BET_FEE_PERCENT // 100
        payout_pool = total_bets_pool - bet_fee

        bet_text += "\n\n💸 <b>Ставки:</b>"
        bet_text += f"\n🏦 Банк ставок: {total_bets_pool} NC"
        bet_text += f"\n🪙 Комісія ставок: {bet_fee} NC"

        for bet_user_id, bet_username, target_id, amount in winner_bets:
            payout = payout_pool * amount // winner_bets_sum
            add_balance(bet_user_id, payout)

            bet_name = f"@{bet_username}" if bet_username else f"ID:{bet_user_id}"
            bet_text += f"\n✅ {bet_name} виграв {payout} NC"

    elif bets:
        bet_text += "\n\n💸 <b>Ставки:</b> ніхто не вгадав."

    delete_duel_bets(duel_id)
    active_duels.pop(duel_id, None)

    await msg.edit_text(
        f"🏆 <b>Дуель завершена!</b>\n\n"

        f"⚔️ {challenger_name} vs {opponent_name}\n"
        f"{challenger_weapon_text}"
        f"{opponent_weapon_text}"
        f"{challenger_crit_text}"
        f"{opponent_crit_text}"
        f"{challenger_effect_text}"
        f"{opponent_effect_text}\n\n"

        f"🎬 <b>Хід бою:</b>\n"
        f"{fight_story}\n\n"

        f"📊 <b>Шанси:</b>\n"
        f"├ {challenger_name}: {challenger_chance}%\n"
        f"└ {opponent_name}: {opponent_chance}%\n\n"

        f"👑 <b>Переможець:</b> {winner_name}\n"
        f"💰 <b>Виграш:</b> {prize} NC\n"
        f"🪙 <b>Комісія бота:</b> {fee} NC"
        f"{bet_text}",

        reply_markup=rematch_keyboard(challenger_id, opponent_id, bet),
        parse_mode="HTML"
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

    delete_duel_bets(duel_id)
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
        await callback.answer("❌ Тільки учасники дуелі.", show_alert=True)
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
        await callback.answer("⏳ Реванш раз на 30 сек.", show_alert=True)
        return

    if get_balance(challenger_id) < bet:
        await callback.answer("❌ Недостатньо NC.", show_alert=True)
        return

    if get_balance(opponent_id) < bet:
        await callback.answer("❌ У суперника недостатньо NC.", show_alert=True)
        return

    duel_cooldowns[challenger_id] = now

    await start_duel_message(
        callback.message,
        challenger_id,
        challenger_name,
        opponent_id,
        bet
    )

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

@router.message(Command("dueltop"))
@router.message(F.text.lower() == "топ дуелей")
async def duel_top_cmd(message: Message):

    rows = get_duel_top(10)

    if not rows:
        await message.answer(
            "⚔️ Топ дуелянтів поки порожній."
        )
        return

    text = (
        "🏆 <b>ТОП ДУЕЛЯНТІВ</b>\n\n"
    )

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for i, row in enumerate(rows, start=1):

        user_id, username, wins, losses, streak, best_streak = row

        if i <= 3:
            place = medals[i - 1]
        else:
            place = f"{i}."

        if username:

            username = str(username)

            if username.startswith("@"):
                name = username
            else:
                name = f"@{username}"

        else:
            name = f"ID:{user_id}"

        total = wins + losses

        winrate = 0

        if total > 0:
            winrate = round(
                (wins / total) * 100
            )

        text += (
            f"{place} <b>{name}</b>\n"
            f"├ 🏆 Перемог: {wins}\n"
            f"├ 💀 Поразок: {losses}\n"
            f"├ 🔥 Серія: {streak}\n"
            f"├ ⚡ Рекорд: {best_streak}\n"
            f"└ 📊 Winrate: {winrate}%\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )