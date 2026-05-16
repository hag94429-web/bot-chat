from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    register_user,
    get_balance,
    spend_balance,
    add_inventory_item
)

from data.weapons import WEAPONS

router = Router()


@router.message(Command("weaponshop"))
async def weapon_shop_cmd(message: Message):
    user_id = message.from_user.id

    register_user(
        user_id,
        message.from_user.username,
        message.from_user.full_name
    )

    text = "⚔️ Магазин зброї\n\n"

    for key, weapon in WEAPONS.items():
        text += (
            f"{weapon['name']}\n"
            f"Рідкість: {weapon['rarity']}\n"
            f"Бонус: +{weapon['win_bonus']}%\n"
            f"Крит: {weapon['crit_chance']}%\n"
            f"💰 Ціна: {weapon['price']} NC\n"
            f"🛒 /buyweapon {key}\n\n"
        )

    await message.answer(text)


@router.message(Command("buyweapon"))
async def buy_weapon_cmd(message: Message):
    user_id = message.from_user.id

    register_user(
        user_id,
        message.from_user.username,
        message.from_user.full_name
    )

    args = message.text.split()

    if len(args) != 2:
        await message.answer(
            "❌ Використання:\n"
            "/buyweapon weapon_key"
        )
        return

    weapon_key = args[1]

    if weapon_key not in WEAPONS:
        await message.answer(
            "❌ Такої зброї не існує."
        )
        return

    weapon = WEAPONS[weapon_key]

    price = weapon["price"]

    if get_balance(user_id) < price:
        await message.answer(
            f"❌ Недостатньо NC.\n\n"
            f"Потрібно: {price} NC"
        )
        return

    spend_balance(user_id, price)

    add_inventory_item(
        user_id,
        weapon_key,
        1
    )

    await message.answer(
        f"✅ Зброя куплена!\n\n"
        f"{weapon['name']}\n"
        f"💰 Списано: {price} NC"
    )