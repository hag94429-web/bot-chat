import asyncio
import random
import time

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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
    set_basic_role,
    get_last_bonus_time,
    set_last_bonus_time,
    get_last_roulette_time,
    set_last_roulette_time
)
from utils import auto_delete

router = Router()

BONUS_COOLDOWN = 60
ROULETTE_COOLDOWN = 60


class AdState(StatesGroup):
    waiting_text = State()


ITEMS = {
    "emoji_1d": ("😊 Emoji статус 1 день", 300, "emoji"),
    "bonus": ("🎁 Міні-бонус", 500, "bonus"),
    "roulette": ("🎰 Рулетка", 1000, "roulette"),

    "role_1d": ("⭐ BASIC VIP 1 день", 1000, "role_basic", 1),
    "role_7d": ("⭐ BASIC VIP 7 днів", 5000, "role_basic", 7),
    "role_30d": ("⭐ BASIC VIP 30 днів", 12000, "role_basic", 30),

    "gray_1d": ("⚪ Сірий префікс 1 день", 1000, "request"),
    "gray_7d": ("⚪ Сірий префікс 7 днів", 5000, "request"),
    "gray_30d": ("⚪ Сірий префікс 30 днів", 12000, "request"),

    "green_1d": ("🟢 Зелений префікс 1 день", 2000, "request"),
    "green_7d": ("🟢 Зелений префікс 7 днів", 9000, "request"),
    "green_30d": ("🟢 Зелений префікс 30 днів", 20000, "request"),

    "ad_30m": ("📌 Реклама 30 хв", 3000, "ad", 1800),
    "ad_1h": ("📌 Реклама 1 год", 5000, "ad", 3600),
    "ad_2h": ("📌 Реклама 2 год", 8000, "ad", 7200),
}


def main_shop_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⚡ Швидкі покупки", callback_data="shopcat:fast")
    kb.button(text="⭐ Ролі", callback_data="shopcat:roles")
    kb.button(text="📌 Реклама", callback_data="shopcat:ads")
    kb.adjust(1)
    return kb.as_markup()


def category_kb(category):
    kb = InlineKeyboardBuilder()

    if category == "fast":
        keys = ["emoji_1d", "bonus", "roulette"]
    elif category == "roles":
        keys = [
            "role_1d", "role_7d", "role_30d",
            "gray_1d", "gray_7d", "gray_30d",
            "green_1d", "green_7d", "green_30d"
        ]
    elif category == "ads":
        keys = ["ad_30m", "ad_1h", "ad_2h"]
    else:
        keys = []

    for key in keys:
        item = ITEMS[key]
        kb.button(text=f"{item[0]} — {item[1]} NC", callback_data=f"buy:{key}")

    kb.button(text="⬅️ Назад", callback_data="shop:back")
    kb.adjust(1)
    return kb.as_markup()


@router.message(Command("shop"))
async def shop_cmd(message: Message):
    register_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    await message.answer(
        f"🛒 Магазин Nyx Coin\n\n"
        f"💰 Баланс: {get_balance(message.from_user.id)} NC\n\n"
        f"Обери категорію:",
        reply_markup=main_shop_kb()
    )


@router.callback_query(F.data == "shop:back")
async def shop_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛒 Магазин Nyx Coin\n\nОбери категорію:",
        reply_markup=main_shop_kb()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("shopcat:"))
