# =========================================================
# handlers/cases.py
# =========================================================

import random

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    register_user,
    get_balance,
    spend_balance,
    add_inventory_item,
    add_balance
)

from data.weapons import WEAPONS

router = Router()

COMMON_CASE_PRICE = 3000
EPIC_CASE_PRICE = 15000


def roll_weapon():
    items = []
    weights = []

    for key, weapon in WEAPONS.items():
        items.append(key)
        weights.append(weapon["drop_chance"])

    result = random.choices(
        items,
        weights=weights,
        k=1
    )[0]

    return result


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

    spend_balance(
        user_id,
        COMMON_CASE_PRICE
    )

    reward_type = random.choice([
        "weapon",
        "coins"
    ])

    if reward_type == "coins":
        reward = random.randint(1000, 7000)

        add_balance(
            user_id,
            reward
        )

        await message.answer(
            f"📦 COMMON CASE\n\n"
            f"💰 Тобі випало:\n"
            f"{reward} NC"
        )

        return

    weapon_key = roll_weapon()

    weapon = WEAPONS[weapon_key]

    add_inventory_item(
        user_id,
        weapon_key,
        1
    )

    await message.answer(
        f"📦 COMMON CASE\n\n"
        f"🎉 Тобі випало:\n\n"
        f"{weapon['name']}\n"
        f"Рідкість: {weapon['rarity']}\n"
        f"Бонус: +{weapon['win_bonus']}%"
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

    spend_balance(
        user_id,
        EPIC_CASE_PRICE
    )

    epic_pool = [
        "axe",
        "shield",
        "dark_sword"
    ]

    weights = [
        45,
        40,
        15
    ]

    weapon_key = random.choices(
        epic_pool,
        weights=weights,
        k=1
    )[0]

    weapon = WEAPONS[weapon_key]

    add_inventory_item(
        user_id,
        weapon_key,
        1
    )

    await message.answer(
        f"🔥 EPIC CASE\n\n"
        f"🎉 Тобі випало:\n\n"
        f"{weapon['name']}\n"
        f"Рідкість: {weapon['rarity']}\n"
        f"Бонус: +{weapon['win_bonus']}%"
    )