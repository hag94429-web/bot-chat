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

    "prem_3m": {"stars": 1100, "premium": "Telegram Premium 3 місяці"},
    "prem_6m": {"stars": 1700, "premium": "Telegram Premium 6 місяців"},
}


def stars_keyboard():
    kb = InlineKeyboardBuilder()

    kb.button(text="⭐ 5 → 700 NC", callback_data="stars:s5")
    kb.button(text="⭐ 10 → 1200 NC", callback_data="stars:s10")
    kb.button(text="⭐ 25 → 3000 NC", callback_data="stars:s25")
    kb.button(text="⭐ 50 → 6500 NC", callback_data="stars:s50")
    kb.button(text="🔥 ⭐ 100 → 14000 NC", callback_data="stars:s100")
    kb.button(text="💎 ⭐ 200 → 32000 NC", callback_data="stars:s200")

    kb.button(text="🎁 Premium 3 міс — 1100⭐", callback_data="stars:prem_3m")
    kb.button(text="🎁 Premium 6 міс — 1700⭐", callback_data="stars:prem_6m")

    kb.adjust(1)
    return kb.as_markup()


@router.message(Command("stars"))
async def stars_cmd(message: Message):
    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    await message.answer(
        "⭐ Купівля за Telegram Stars\n\n"
        "💰 Nyx Coin:\n"
        "5⭐ = 700 NC\n"
        "10⭐ = 1200 NC\n"
        "25⭐ = 3000 NC\n"
        "50⭐ = 6500 NC\n"
        "100⭐ = 14000 NC 🔥\n"
        "200⭐ = 32000 NC 💎\n\n"
        "🎁 Telegram Premium:\n"
        "1100⭐ = Premium 3 місяці\n"
        "1700⭐ = Premium 6 місяців\n\n"
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

    if "coins" in pack:
        coins = pack["coins"]

        await callback.message.answer_invoice(
            title=f"{coins} Nyx Coin",
            description=f"Поповнення балансу на {coins} NC",
            payload=f"nyxcoins:{coins}:{stars}",
            currency="XTR",
            prices=[LabeledPrice(label=f"{coins} Nyx Coin", amount=stars)],
            provider_token=""
        )

    elif "premium" in pack:
        premium = pack["premium"]

        await callback.message.answer_invoice(
            title=premium,
            description="Заявка на Telegram Premium. Після оплати адмін видасть Premium вручну.",
            payload=f"premium:{pack_key}:{stars}",
            currency="XTR",
            prices=[LabeledPrice(label=premium, amount=stars)],
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

    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    if payload.startswith("nyxcoins:"):
        parts = payload.split(":")
        coins = int(parts[1])
        stars = int(parts[2])

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
            f"💰 Додано: {coins} NC"
        )

        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"💎 Новий донат!\n\n"
                    f"👤 @{message.from_user.username if message.from_user.username else message.from_user.full_name}\n"
                    f"🆔 ID: {message.from_user.id}\n"
                    f"⭐ Stars: {stars}\n"
                    f"💰 Видано: {coins} NC"
                )
            except Exception:
                pass

    elif payload.startswith("premium:"):
        parts = payload.split(":")
        pack_key = parts[1]
        stars = int(parts[2])
        premium = STAR_PACKS[pack_key]["premium"]

        add_log(
            message.from_user.id,
            message.from_user.username,
            "premium_request",
            stars,
            premium
        )

        await message.answer(
            f"✅ Оплата Premium прийнята!\n\n"
            f"🎁 Товар: {premium}\n"
            f"⭐ Оплачено: {stars} Stars\n\n"
            f"⏳ Адмін перевірить оплату і видасть Premium вручну."
        )

        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🎁 Нова заявка на Telegram Premium!\n\n"
                    f"👤 @{message.from_user.username if message.from_user.username else message.from_user.full_name}\n"
                    f"🆔 ID: {message.from_user.id}\n"
                    f"📦 Товар: {premium}\n"
                    f"⭐ Оплачено: {stars} Stars\n\n"
                    f"Видай Premium вручну."
                )
            except Exception:
                pass