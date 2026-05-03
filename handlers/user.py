from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import DAILY_REWARD, ADMIN_IDS
from database import (
    register_user,
    get_balance,
    add_balance,
    can_daily,
    set_daily,
    get_top,
    get_logs,
    get_top_donates,
    get_active_emoji,
    get_active_role
)

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def display_name(username, full_name, user_id):
    if username:
        return f"@{username}"
    if full_name:
        return f'<a href="tg://user?id={user_id}">{full_name}</a>'
    return f'<a href="tg://user?id={user_id}">user</a>'


@router.message(Command("start"))
async def start_cmd(message: Message):
    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    await message.answer(
        "🌙 Nyx Coin бот активний!\n\n"
        "/profile — профіль\n"
        "/balance — баланс\n"
        "/daily — щоденний бонус\n"
        "/top — топ по NC\n"
        "/shop — магазин\n"
        "/stars — купити NC за ⭐\n"
        "/uah — купити NC за грн\n"
        "/pay — переказ NC\n"
        "/case — відкрити кейс\n"
        "/topdonate — топ донатерів"
    )


@router.message(Command("profile"))
async def profile_cmd(message: Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username, message.from_user.full_name)

    balance = get_balance(user_id)
    emoji = get_active_emoji(user_id)
    role = get_active_role(user_id)

    await message.answer(
        f"👤 Профіль\n\n"
        f"💰 Баланс: {balance} NC\n"
        f"😊 Emoji статус: {emoji if emoji else 'немає'}\n"
        f"⭐ Роль: {'BASIC VIP' if role == 'basic' else 'немає'}"
    )


@router.message(Command("balance"))
async def balance_cmd(message: Message):
    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(f"💰 Твій баланс: {get_balance(message.from_user.id)} NC")


@router.message(Command("daily"))
async def daily_cmd(message: Message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username, message.from_user.full_name)

    if not can_daily(user_id):
        await message.answer("⏳ Ти вже забирав бонус сьогодні.")
        return

    reward = DAILY_REWARD

    if get_active_role(user_id) == "basic":
        reward = int(reward * 1.1)

    add_balance(user_id, reward)
    set_daily(user_id)

    await message.answer(f"🎁 Ти отримав {reward} NC!")


@router.message(Command("top"))
async def top_cmd(message: Message):
    rows = get_top()

    if not rows:
        await message.answer("🏆 Топ поки порожній.")
        return

    text = "🏆 Топ Nyx Coin:\n\n"

    for i, row in enumerate(rows, start=1):
        username, full_name, user_id, balance = row

        name = display_name(username, full_name, user_id)
        emoji = get_active_emoji(user_id)
        role = get_active_role(user_id)

        emoji_prefix = f"{emoji} " if emoji else ""
        role_prefix = "⭐ [VIP] " if role == "basic" else ""

        text += f"{i}. {emoji_prefix}{role_prefix}{name} — {balance} NC\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("give"))
async def give_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Тільки адмін.")
        return

    args = message.text.split()

    if len(args) != 3:
        await message.answer("❌ Використання: /give user_id сума")
        return

    try:
        user_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        await message.answer("❌ user_id і сума мають бути числами.")
        return

    if amount <= 0:
        await message.answer("❌ Сума має бути більше 0.")
        return

    register_user(user_id)
    add_balance(user_id, amount)

    await message.answer(f"✅ Видано {amount} NC користувачу {user_id}.")


@router.message(Command("logs"))
async def logs_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Тільки адмін.")
        return

    rows = get_logs(15)

    if not rows:
        await message.answer("📊 Логів поки нема.")
        return

    text = "📊 Останні дії:\n\n"

    for row in rows:
        username, user_id, action, amount, item, created_at = row
        name = f"@{username}" if username else f"ID:{user_id}"
        text += f"{name} | {action} | {amount} | {item} | {created_at}\n"

    await message.answer(text)


@router.message(Command("topdonate"))
async def topdonate_cmd(message: Message):
    rows = get_top_donates()

    if not rows:
        await message.answer("💎 Донатів поки нема.")
        return

    text = "💎 Топ донатерів:\n\n"

    for i, row in enumerate(rows, start=1):
        username, user_id, total = row
        name = f"@{username}" if username else f"ID:{user_id}"
        text += f"{i}. {name} — {total}⭐\n"

    await message.answer(text)


@router.message(Command("uah"))
async def uah_cmd(message: Message):
    register_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    kb = InlineKeyboardBuilder()

    kb.button(
        text="💳 Оплатити через Monobank",
        url="https://send.monobank.ua/jar/9mkvsU4izA"
    )

    kb.button(
        text="✅ Я оплатив",
        callback_data="uah_paid"
    )

    kb.adjust(1)

await message.answer(
    "💳 Купівля Nyx Coin за гривні\n\n"
    "5 грн  → 700 NC\n"
    "10 грн → 1200 NC\n"
    "25 грн → 3000 NC\n"
    "50 грн → 6500 NC\n"
    "90 грн → 14000 NC\n"
    "160 грн → 32000 NC\n\n"
    "🎁 Telegram Premium:\n"
    "3 місяці → 1100⭐ або оплата грн за домовленістю\n"
    "6 місяців → 1700⭐ або оплата грн за домовленістю\n\n"
    "1️⃣ Натисни кнопку оплати\n"
    "2️⃣ Оплати потрібну суму\n"
    "3️⃣ Натисни «✅ Я оплатив»\n\n"
    "⚠️ Після перевірки адмін видасть NC або Premium вручну.",
    reply_markup=kb.as_markup()
)


@router.callback_query(F.data == "uah_paid")
async def uah_paid_callback(callback: CallbackQuery):
    user = callback.from_user

    register_user(user.id, user.username, user.full_name)

    if user.username:
        name = f"@{user.username}"
    else:
        name = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'

    for admin_id in ADMIN_IDS:
        try:
            await callback.bot.send_message(
                admin_id,
                "💳 НОВА ОПЛАТА ЗА ГРН\n\n"
                f"👤 Користувач: {name}\n"
                f"🆔 ID: {user.id}\n\n"
                "Перевір Monobank банку:\n"
                "https://send.monobank.ua/jar/9mkvsU4izA\n\n"
                "Після перевірки: \n"
                f"• /give {user.id} сума\n"
                "• aбо видати Premium"
                parse_mode="HTML"
            )
            
        except Exception:
            pass

    await callback.answer("✅ Заявку відправлено адміну.", show_alert=True)

    await callback.message.answer(
        "✅ Заявку відправлено адміну.\n\n"
        "Після перевірки оплати тобі видадуть NC."
    )