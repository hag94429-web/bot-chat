from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_IDS
from database import register_user, add_balance, add_log

router = Router()


STAR_PACKS = {
    "s5": {"stars": 5, "coins": 700},
    "s10": {"stars": 10, "coins": 1200},
    "s25": {"stars": 25, "coins": 3000},
    "s50": {"stars": 50, "coins": 6500},
    "s100": {"stars": 100, "coins": 14000},
    "s200": {"stars": 200, "coins": 32000},
}


def stars_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(text="⭐ 5 → 700 NC", callback_data="stars:s5")
    kb.button(text="⭐ 10 → 1200 NC", callback_data="stars:s10")
    kb.button(text="⭐ 25 → 3000 NC", callback_data="stars:s25")
    kb.button(text="⭐ 50 → 6500 NC", callback_data="stars:s50")
    kb.button(text="🔥 ⭐ 100 → 14000 NC", callback_data="stars:s100")
    kb.button(text="💎 ⭐ 200 → 32000 NC", callback_data="stars:s200")

    kb.adjust(1)
    return kb.as_markup()


@router.message(Command("stars"))
async def stars_cmd(message: Message):
    register_user(message.from_user.id, message.from_user.username)

    await message.answer(
        "⭐ Купівля Nyx Coin за Telegram Stars\n\n"
        "5⭐ = 700 NC\n"
        "10⭐ = 1200 NC\n"
        "25⭐ = 3000 NC\n"
        "50⭐ = 6500 NC\n"
        "100⭐ = 14000 NC 🔥\n"
        "200⭐ = 32000 NC 💎\n\n"
        "Обери пакет:",
        reply_markup=stars_keyboard()
    )


@router.callback_query(F.data.startswith("stars:"))
async def buy_stars_pack(callback: CallbackQuery):
    pack_key = callback.data.split(":")[1]
    pack = STAR_PACKS.get(pack_key)

    if not pack:
        await callback.answer("Пакет не знайдено.", show_alert=True)
        return

    stars = pack["stars"]
    coins = pack["coins"]

    await callback.message.answer_invoice(
        title=f"{coins} Nyx Coin",
        description=f"Поповнення балансу на {coins} NC",
        payload=f"nyxcoins:{coins}:{stars}",
        currency="XTR",
        prices=[
            LabeledPrice(label=f"{coins} Nyx Coin", amount=stars)
        ],
        provider_token=""
    )

    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment

    if payment.currency != "XTR":
        return

    payload = payment.invoice_payload

    if not payload.startswith("nyxcoins:"):
        return

    parts = payload.split(":")
    coins = int(parts[1])
    stars = int(parts[2]) if len(parts) >= 3 else payment.total_amount

    register_user(message.from_user.id, message.from_user.username)
    add_balance(message.from_user.id, coins)

    add_log(
        message.from_user.id,
        message.from_user.username,
        "donate_stars",
        stars,
        f"+{coins} NC"
    )

    await message.answer(
        f"✅ Оплата успішна!\n\n"
        f"⭐ Оплачено: {stars} Stars\n"
        f"💰 Додано: {coins} NC\n"
        f"Баланс оновлено."
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"💎 Новий донат!\n\n"
                f"👤 Користувач: @{message.from_user.username if message.from_user.username else 'без username'}\n"
                f"🆔 ID: {message.from_user.id}\n"
                f"⭐ Stars: {stars}\n"
                f"💰 Видано: {coins} NC"
            )
        except Exception:
            pass