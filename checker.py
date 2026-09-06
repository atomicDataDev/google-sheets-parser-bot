"""
Change-checking orchestration module.

Coordinates the full update cycle: querying the Google Drive modification
timestamp, comparing it with the persisted state, downloading the PDF on
change, and notifying the Telegram chat.
"""
import os

import telebot

from config import GROUP_CHAT_ID, MESSAGE_THREAD_ID, SPREADSHEET_ID
from google_client import GoogleSheetsClient
from state_manager import StateManager


class CheckerLogic:
    """
    Orchestrates spreadsheet change detection and Telegram notifications.

    Designed for use via dependency injection so that the bot instance,
    Google client, and state manager can be swapped or mocked independently.

    :param bot: Configured ``telebot.TeleBot`` instance.
    :type bot: telebot.TeleBot
    :param google_client: Client for Google Drive API access.
    :type google_client: GoogleSheetsClient
    :param state_manager: Handler for persistent bot state.
    :type state_manager: StateManager
    """

    def __init__(
        self,
        bot: telebot.TeleBot,
        google_client: GoogleSheetsClient,
        state_manager: StateManager,
    ) -> None:
        self.bot = bot
        self.google = google_client
        self.state = state_manager

    def check_updates(
        self,
        manual: bool = False,
        chat_id: int | str | None = None,
        thread_id: int | str | None = None,
    ) -> None:
        """
        Run a single update check cycle.

        Fetches the current ``modifiedTime`` from Google Drive and compares it
        with the stored value. On a mismatch, downloads the spreadsheet as PDF
        and sends it to the target Telegram chat. If ``manual`` is ``True``,
        sends status messages for both the update and the no-change cases.

        The temporary PDF file is always removed in the ``finally`` block,
        regardless of success or failure.

        :param manual: ``True`` when triggered by a user command (``/check``);
            enables verbose status replies.
        :type manual: bool
        :param chat_id: Destination chat ID. Falls back to ``GROUP_CHAT_ID``
            from config when ``None``.
        :type chat_id: int | str | None
        :param thread_id: Destination forum topic ID. Falls back to
            ``MESSAGE_THREAD_ID`` from config when ``None``.
        :type thread_id: int | str | None
        """
        target_chat: int | str = chat_id if chat_id is not None else GROUP_CHAT_ID
        raw_thread = thread_id if thread_id is not None else MESSAGE_THREAD_ID

        target_thread: int | None = None
        if isinstance(raw_thread, int):
            target_thread = raw_thread
        elif isinstance(raw_thread, str) and raw_thread.strip().isdigit():
            target_thread = int(raw_thread.strip())

        pdf_path = "temp_sheet.pdf"

        try:
            if manual:
                self.bot.send_message(
                    target_chat, "Начал проверку...", message_thread_id=target_thread
                )

            new_time = self.google.get_modified_time(SPREADSHEET_ID)
            current_state = self.state.get_state()

            if new_time != current_state.get("modifiedTime") and new_time != "unknown":
                pdf_path = self.google.download_pdf(SPREADSHEET_ID)

                with open(pdf_path, "rb") as doc:
                    caption = (
                        "<b>Обновление таблицы!</b>\n"
                        "Время изменения:\n"
                        f"<code>{new_time}</code>"
                    )
                    self.bot.send_document(
                        target_chat,
                        doc,
                        message_thread_id=target_thread,
                        caption=caption,
                        parse_mode="HTML",
                        visible_file_name="Spreadsheet.pdf",
                    )

                self.state.update_state(new_time)
            elif manual:
                msg = (
                    "Таблица находится в актуальном состоянии.\n"
                    "Последнее обновление:\n"
                    f"<code>{current_state.get('modifiedTime')}</code>"
                )
                self.bot.send_message(
                    target_chat, msg, message_thread_id=target_thread, parse_mode="HTML"
                )

        except Exception as e:
            error_msg = (
                f"Ошибка при проверке (chat_id={target_chat}, "
                f"thread_id={target_thread}): {e}"
            )
            print(error_msg)
            if manual:
                self.bot.send_message(
                    target_chat, error_msg, message_thread_id=target_thread
                )
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
