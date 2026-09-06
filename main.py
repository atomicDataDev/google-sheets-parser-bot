"""
Bot entry point.

Instantiates all components, registers Telegram command handlers, starts the
background scheduling thread, and runs the polling loop with automatic
reconnect on network errors.
"""
import threading
import time

import schedule
import telebot

from checker import CheckerLogic
from config import BOT_TOKEN, STATE_FILE_PATH
from google_client import GoogleSheetsClient
from state_manager import StateManager

bot = telebot.TeleBot(BOT_TOKEN)
google_client = GoogleSheetsClient()
state_manager = StateManager(STATE_FILE_PATH)
checker = CheckerLogic(bot, google_client, state_manager)


@bot.message_handler(commands=["check"])
def handle_check(message: telebot.types.Message) -> None:
    """
    Handle the ``/check`` command.

    Triggers a manual update check and replies in the originating chat/thread.

    :param message: Incoming Telegram message object.
    :type message: telebot.types.Message
    """
    checker.check_updates(
        manual=True,
        chat_id=message.chat.id,
        thread_id=message.message_thread_id,
    )


@bot.message_handler(commands=["ping"])
def handle_ping(message: telebot.types.Message) -> None:
    """
    Handle the ``/ping`` command.

    Replies with the current bot status and the last known spreadsheet
    modification timestamp.

    :param message: Incoming Telegram message object.
    :type message: telebot.types.Message
    """
    state = state_manager.get_state()
    msg = (
        "Состояние: в сети\n"
        "Последнее обновление таблицы:\n"
        f"<code>{state.get('modifiedTime', 'N/A')}</code>"
    )
    bot.send_message(
        message.chat.id,
        msg,
        message_thread_id=message.message_thread_id,
        parse_mode="HTML",
    )


def run_scheduler() -> None:
    """
    Run the background scheduling loop.

    Schedules a daily automatic check at 10:00 and executes pending jobs every
    10 seconds. Intended to run in a daemon thread.
    """
    schedule.every().day.at("18:00").do(checker.check_updates)
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    print("Bot started.")
    threading.Thread(target=run_scheduler, daemon=True).start()

    while True:
        try:
            bot.infinity_polling(timeout=20, skip_pending=True)
        except Exception as e:
            print(f"Network / Telegram API error: {e}")
            time.sleep(5)
