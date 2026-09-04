import threading
import time
import schedule
import telebot

from config import BOT_TOKEN, STATE_FILE_PATH
from google_client import GoogleSheetsClient
from state_manager import StateManager
from checker import CheckerLogic

bot = telebot.TeleBot(BOT_TOKEN)
google_client = GoogleSheetsClient()
state_manager = StateManager(STATE_FILE_PATH)
checker = CheckerLogic(bot, google_client, state_manager)

@bot.message_handler(commands=['check'])
def handle_check(message):
    checker.check_updates(manual=True, chat_id=message.chat.id, thread_id=message.message_thread_id)

@bot.message_handler(commands=['ping'])
def handle_ping(message):
    state = state_manager.get_state()
    msg = (
        "Состояние: в сети\n"
        f"последнее обновление таблицы: {state.get('lastModifiedDate')}\n"
        "актуальный хэш:\n"
        f"<code>{state.get('actualHash')}</code>"
    )
    bot.send_message(message.chat.id, msg, message_thread_id=message.message_thread_id, parse_mode="HTML")


def run_scheduler():
    schedule.every().day.at("10:00").do(checker.check_updates)
    while True:
        schedule.run_pending()
        time.sleep(10) 

if __name__ == '__main__':
    print("Бот запущен...")
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    while True:
        try:
            bot.infinity_polling(timeout=20, skip_pending=True)
        except Exception as e:
            print(f"Ошибка сети/Telegram API: {e}")
            time.sleep(5)