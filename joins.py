import asyncio
import logging

from aiogram import F, Router, types
from aiogram import Bot

from config import CAPTCHA_TIMEOUT, CHAT_ID
from db import is_wl, log_join
from keyboards import captcha_kb
from services import anti_raid

router = Router()


async def captcha_timeout(bot: Bot, chat_id: int, uid: int):
    await asyncio.sleep(CAPTCHA_TIMEOUT)
    if uid in anti_raid.pending:
        anti_raid.pending.pop(uid, None)
        await anti_raid.ban_user(bot, chat_id, uid, "captcha_timeout")


@router.message(F.chat.id == CHAT_ID, F.new_chat_members)
async def join_handler(message: types.Message, bot: Bot):
    global_count = anti_raid.add_join()

    for u in message.new_chat_members:
        link = message.invite_link.invite_link if message.invite_link else "unknown"
        typ, limit = anti_raid.get_type(link)
        invite_count = anti_raid.add_invite_join(link)

        logging.warning("JOIN HANDLER WORKED uid=%s link=%s type=%s", u.id, link, typ)

        if u.is_bot:
            log_join(u.id, link, "bot")
            await anti_raid.ban_user(bot, message.chat.id, u.id, "bot_join")
            continue

        if is_wl(u.id):
            log_join(u.id, link, "whitelist")
            continue

        log_join(u.id, link, typ)

        if global_count >= 5 or invite_count >= limit:
            await anti_raid.enable_raid(f"joins global={global_count} invite={invite_count} type={typ}")

        if typ in {"top", "ads", "external"} and invite_count >= limit and link != "unknown":
            try:
                await bot.revoke_chat_invite_link(message.chat.id, link)
            except Exception:
                pass

        if anti_raid.lockdown_mode:
            await anti_raid.mute_user(bot, message.chat.id, u.id, "lockdown_new_user")
            continue

        if anti_raid.strict_mode and anti_raid.raid_mode:
            await anti_raid.ban_user(bot, message.chat.id, u.id, "strict_raid_join")
            continue

        if anti_raid.need_captcha(global_count, invite_count, limit):
            await anti_raid.mute_user(bot, message.chat.id, u.id, "captcha_pending")
            msg = await message.answer(
                f"{u.first_name}, підтверди що ти не бот",
                reply_markup=captcha_kb(u.id),
            )
            anti_raid.pending[u.id] = True
            asyncio.create_task(captcha_timeout(bot, message.chat.id, u.id))
            asyncio.create_task(auto_delete_message(bot, msg.chat.id, msg.message_id, 45))


async def auto_delete_message(bot: Bot, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass