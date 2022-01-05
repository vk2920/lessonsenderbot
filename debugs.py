import logging
import datetime

from aiogram.types import Message


def debug_log(message: Message, debug_message: str = "Дополнительное сообщение не указано"):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text
    username = message.from_user.first_name
    logging.info(f"{username} ({user_id}) написал: {text} в чат {chat_id}")
    logging.info(debug_message)


class Logger:
    def __init__(self, file_name: str = f"lessonsenderbot-{datetime.date.today().isoformat()}.log"):
        self._log_file = open(file_name, 'a')
        self._log_file.write("\n\n" + ("-"*80) + f"\nLog started at "
                             f"{datetime.datetime.now().replace(microsecond=0).isoformat().replace('T', ' ')}\n\n")

    def __del__(self):
        self._log_file.close()

    def log(self, message: Message, _ex, debug_message: str = "Дополнительное сообщение не указано"):
        self._log_file.write(f"{message.from_user.first_name} ({message.from_user.id}) написал \""
                             f"{message.text}\" в чат {message.chat.id}\n{debug_message}\n{_ex}\n\n")
