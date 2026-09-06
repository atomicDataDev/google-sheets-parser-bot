"""
Configuration module.

Loads all settings from environment variables (via .env file) and exposes
them as module-level constants for use across the project.
"""
import json
import os

from dotenv import load_dotenv

# Use override=True so values from .env always take precedence over cached shell vars
load_dotenv(override=True)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip().strip("'\"")

_group_chat_raw: str = (
    os.getenv("GROUP_CHAT_ID", "").split("#")[0].strip().strip("'\"")
)
GROUP_CHAT_ID: int | str = (
    int(_group_chat_raw)
    if _group_chat_raw.lstrip("-").isdigit()
    else _group_chat_raw
)

_thread_id_raw: str = (
    os.getenv("MESSAGE_THREAD_ID", "").split("#")[0].strip().strip("'\"")
)
MESSAGE_THREAD_ID: int | None = (
    int(_thread_id_raw) if _thread_id_raw.isdigit() else None
)

SPREADSHEET_ID: str = (
    os.getenv("SPREADSHEET_ID", "").strip().strip("'\"")
)

STATE_FILE_PATH: str = "state.json"
TEMP_FILE_PATH: str = "temp_sheet.xlsx"

GOOGLE_CREDS_DICT: dict = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))

_target_sheets_raw: str = os.getenv("TARGET_SHEETS", "")
TARGET_SHEETS: list[str] = (
    [s.strip() for s in _target_sheets_raw.split(",")]
    if _target_sheets_raw
    else []
)