async def shop_category(callback: CallbackQuery):
    category = callback.data.split(":")[1]

    titles = {
        "fast": "⚡ Швидкі покупки",
        "roles": "⭐ Ролі",
        "ads": "📌 Реклама"
    }

    await callback.message.edit_text(
        f"{titles.get(category, 'Магазин')}\n\nОбери товар:",
        reply_markup=category_kb(category)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def buy_item(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    username = callback.from_user.username
    full_name = callback.from_user.full_name

    register_user(user_id, username, full_name)

    item_key = callback.data.split(":")[1]

    if item_key not in ITEMS:
        await callback.answer("Товар не знайдено.", show_alert=True)
        return

    item = ITEMS[item_key]
    name = item[0]
    price = item[1]
    item_type = item[2]

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
            f"🏆 Буде видно в /top."
        )

    elif item_type == "role_basic":
        days = item[3]
        set_basic_role(user_id, days)
        add_log(user_id, username, "role_basic", price, f"BASIC VIP {days} дн.")

        await callback.message.answer(
            f"✅ BASIC VIP активовано!\n\n"
            f"⏳ Діє: {days} дн.\n"
            f"🏆 У /top буде ⭐ [VIP]\n"
            f"🎁 /daily дає +10%\n"
            f"💬 За повідомлення: +3 NC."
        )

    elif item_type == "bonus":
        now = int(time.time())
        last_bonus = get_last_bonus_time(user_id)

        if last_bonus and now - int(last_bonus) < BONUS_COOLDOWN:
            add_balance(user_id, price)
            await callback.answer("⏳ Міні-бонус можна раз на 60 секунд.", show_alert=True)
            return

        set_last_bonus_time(user_id)

        reward = random.choice([200, 300, 400, 500, 600])
        add_balance(user_id, reward)
        add_log(user_id, username, "bonus_reward", reward, "Міні-бонус")

        msg = await callback.message.answer(
            f"🎁 Міні-бонус відкрито!\n\n"
            f"Вартість: {price} NC\n"
            f"Випало: {reward} NC"
        )
        asyncio.create_task(auto_delete(msg, 15))

elif item_type == "roulette":
    now = int(time.time())
    last_roulette = get_last_roulette_time(user_id)

    if last_roulette and now - int(last_roulette) < ROULETTE_COOLDOWN:
        add_balance(user_id, price)
        await callback.answer("⏳ Рулетку можна крутити раз на 60 секунд.", show_alert=True)
        return

    set_last_roulette_time(user_id)

    msg = await callback.message.answer("🎰 Запускаємо рулетку...")

    frames = [
        "🎰 | 🍒 💎 🔥 |",
        "🎰 | 💎 🔥 🍒 |",
        "🎰 | 🔥 🍒 💎 |",
    ]

    for frame in frames:
        await asyncio.sleep(0.5)
        try:
            await msg.edit_text(frame)
        except Exception:
            pass

    reward = random.choices(
        population=[300, 500, 700, 1200, 2000, 4000],
        weights=[35, 25, 20, 12, 6, 2],
        k=1
    )[0]

    add_balance(user_id, reward)
    add_log(user_id, username, "roulette_reward", reward, "roulette")

    if reward >= 4000:
        try:
            await msg.edit_text("💥 JACKPOT 💥")
            await asyncio.sleep(0.6)
        except Exception:
            pass

        text = (
            f"💥 ДЖЕКПОТ РУЛЕТКИ!\n\n"
            f"💰 Випало: {reward} NC"
        )

    elif reward >= 2000:
        text = (
            f"🔥 Великий виграш!\n\n"
            f"🎰 Випало: {reward} NC"
        )

    else:
        text = (
            f"🎰 Рулетка завершена!\n\n"
            f"💰 Випало: {reward} NC"
        )

    try:
        await msg.edit_text(text)
    except Exception:
        pass

    asyncio.create_task(auto_delete(msg, 15))

    elif item_type == "ad":
        duration = item[3]

        if callback.message.chat.type == "private":
            add_balance(user_id, price)
            await callback.message.answer(
                "❌ Рекламу треба купувати в чаті, де бот має права на закріп."
            )
            await callback.answer()
            return

        await state.set_state(AdState.waiting_text)
        await state.update_data(
            chat_id=callback.message.chat.id,
            duration=duration,
            name=name,
            price=price
        )

        await callback.message.answer(
            f"📌 Реклама оплачена: {name}\n\n"
            f"✍️ Надішли текст реклами наступним повідомленням.\n"
            f"Бот опублікує його і закріпить."
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
                    f"👤 @{username if username else 'без username'}\n"
                    f"🆔 ID: {user_id}\n"
                    f"📦 Товар: {name}\n"
                    f"💰 Ціна: {price} NC"
                )
            except Exception:
                pass

    await callback.answer("Готово!")


@router.message(AdState.waiting_text)
async def receive_ad_text(message: Message, state: FSMContext):
    data = await state.get_data()

    chat_id = data["chat_id"]
    duration = data["duration"]
    name = data["name"]

    ad_text = message.text

    if not ad_text:
        await message.answer("❌ Надішли саме текст реклами.")
        return

    ad_message = await message.bot.send_message(
        chat_id,
        f"📌 Реклама\n\n{ad_text}"
    )

    try:
        await message.bot.pin_chat_message(
            chat_id=chat_id,
            message_id=ad_message.message_id,
            disable_notification=True
        )
    except Exception:
        await message.answer("❌ Не зміг закріпити. Дай боту право закріплювати повідомлення.")
        await state.clear()
        return

    await message.answer(f"✅ Реклама закріплена: {name}")
    await state.clear()

    await asyncio.sleep(duration)

    try:
        await message.bot.unpin_chat_message(
            chat_id=chat_id,
            message_id=ad_message.message_id
        )
    except Exception:
        pass