import logging

from aiogram import Bot

import notifier
import settings
import storage
from checkers import CHECKERS
from config import ADMIN_ID

logger = logging.getLogger(__name__)


async def run_check(bot: Bot, manual: bool = False) -> str | None:
    state = storage.load_state()
    manual_messages: list[str] = []

    for checker in CHECKERS:
        try:
            offers = await checker.fetch_available()
        except Exception:
            logger.exception("Checker %s failed", checker.name)
            if manual:
                manual_messages.append(f"{checker.name}: ошибка проверки, см. логи.")
            continue

        current_keys = {offer.key for offer in offers}
        is_first_run = checker.name not in state
        previous_keys = set(state.get(checker.name, []))
        new_keys = current_keys - previous_keys
        state[checker.name] = sorted(current_keys)

        if manual:
            manual_messages.append(notifier.format_status(checker.name, offers))
        elif new_keys and not is_first_run and settings.is_enabled(checker.name):
            new_offers = [o for o in offers if o.key in new_keys]
            await bot.send_message(
                ADMIN_ID,
                notifier.format_new_offers(checker.name, new_offers),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )

    storage.save_state(state)

    if manual:
        return "\n\n".join(manual_messages)
    return None
