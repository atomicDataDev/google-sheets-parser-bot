"""
Configuration module.

Loads all settings from environment variables (via .env file) and exposes
them as module-level constants for use across the project.
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
GROUP_CHAT_ID: str = os.getenv("GROUP_CHAT_ID", "")
MESSAGE_THREAD_ID: str | None = os.getenv("MESSAGE_THREAD_ID")
SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "")

STATE_FILE_PATH: str = "state.json"
TEMP_FILE_PATH: str = "temp_sheet.xlsx"

GOOGLE_CREDS_DICT: dict = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))

_target_sheets_raw: str = os.getenv("TARGET_SHEETS", "")
TARGET_SHEETS: list[str] = (
    [s.strip() for s in _target_sheets_raw.split(",")]
    if _target_sheets_raw
    else []
)
