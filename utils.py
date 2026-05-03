import asyncio


async def auto_delete(message, delay=15):
    await asyncio.sleep(delay)

    try:
        await message.delete()
    except Exception:
        pass