
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import (
    register_user,
    get_balance,
    spend_balance,
    add_inventory_item,
    equip_weapon
)

from data.weapons import WEAPONS

router = Router()

@router.message(Command("weaponshop"))
@router.message(F.text.lower() == "магазин зброї")
async def weapon_shop_cmd(message: Message):
    user_id = message.from_user.id

    register_user(
        user_id,
        message.from_user.username,
        message.from_user.full_name
    )

    text = (
        "⚔️ <b>МАГАЗИН ЗБРОЇ</b>\n\n"
    )

    kb = InlineKeyboardBuilder()

    for weapon_key, weapon in WEAPONS.items():

        text += (
            f"{weapon['name']}\n"
            f"├ Рідкість: {weapon['rarity']}\n"
            f"├ Бонус: +{weapon['win_bonus']}%\n"
            f"├ Crit: {weapon['crit_chance']}%\n"
            f"└ 💰 {weapon['price']} NC\n\n"
        )

        kb.button(
            text=f"🛒 Купити {weapon['name']}",
            callback_data=f"buy_weapon:{weapon_key}"
        )

    kb.adjust(1)

    await message.answer(
        text,
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("buy_weapon:"))
async def buy_weapon_callback(callback: CallbackQuery):
    user_id = callback.from_user.id

    register_user(
        user_id,
        callback.from_user.username,
        callback.from_user.full_name
    )

    weapon_key = callback.data.split(":")[1]

    if weapon_key not in WEAPONS:
        await callback.answer(
            "❌ Зброя не знайдена.",
            show_alert=True
        )
        return

    weapon = WEAPONS[weapon_key]

    price = weapon["price"]

    if get_balance(user_id) < price:
        await callback.answer(
            "❌ Недостатньо NC.",
            show_alert=True
        )
        return

    spend_balance(
        user_id,
        price
    )

    add_inventory_item(
        user_id,
        weapon_key,
        1
    )

    # AUTO EQUIP
    equip_weapon(
        user_id,
        weapon_key
    )

    await callback.answer(
        "✅ Зброя куплена!",
        show_alert=True
    )

    await callback.message.answer(
        f"✅ <b>Зброя успішно куплена!</b>\n\n"

        f"{weapon['name']}\n"
        f"💰 Списано: {price} NC\n"
        f"⚡ Бонус: +{weapon['win_bonus']}%\n"
        f"🔥 Crit: {weapon['crit_chance']}%\n\n"

        "🎒 Зброя додана в інвентар\n"
        "✅ Автоматично екіпірована",

        parse_mode="HTML"
    )