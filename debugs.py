from aiogram.types import Message

def debug_log(message: Message, debug_message: str = "Дополнительное сообщение не указано"):
    user_id = message.from_user.id
    text = message.text
    username = message.from_user.first_name
    print(f"{username} ({user_id}) написал: {text}")
    print(debug_message)