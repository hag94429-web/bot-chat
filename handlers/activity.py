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

COOLDOWN = 30
MIN_TEXT_LENGTH = 5


@router.message(F.text, ~F.text.startswith("/"))
async def activity_handler(message: Message):
    if not message.from_user:
        return

    text = message.text.strip()

    if len(text) < MIN_TEXT_LENGTH:
        return

    user_id = message.from_user.id
    username = message.from_user.username

    register_user(user_id, username)

    last_time, last_text = get_last_msg(user_id)
    now = int(time.time())

    if last_time and now - int(last_time) < COOLDOWN:
        return

    if last_text and last_text.strip().lower() == text.lower():
        return

    role = get_active_role(user_id)

    reward = 2
    if role == "basic":
        reward = 3

    add_balance(user_id, reward)
    update_last_msg(user_id, text)