import random

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS
from database import (
    register_user,
    get_balance,
    spend_balance,
    add_balance,
    add_log,
    set_emoji_status,
    set_role
)

router = Router()


SHOP_ITEMS = {
    "emoji_1d": ("😊 Emoji/стікер статус 1 день", 300, "emoji"),
    "bonus": ("🎁 Міні-бонус", 500, "bonus"),
    "roulette": ("🎰 Рулетка", 700, "roulette"),
    "role_1d": ("⭐ Базова роль 1 день", 1000, "role_basic"),

    "gray_1d": ("⚪ Сірий префікс 1 день", 1000, "request"),
    "gray_7d": ("⚪ Сірий префікс 7 днів", 5000, "request"),
    "gray_30d": ("⚪ Сірий префікс 30 днів", 12000, "request"),

    "green_1d": ("🟢 Зелений префікс 1 день", 2000, "request"),
    "green_7d": ("🟢 Зелений префікс 7 днів", 9000, "request"),
    "green_30d": ("🟢 Зелений префікс 30 днів", 20000, "request"),

    "game_mafia": ("🎮 Гра дня: Мафія", 3000, "request"),
    "game_uno": ("🎮 Гра дня: Уно", 2500, "request"),
    "game_truth": ("🎮 Гра дня: Правда чи дія", 2000, "request"),

    "ad_30m": ("📌 Реклама в закріп 30 хв", 3000, "request"),
    "ad_1h": ("📌 Реклама в закріп 1 год", 5000, "request"),
    "ad_2h": ("📌 Реклама в закріп 2 год", 8000, "request"),
}


def shop_keyboard():
    kb = InlineKeyboardBuilder()

    for key, item in SHOP_ITEMS.items():
        name, price, _ = item
        kb.button(text=f"{name} — {price} NC", callback_data=f"buy:{key}")

    kb.adjust(1)
    return kb.as_markup()


@router.message(Command("shop"))
async def shop_cmd(message: Message):
    register_user(message.from_user.id, message.from_user.username)

    balance = get_balance(message.from_user.id)

    await message.answer(
        f"🛒 Магазин Nyx Coin\n\n"
        f"💰 Баланс: {balance} NC\n\n"
        f"⚡ Швидкі покупки:\n"
        f"😊 Emoji — 300 NC на 1 день\n"
        f"🎁 Міні-бонус — 500 NC\n"
        f"🎰 Рулетка — 700 NC\n"
        f"⭐ BASIC VIP — 1000 NC на 1 день\n\n"
        f"⭐ BASIC VIP дає:\n"
        f"— значок у /top\n"
        f"— +10% до /daily\n\n"
        f"⚪ Сірий преф: день / тиждень / місяць\n"
        f"🟢 Зелений преф: день / тиждень / місяць\n\n"
        f"🎮 Ігри дня: Мафія / Уно / Правда чи дія\n"
        f"📌 Реклама: 30 хв / 1 год / 2 год",
        reply_markup=shop_keyboard()
    )


@router.callback_query(F.data.startswith("buy:"))
async def buy_item(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username

    register_user(user_id, username)

    item_key = callback.data.split(":")[1]

    if item_key not in SHOP_ITEMS:
        await callback.answer("Товар не знайдено.", show_alert=True)
        return

    name, price, item_type = SHOP_ITEMS[item_key]

    if not spend_balance(user_id, price):
        await callback.answer(
            f"❌ Недостатньо NC.\nБаланс: {get_balance(user_id)} NC",
            show_alert=True
        )
        return

    add_log(user_id, username, "buy", price, name)

    if item_type == "emoji":
        emoji = random.choice(["🔥", "💎", "😈", "👑", "⚡", "🌙", "💀"])
        set_emoji_status(user_id, emoji)
        add_log(user_id, username, "emoji_status", price, emoji)

        await callback.message.answer(
            f"✅ Emoji статус активовано!\n\n"
            f"Твій статус: {emoji}\n"
            f"⏳ Діє: 1 день\n"
            f"🏆 Буде видно біля твого ніку в /top."
        )

    elif item_type == "role_basic":
        set_role(user_id, "basic")
        add_log(user_id, username, "role_basic", price, "BASIC VIP 1 день")

        await callback.message.answer(
            f"✅ BASIC VIP активовано!\n\n"
            f"⏳ Діє: 1 день\n"
            f"🏆 У /top буде значок ⭐ [VIP]\n"
            f"🎁 /daily дає +10% бонус."
        )

    elif item_type == "bonus":
        reward = random.choice([200, 300, 400, 500, 600])
        add_balance(user_id, reward)
        add_log(user_id, username, "bonus_reward", reward, "Міні-бонус")

        await callback.message.answer(
            f"🎁 Міні-бонус відкрито!\n\n"
            f"Вартість: {price} NC\n"
            f"Випало: {reward} NC"
        )

    elif item_type == "roulette":
        reward = random.choices(
            population=[300, 500, 700, 1200, 2000, 4000],
            weights=[35, 25, 20, 12, 6, 2],
            k=1
        )[0]

        add_balance(user_id, reward)
        add_log(user_id, username, "roulette_reward", reward, "Рулетка")

        await callback.message.answer(
            f"🎰 Рулетка!\n\n"
            f"Вартість: {price} NC\n"
            f"Випало: {reward} NC"
        )

    else:
        await callback.message.answer(
            f"✅ Покупка успішна!\n\n"
            f"Товар: {name}\n"
            f"Списано: {price} NC\n\n"
            f"⏳ Адмін скоро видасть покупку."
        )

        for admin_id in ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"🛒 Нова покупка!\n\n"
                    f"👤 Користувач: @{username if username else 'без username'}\n"
                    f"🆔 ID: {user_id}\n"
                    f"📦 Товар: {name}\n"
                    f"💰 Ціна: {price} NC"
                )
            except Exception:
                pass

    await callback.answer("Готово!")