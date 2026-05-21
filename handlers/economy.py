import asyncio
import random
import time

from aiogram import Router, F
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
    set_basic_role,
    get_user_by_username
)
from utils import auto_delete

router = Router()

PAY_MIN = 50
PAY_COOLDOWN = 10

CASE_PRICE = 600
CASE_COOLDOWN = 20


@router.message(Command("pay"))
async def pay_cmd(message: Message):
    sender_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    register_user(sender_id, username, full_name)

    args = message.text.split()

    if len(args) != 3:
        msg = await message.answer(
            "❌ Використання:\n"
            "/pay @username сума\n"
            "або\n"
            "/pay user_id сума"
        )
        asyncio.create_task(auto_delete(msg, 10))
        return

    target = args[1]

    try:
        amount = int(args[2])
    except ValueError:
        msg = await message.answer("❌ Сума має бути числом.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    if amount < PAY_MIN:
        msg = await message.answer(
            f"❌ Мінімальний переказ: {PAY_MIN} NC."
        )
        asyncio.create_task(auto_delete(msg, 10))
        return

    if target.startswith("@"):

        user_row = get_user_by_username(target)

        if not user_row:
            msg = await message.answer(
                "❌ Я не знаю цього користувача.\n\n"
                "Він має хоча б раз написати в чат."
            )
            asyncio.create_task(auto_delete(msg, 10))
            return

        receiver_id = user_row[0]
        receiver_username = user_row[1]
        receiver_full_name = user_row[2]

    else:

        try:
            receiver_id = int(target)
        except ValueError:
            msg = await message.answer(
                "❌ Використання:\n"
                "/pay @username сума\n"
                "або\n"
                "/pay user_id сума"
            )
            asyncio.create_task(auto_delete(msg, 10))
            return

        receiver_username = None
        receiver_full_name = None

    if receiver_id == sender_id:
        msg = await message.answer("❌ Не можна переказати собі.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    now = int(time.time())
    last_pay = get_last_pay_time(sender_id)

    if last_pay and now - int(last_pay) < PAY_COOLDOWN:
        msg = await message.answer(
            "⏳ Зачекай перед наступним переказом."
        )
        asyncio.create_task(auto_delete(msg, 10))
        return

    if not spend_balance(sender_id, amount):
        msg = await message.answer("❌ Недостатньо NC.")
        asyncio.create_task(auto_delete(msg, 10))
        return

    register_user(
        receiver_id,
        receiver_username,
        receiver_full_name
    )

    add_balance(receiver_id, amount)

    set_last_pay_time(sender_id)

    add_log(
        sender_id,
        username,
        "pay_send",
        amount,
        f"to {receiver_id}"
    )

    add_log(
        receiver_id,
        receiver_username,
        "pay_receive",
        amount,
        f"from {sender_id}"
    )

    if receiver_username:
        receiver_name = f"@{receiver_username}"
    elif receiver_full_name:
        receiver_name = receiver_full_name
    else:
        receiver_name = f"ID:{receiver_id}"

    await message.answer(
        f"💸 <b>Переказ виконано!</b>\n\n"
        f"👤 Отримувач: {receiver_name}\n"
        f"💰 Сума: {amount} NC",
        parse_mode="HTML"
    )


@router.message(Command("case"))
async def case_cmd(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    register_user(user_id, username, message.from_user.full_name)

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

    msg = await message.answer("📦 Відкриваємо кейс...")

    frames = [
        "📦 ░░░░░░",
        "📦 ███░░░",
        "📦 ██████",
    ]

    for frame in frames:
        await asyncio.sleep(0.5)
        try:
            await msg.edit_text(frame)
        except:
            pass

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

        if value >= 3000:
            try:
                await msg.edit_text("💥 ДЖЕКПОТ 💥")
                await asyncio.sleep(0.6)
            except:
                pass

            text = f"💥 ДЖЕКПОТ!!!\n\n💰 Випало: {value} NC"
        else:
            text = f"🎁 Випало: {value} NC"

    elif reward_type == "emoji":
        emoji = random.choice(["🔥", "💎", "👑", "⚡"])
        set_emoji_status(user_id, emoji)

        text = f"😊 Emoji: {emoji}"

    elif reward_type == "vip":
        set_basic_role(user_id, 1)
        text = "⭐ VIP на 1 день!"

    else:
        text = "😢 Нічого не випало"

    try:
        await msg.edit_text(text)
    except:
        pass

    asyncio.create_task(auto_delete(msg, 20))

@router.message(F.text.lower() == "кейс")
async def case_text(message: Message):
    await case_cmd(message)
    