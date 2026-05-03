import asyncio
import random
import time

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    register_user,
    get_balance,
    add_balance,
    spend_balance,
    add_log,
    get_last_pay_time,
    set_last_pay_time,
    get_last_case_time,
    set_last_case_time,
    set_emoji_status,
    set_basic_role
)
from utils import auto_delete

router = Router()

PAY_MIN = 50
PAY_COOLDOWN = 10

CASE_PRICE = 600
CASE_COOLDOWN = 0


@router.message(Command("pay"))
async def pay_cmd(message: Message):
    sender_id = message.from_user.id
    username = message.from_user.username

    register_user(
        sender_id,
        username,
        message.from_user.full_name
    )

    args = message.text.split()

    if len(args) != 3:
        msg = await message.answer("❌ Використання: /pay user_id сума")
        asyncio.create_task(auto_delete(msg, 10))
        return

    try:
        receiver_id = int(args[1])
        amount = int(args[2])
    except ValueError:
        msg = await message.answer("❌ user_id і сума мають бути числами.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    if receiver_id == sender_id:
        msg = await message.answer("❌ Не можна переказати собі.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    if amount < PAY_MIN:
        msg = await message.answer(f"❌ Мінімальний переказ: {PAY_MIN} NC.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    now = int(time.time())
    last_pay = get_last_pay_time(sender_id)

    if last_pay and now - int(last_pay) < PAY_COOLDOWN:
        msg = await message.answer("⏳ Зачекай перед наступним переказом.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    if not spend_balance(sender_id, amount):
        msg = await message.answer("❌ Недостатньо NC.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    register_user(receiver_id)
    add_balance(receiver_id, amount)
    set_last_pay_time(sender_id)

    add_log(sender_id, username, "pay_send", amount, f"to {receiver_id}")
    add_log(receiver_id, None, "pay_receive", amount, f"from {sender_id}")

    await message.answer(f"✅ Переказано {amount} NC користувачу {receiver_id}.")


@router.message(Command("case"))
async def case_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    register_user(
        user_id,
        username,
        message.from_user.full_name
    )

    now = int(time.time())
    last_case = get_last_case_time(user_id)

    if last_case and now - int(last_case) < CASE_COOLDOWN:
        msg = await message.answer("⏳ Зачекай перед наступним кейсом.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    if not spend_balance(user_id, CASE_PRICE):
        msg = await message.answer(
            f"❌ Кейc коштує {CASE_PRICE} NC.\n"
            f"У тебе: {get_balance(user_id)} NC."
        )
        asyncio.create_task(auto_delete(msg, 10))
        return

    set_last_case_time(user_id)

    reward = random.choices(
        population=[
            ("money", 200),
            ("money", 500),
            ("money", 1000),
            ("money", 3000),
            ("emoji", 0),
            ("vip", 0),
            ("nothing", 0)
        ],
        weights=[40, 28, 18, 4, 6, 2, 2],
        k=1
    )[0]

    reward_type, value = reward

    add_log(user_id, username, "case_open", CASE_PRICE, "case")

    if reward_type == "money":
        add_balance(user_id, value)
        add_log(user_id, username, "case_reward", value, "NC")

        msg = await message.answer(
            f"🎁 Ти відкрив кейс за {CASE_PRICE} NC\n\n"
            f"💰 Випало: {value} NC"
        )

    elif reward_type == "emoji":
        emoji = random.choice(["🔥", "💎", "👑", "⚡"])
        set_emoji_status(user_id, emoji)
        add_log(user_id, username, "case_reward", 0, f"emoji {emoji}")

        msg = await message.answer(
            f"🎁 Ти відкрив кейс за {CASE_PRICE} NC\n\n"
            f"😊 Випав emoji статус: {emoji} на 1 день"
        )

    elif reward_type == "vip":
        set_basic_role(user_id, 1)
        add_log(user_id, username, "case_reward", 0, "BASIC VIP")

        msg = await message.answer(
            f"🎁 Ти відкрив кейс за {CASE_PRICE} NC\n\n"
            f"⭐ Випав BASIC VIP на 1 день"
        )

    else:
        msg = await message.answer(
            f"🎁 Ти відкрив кейс за {CASE_PRICE} NC\n\n"
            f"😢 Нічого не випало."
        )

    asyncio.create_task(auto_delete(msg, 20))