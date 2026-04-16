from aiogram import F, Router, types
from aiogram import Bot

from config import CHAT_ID, SPAM_LIMIT, SPAM_WINDOW
from db import get_join_logs, is_wl, log_join
from services import anti_raid
from services.trust import touch_user, get_trust

router = Router()
seen_users = set()


@router.message(F.chat.id == CHAT_ID)
async def message_pipeline(message: types.Message, bot: Bot):
    uid = message.from_user.id

    await anti_raid.maybe_disable_raid()

    if is_wl(uid):
        return

    touch_user(uid)
    trust = get_trust(uid)

    # fallback log if join event never came
    if uid not in seen_users:
        seen_users.add(uid)
        last_logs = get_join_logs(100)
        if not any(row["user_id"] == uid for row in last_logs):
            log_join(uid, "unknown", f"fallback_{trust}")

    # captcha pending users cannot write
    if uid in anti_raid.pending:
        try:
            await message.delete()
        except Exception:
            pass
        return

    # command messages do not go to anti-spam
    if message.text and message.text.startswith("/"):
        return

    # message-based raid detection
    points = anti_raid.add_message_raid_point()
    if points >= 10:
        await anti_raid.enable_raid(f"messages={points}/5s")

    duplicate_count = 0
    if message.text:
        duplicate_count = anti_raid.add_duplicate_text(message.text)
        if anti_raid.should_enable_lockdown_by_duplicates(duplicate_count):
            await anti_raid.enable_lockdown(f"duplicate_text x{duplicate_count}")

    # spam by trust level
    anti_raid.msgs[uid].append(anti_raid.now())
    anti_raid.clean(anti_raid.msgs[uid], SPAM_WINDOW)

    current_limit = SPAM_LIMIT
    if trust == "new":
        current_limit = 8
    elif trust == "regular":
        current_limit = 10

    if len(anti_raid.msgs[uid]) >= current_limit:
        await anti_raid.mute_user(bot, message.chat.id, uid, f"spam_{len(anti_raid.msgs[uid])}/{SPAM_WINDOW}s")