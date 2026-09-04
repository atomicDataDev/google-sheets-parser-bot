import os
import telebot
from config import TARGET_SHEETS, SPREADSHEET_ID, GROUP_CHAT_ID, MESSAGE_THREAD_ID, TEMP_FILE_PATH
from google_client import GoogleSheetsClient
from excel_parser import ExcelParser
from state_manager import StateManager

class CheckerLogic:

    def __init__(self, bot: telebot.TeleBot, google_client: GoogleSheetsClient, state_manager: StateManager):
        self.bot = bot
        self.google = google_client
        self.state = state_manager

    def check_updates(self, manual: bool = False, chat_id=None, thread_id=None):
        target_chat = chat_id or GROUP_CHAT_ID
        target_thread = thread_id or MESSAGE_THREAD_ID

        try:
            if manual:
                self.bot.send_message(target_chat, "Начал проверку...", message_thread_id=target_thread)

            file_path = self.google.download_to_file(SPREADSHEET_ID)

            new_hash, _ = ExcelParser.get_sheet_hashes(file_path, TARGET_SHEETS)

            current_state = self.state.get_state()

            if new_hash != current_state.get("actualHash"):
                with open(file_path, 'rb') as doc:
                    caption = (
                        "<b>Обновление таблицы!</b>\n"
                        "MD5 Hash:\n"
                        f"<code>{new_hash}</code>"
                    )
                    self.bot.send_document(
                        target_chat, 
                        doc, 
                        message_thread_id=target_thread, 
                        caption=caption, 
                        parse_mode="HTML"
                    )
                
                self.state.update_state(new_hash)
            else:
                if manual:
                    msg = (
                        "Таблица находится в актуальном состоянии,\n"
                        f"последняя дата обновления: {current_state.get('lastModifiedDate')}\n"
                        "актуальный хэш:\n"
                        f"<code>{current_state.get('actualHash')}</code>"
                    )
                    self.bot.send_message(target_chat, msg, message_thread_id=target_thread, parse_mode="HTML")

        except Exception as e:
            err_msg = f"Ошибка при проверке таблицы: {e}"
            print(err_msg)
            if manual:
                self.bot.send_message(target_chat, err_msg, message_thread_id=target_thread)
        finally:
            
            if os.path.exists(TEMP_FILE_PATH):
                os.remove(TEMP_FILE_PATH)