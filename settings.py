import json
import os

from config import SETTINGS_FILE


def load_settings() -> dict[str, bool]:
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings: dict[str, bool]) -> None:
    os.makedirs(os.path.dirname(SETTINGS_FILE) or ".", exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def is_enabled(checker_name: str) -> bool:
    return load_settings().get(checker_name, True)


def set_enabled(checker_name: str, enabled: bool) -> None:
    settings = load_settings()
    settings[checker_name] = enabled
    save_settings(settings)
