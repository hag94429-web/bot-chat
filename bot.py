import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from db import init_db
from handlers.admin import router as admin_router, load_admins
from handlers.joins import router as joins_router
from handlers.messages import router as messages_router


async def main():
    init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.include_router(admin_router)
    dp.include_router(joins_router)
    dp.include_router(messages_router)

    await load_admins(bot)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())