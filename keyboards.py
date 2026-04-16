from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚨 RAID ON", callback_data="raid_on"),
                InlineKeyboardButton(text="✅ RAID OFF", callback_data="raid_off"),
            ],
            [
                InlineKeyboardButton(text="⛔ STRICT", callback_data="strict_toggle"),
                InlineKeyboardButton(text="🔒 LOCKDOWN", callback_data="lockdown_toggle"),
            ],
            [
                InlineKeyboardButton(text="📊 STATUS", callback_data="status"),
                InlineKeyboardButton(text="👑 SYNC ADMINS", callback_data="sync_admins"),
            ],
            [
                InlineKeyboardButton(text="📜 JOIN LOGS", callback_data="join_logs"),
                InlineKeyboardButton(text="🔇 MUTES", callback_data="mute_logs"),
            ],
            [
                InlineKeyboardButton(text="⛔ BANS", callback_data="ban_logs"),
                InlineKeyboardButton(text="⚠️ RAID EVENTS", callback_data="raid_events"),
            ],
        ]
    )


def captcha_kb(uid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я не бот", callback_data=f"ok:{uid}")]
        ]
    )