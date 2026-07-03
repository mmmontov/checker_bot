from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import monitor
import settings
from checkers import CHECKERS

router = Router()

CHECK_BUTTON_TEXT = "🔍 Проверить наличие"
CHECK_CALLBACK_DATA = "check_now"
SETTINGS_BUTTON_TEXT = "⚙️ Уведомления"
SETTINGS_CALLBACK_DATA = "settings_menu"
BACK_CALLBACK_DATA = "settings_back"
TOGGLE_CALLBACK_PREFIX = "toggle:"

MENU_TEXT = (
    "Проверка идёт автоматически каждые 5 минут, но можно проверить и вручную, "
    "а также включить/отключить уведомления по каждой площадке отдельно:"
)


def _main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=CHECK_BUTTON_TEXT, callback_data=CHECK_CALLBACK_DATA)],
            [InlineKeyboardButton(text=SETTINGS_BUTTON_TEXT, callback_data=SETTINGS_CALLBACK_DATA)],
        ]
    )


def _settings_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for checker in CHECKERS:
        mark = "✅" if settings.is_enabled(checker.name) else "🚫"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {checker.display_name}",
                    callback_data=f"{TOGGLE_CALLBACK_PREFIX}{checker.name}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=BACK_CALLBACK_DATA)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        f"Привет! Я слежу за наличием серверов на нескольких площадках "
        f"и пришлю уведомление, как только что-то появится в продаже.\n\n{MENU_TEXT}",
        reply_markup=_main_keyboard(),
    )


@router.callback_query(F.data == CHECK_CALLBACK_DATA)
async def on_check_now(callback: CallbackQuery) -> None:
    await callback.answer("Проверяю...")
    result = await monitor.run_check(callback.bot, manual=True)
    await callback.message.answer(
        result or "Нечего проверять — нет ни одного подключённого чекера.",
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=_main_keyboard(),
    )


@router.callback_query(F.data == SETTINGS_CALLBACK_DATA)
async def on_settings_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "Уведомления по площадкам (нажми, чтобы включить/отключить):",
        reply_markup=_settings_keyboard(),
    )


@router.callback_query(F.data == BACK_CALLBACK_DATA)
async def on_settings_back(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(MENU_TEXT, reply_markup=_main_keyboard())


@router.callback_query(F.data.startswith(TOGGLE_CALLBACK_PREFIX))
async def on_toggle(callback: CallbackQuery) -> None:
    checker_name = callback.data.removeprefix(TOGGLE_CALLBACK_PREFIX)
    new_value = not settings.is_enabled(checker_name)
    settings.set_enabled(checker_name, new_value)
    await callback.answer("Уведомления включены" if new_value else "Уведомления отключены")
    await callback.message.edit_reply_markup(reply_markup=_settings_keyboard())
