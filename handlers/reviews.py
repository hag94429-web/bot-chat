from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

CHANNEL_LINK = "https://t.me/wtxkda"


@router.message(Command("reviews"))
@router.message(F.text.lower() == "відгуки")
async def reviews_cmd(message: Message):

    kb = InlineKeyboardBuilder()

    kb.button(
        text="💬 Перейти до відгуків",
        url=CHANNEL_LINK
    )

    kb.adjust(1)

    await message.answer(
        "🌟 <b>ВІДГУКИ ПРО 𝑻𝑶𝑿𝑰𝑪 𝑺𝑨𝑽𝑨𝑮𝑬 𝑩𝑶𝑻</b>\n\n"

        "📌 Тут публікуються:\n"
        "├ 💎 донати\n"
        "├ 🎁 видача Premium\n"
        "└ 🏆 відгуки користувачів\n\n"

        "👇 Натисни кнопку нижче:",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )