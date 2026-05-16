
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS

from database import (
    register_user,
    get_inventory,
    has_inventory_item,
    equip_weapon,
    get_equipped_weapon,
    add_inventory_item,
    delete_inventory_item,
    add_balance
)

from data.weapons import WEAPONS, rarity_text

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("inventory"))
@router.message(F.text.lower() == "інвентар")
async def inventory_cmd(message: Message):

    user_id = message.from_user.id

    register_user(
        user_id,
        message.from_user.username,
        message.from_user.full_name
    )

    items = get_inventory(user_id)

    equipped = get_equipped_weapon(user_id)

    if not items:

        await message.answer(
            "🎒 Інвентар порожній."
        )

        return

    text = "🎒 <b>Твій інвентар</b>\n\n"

    kb = InlineKeyboardBuilder()

    for item_key, amount in items:

        if item_key not in WEAPONS:
            continue

        weapon = WEAPONS[item_key]

        sell_price = weapon["price"] // 2

        active = ""

        if equipped == item_key:
            active = "✅ Екіпіровано"

        text += (
            f"{weapon['name']} x{amount}\n"
            f"├ Рідкість: {rarity_text(weapon['rarity'])}\n"
            f"├ Бонус перемоги: +{weapon['win_bonus']}%\n"
            f"├ Crit шанс: {weapon['crit_chance']}%\n"
            f"├ Продаж: {sell_price} NC\n"
            f"└ {active}\n\n"
        )

        kb.button(
            text=f"⚔️ Екіпірувати {weapon['name']}",
            callback_data=f"equip_weapon:{item_key}"
        )

        kb.button(
            text=f"💸 Продати {weapon['name']}",
            callback_data=f"sell_weapon:{item_key}"
        )

    kb.adjust(1)

    await message.answer(
        text,
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("equip_weapon:"))
async def equip_weapon_callback(callback: CallbackQuery):

    user_id = callback.from_user.id

    weapon_key = callback.data.split(":")[1]

    register_user(
        user_id,
        callback.from_user.username,
        callback.from_user.full_name
    )

    if weapon_key not in WEAPONS:

        await callback.answer(
            "❌ Зброя не знайдена.",
            show_alert=True
        )

        return

    if not has_inventory_item(user_id, weapon_key):

        await callback.answer(
            "❌ У тебе немає цієї зброї.",
            show_alert=True
        )

        return

    equip_weapon(
        user_id,
        weapon_key
    )

    weapon = WEAPONS[weapon_key]

    await callback.answer(
        "✅ Екіпіровано!",
        show_alert=True
    )

    await callback.message.answer(
        f"⚔️ <b>Зброю екіпіровано!</b>\n\n"
        f"{weapon['name']}\n"
        f"├ Рідкість: {rarity_text(weapon['rarity'])}\n"
        f"├ Бонус: +{weapon['win_bonus']}%\n"
        f"└ Crit: {weapon['crit_chance']}%",
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("sell_weapon:"))
async def sell_weapon_callback(callback: CallbackQuery):

    user_id = callback.from_user.id

    weapon_key = callback.data.split(":")[1]

    register_user(
        user_id,
        callback.from_user.username,
        callback.from_user.full_name
    )

    if weapon_key not in WEAPONS:

        await callback.answer(
            "❌ Зброя не знайдена.",
            show_alert=True
        )

        return

    if not has_inventory_item(user_id, weapon_key):

        await callback.answer(
            "❌ У тебе немає цієї зброї.",
            show_alert=True
        )

        return

    weapon = WEAPONS[weapon_key]

    sell_price = weapon["price"] // 2

    deleted = delete_inventory_item(
        user_id,
        weapon_key
    )

    if not deleted:

        await callback.answer(
            "❌ Не вдалося продати.",
            show_alert=True
        )

        return

    equipped = get_equipped_weapon(user_id)

    if equipped == weapon_key:
        equip_weapon(user_id, "")

    add_balance(
        user_id,
        sell_price
    )

    await callback.answer(
        "✅ Зброя продана!",
        show_alert=True
    )

    await callback.message.answer(
        f"💸 <b>Зброя продана!</b>\n\n"
        f"{weapon['name']}\n"
        f"💰 Отримано: {sell_price} NC",
        parse_mode="HTML"
    )


@router.message(Command("admin_give_weapon"))
async def admin_give_weapon_cmd(message: Message):

    if not is_admin(message.from_user.id):

        await message.answer(
            "❌ Тільки адмін."
        )

        return

    args = message.text.split()

    if len(args) != 3:

        await message.answer(
            "❌ Використання:\n"
            "/admin_give_weapon user_id weapon_key"
        )

        return

    try:
        user_id = int(args[1])

    except ValueError:

        await message.answer(
            "❌ user_id має бути числом."
        )

        return

    weapon_key = args[2]

    if weapon_key not in WEAPONS:

        await message.answer(
            "❌ Такої зброї нема."
        )

        return

    add_inventory_item(
        user_id,
        weapon_key,
        1
    )

    await message.answer(
        f"✅ Видано зброю користувачу {user_id}\n\n"
        f"{WEAPONS[weapon_key]['name']}"
    )