import asyncio
import random

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    register_user,
    get_balance,
    spend_balance,
    add_inventory_item,
    add_balance,
    equip_weapon
)

from data.weapons import WEAPONS

router = Router()

COMMON_CASE_PRICE = 3000
EPIC_CASE_PRICE = 15000


def roll_weapon(pool=None):
    items = []
    weights = []

    source = pool if pool else WEAPONS.keys()

    for key in source:
        weapon = WEAPONS[key]
        items.append(key)
        weights.append(weapon["drop_chance"])

    return random.choices(items, weights=weights, k=1)[0]


async def case_animation(message: Message, title: str):
    msg = await message.answer(f"{title}\n\n📦 Відкриваємо кейс...")

    frames = [
        f"{title}\n\n📦 ░░░░░░ 0%",
        f"{title}\n\n📦 ██░░░░ 35%",
        f"{title}\n\n📦 ████░░ 70%",
        f"{title}\n\n📦 ██████ 100%",
        f"{title}\n\n🎁 Кейс відкрито!"
    ]

    for frame in frames:
        await asyncio.sleep(0.45)
        try:
            await msg.edit_text(frame)
        except Exception:
            pass

    return msg


@router.message(Command("commoncase"))
@router.message(F.text.lower() == "камонкейс")
async def common_case_cmd(message: Message):
    user_id = message.from_user.id

    register_user(
        user_id,
        message.from_user.username,
        message.from_user.full_name
    )

    if get_balance(user_id) < COMMON_CASE_PRICE:
        await message.answer(
            f"❌ Недостатньо NC.\n"
            f"Потрібно: {COMMON_CASE_PRICE} NC"
        )
        return

    await message.answer(
        "📦 <b>COMMON CASE</b>\n\n"
        f"💰 Ціна: {COMMON_CASE_PRICE} NC\n\n"
        "🎲 <b>Можливі нагороди:</b>\n"
        "├ 💰 1000–7000 NC\n"
        "├ 🗡 Кинджал — часто\n"
        "├ 🪓 Сокира — рідше\n"
        "├ 🛡 Щит — рідко\n"
        "└ ⚔️ Темний меч — дуже рідко\n\n"
        "⏳ Відкриваю...",
        parse_mode="HTML"
    )

    spend_balance(user_id, COMMON_CASE_PRICE)

    msg = await case_animation(message, "📦 COMMON CASE")

    reward_type = random.choices(
        population=["weapon", "coins"],
        weights=[70, 30],
        k=1
    )[0]

    if reward_type == "coins":
        reward = random.randint(1000, 7000)
        add_balance(user_id, reward)

        await msg.edit_text(
            "📦 <b>COMMON CASE</b>\n\n"
            "💰 <b>Тобі випало:</b>\n"
            f"{reward} NC",
            parse_mode="HTML"
        )
        return

    weapon_key = roll_weapon()
    weapon = WEAPONS[weapon_key]

    add_inventory_item(user_id, weapon_key, 1)
    equip_weapon(user_id, weapon_key)

    await msg.edit_text(
        "📦 <b>COMMON CASE</b>\n\n"
        "🎉 <b>Тобі випала зброя:</b>\n\n"
        f"{weapon['name']}\n"
        f"├ Рідкість: {weapon['rarity']}\n"
        f"├ Бонус перемоги: +{weapon['win_bonus']}%\n"
        f"└ Crit шанс: {weapon['crit_chance']}%\n\n"
        "🎒 Додано в інвентар\n"
        "✅ Автоматично екіпіровано",
        parse_mode="HTML"
    )


@router.message(Command("epiccase"))
@router.message(F.text.lower() == "епіккейс")
async def epic_case_cmd(message: Message):
    user_id = message.from_user.id

    register_user(
        user_id,
        message.from_user.username,
        message.from_user.full_name
    )

    if get_balance(user_id) < EPIC_CASE_PRICE:
        await message.answer(
            f"❌ Недостатньо NC.\n"
            f"Потрібно: {EPIC_CASE_PRICE} NC"
        )
        return

    await message.answer(
        "🔥 <b>EPIC CASE</b>\n\n"
        f"💰 Ціна: {EPIC_CASE_PRICE} NC\n\n"
        "🎲 <b>Можливі нагороди:</b>\n"
        "├ 🪓 Сокира — 45%\n"
        "├ 🛡 Щит — 40%\n"
        "└ ⚔️ Темний меч — 15%\n\n"
        "⏳ Відкриваю...",
        parse_mode="HTML"
    )

    spend_balance(user_id, EPIC_CASE_PRICE)

    msg = await case_animation(message, "🔥 EPIC CASE")

    epic_pool = ["axe", "shield", "dark_sword"]
    weights = [45, 40, 15]

    weapon_key = random.choices(epic_pool, weights=weights, k=1)[0]
    weapon = WEAPONS[weapon_key]

    add_inventory_item(user_id, weapon_key, 1)
    equip_weapon(user_id, weapon_key)

    await msg.edit_text(
        "🔥 <b>EPIC CASE</b>\n\n"
        "🎉 <b>Тобі випала зброя:</b>\n\n"
        f"{weapon['name']}\n"
        f"├ Рідкість: {weapon['rarity']}\n"
        f"├ Бонус перемоги: +{weapon['win_bonus']}%\n"
        f"└ Crit шанс: {weapon['crit_chance']}%\n\n"
        "🎒 Додано в інвентар\n"
        "✅ Автоматично екіпіровано",
        parse_mode="HTML"
    )