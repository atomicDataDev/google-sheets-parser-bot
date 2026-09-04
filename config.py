import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
MESSAGE_THREAD_ID = os.getenv("MESSAGE_THREAD_ID")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
STATE_FILE_PATH = "state.json"
TEMP_FILE_PATH = "temp_sheet.xlsx"

GOOGLE_CREDS_DICT = json.loads(os.getenv("GOOGLE_CREDENTIALS", "{}"))

_target_sheets_raw = os.getenv("TARGET_SHEETS", "")
TARGET_SHEETS = [s.strip() for s in _target_sheets_raw.split(",")] if _target_sheets_raw else []