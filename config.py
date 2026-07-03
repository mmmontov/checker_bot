import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", 300))
STATE_FILE = os.environ.get("STATE_FILE", "data/state.json")
SETTINGS_FILE = os.environ.get("SETTINGS_FILE", "data/settings.json")
