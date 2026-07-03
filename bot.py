import asyncio
import logging

from aiogram import Bot, Dispatcher

import monitor
from config import BOT_TOKEN, CHECK_INTERVAL_SECONDS
from handlers import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def periodic_loop(bot: Bot) -> None:
    while True:
        try:
            await monitor.run_check(bot, manual=False)
        except Exception:
            logger.exception("Periodic check failed")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    asyncio.create_task(periodic_loop(bot))

    logger.info("Bot started, checking every %s seconds", CHECK_INTERVAL_SECONDS)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
