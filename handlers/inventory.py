from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_IDS
from database import (
    register_user,
    get_inventory,
    has_inventory_item,
    equip_weapon,
    get_equipped_weapon,
    add_inventory_item
)
from data.weapons import WEAPONS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("inventory"))
async def inventory_cmd(message: Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username, message.from_user.full_name)

    rows = get_inventory(user_id)
    equipped = get_equipped_weapon(user_id)

    if not rows:
        await message.answer(
            "🎒 Інвентар порожній.\n\n"
            "Зброю можна отримати з кейсів, магазину або івентів."
        )
        return

    text = "🎒 Твій інвентар:\n\n"

    for item_key, amount in rows:
        weapon = WEAPONS.get(item_key)

        if not weapon:
            continue

        active = "✅ Екіпіровано" if equipped == item_key else ""

        text += (
            f"{weapon['name']} x{amount}\n"
            f"Рідкість: {weapon['rarity']}\n"
            f"Бонус перемоги: +{weapon['win_bonus']}%\n"
            f"Крит шанс: {weapon['crit_chance']}%\n"
            f"{active}\n\n"
        )

    text += "Щоб екіпірувати:\n/equip weapon_key\n\n"
    text += "Наприклад:\n/equip dagger"

    await message.answer(text)


@router.message(Command("equip"))
async def equip_cmd(message: Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username, message.from_user.full_name)

    args = message.text.split()

    if len(args) != 2:
        await message.answer("❌ Використання: /equip weapon_key\nНаприклад: /equip dagger")
        return

    weapon_key = args[1]

    if weapon_key not in WEAPONS:
        await message.answer("❌ Такої зброї не існує.")
        return

    if not has_inventory_item(user_id, weapon_key):
        await message.answer("❌ У тебе немає цієї зброї.")
        return

    equip_weapon(user_id, weapon_key)

    weapon = WEAPONS[weapon_key]

    await message.answer(
        f"✅ Зброю екіпіровано!\n\n"
        f"{weapon['name']}\n"
        f"Бонус перемоги: +{weapon['win_bonus']}%\n"
        f"Крит шанс: {weapon['crit_chance']}%"
    )


@router.message(Command("admin_give_weapon"))
async def admin_give_weapon_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Тільки адмін.")
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer("❌ Використання: /admin_give_weapon user_id weapon_key")
        return

    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ user_id має бути числом.")
        return

    weapon_key = args[2]

    if weapon_key not in WEAPONS:
        await message.answer("❌ Такої зброї нема.")
        return

    add_inventory_item(user_id, weapon_key, 1)

    await message.answer(
        f"✅ Видано зброю користувачу {user_id}\n\n"
        f"{WEAPONS[weapon_key]['name']}"
    )