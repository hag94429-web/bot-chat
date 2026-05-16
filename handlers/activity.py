import time

from aiogram import Router, F
from aiogram.types import Message

from database import (
    register_user,
    add_balance,
    get_active_role,
    get_last_msg,
    update_last_msg
)

router = Router()

# ==========================================
# SETTINGS
# ==========================================

COOLDOWN = 30
MIN_TEXT_LENGTH = 5

BASE_REWARD = 5
ROLE_BONUS = 2

# ==========================================
# ACTIVITY HANDLER
# ==========================================

@router.message(F.text, ~F.text.startswith("/"))
async def activity_handler(message: Message):
    if not message.from_user:
        return

    text = message.text.strip()

    # ==========================================
    # SHORT MESSAGE PROTECTION
    # ==========================================

    if len(text) < MIN_TEXT_LENGTH:
        return

    user_id = message.from_user.id

    username = message.from_user.username
    full_name = message.from_user.full_name

    register_user(
        user_id,
        username,
        full_name
    )

    now = int(time.time())

    last_msg_time, last_msg_text = get_last_msg(user_id)

    # ==========================================
    # SAME MESSAGE PROTECTION
    # ==========================================

    if last_msg_text:
        if text.lower() == last_msg_text.lower():
            return

    # ==========================================
    # COOLDOWN PROTECTION
    # ==========================================

    if last_msg_time:
        if now - int(last_msg_time) < COOLDOWN:
            return

    # ==========================================
    # REWARD
    # ==========================================

    reward = BASE_REWARD

    role = get_active_role(user_id)

    if role == "basic":
        reward += ROLE_BONUS

    # ==========================================
    # SAVE LAST MESSAGE
    # ==========================================

    update_last_msg(
        user_id,
        now,
        text
    )

    # ==========================================
    # GIVE MONEY
    # ==========================================

    add_balance(
        user_id,
        reward
    )