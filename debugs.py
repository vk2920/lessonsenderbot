import logging

from aiogram.types import Message


def debug_log(message: Message, debug_message: str = "Дополнительное сообщение не указано"):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text
    username = message.from_user.first_name
    logging.info(f"{username} ({user_id}) написал: {text} в чат {chat_id}")
    logging.info(debug_message)