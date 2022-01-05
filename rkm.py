from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура для выбора курса
rkm_select_course = ReplyKeyboardMarkup()\
    .row(KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3"))\
    .row(KeyboardButton("4"), KeyboardButton("5"), KeyboardButton("6"))

# Стандартная клавиатура (основное состояние обычного юзера)
rkm_std = ReplyKeyboardMarkup()\
    .row(KeyboardButton("Сегодня"), KeyboardButton("Завтра"))\
    .row(KeyboardButton("Конкретный день"), KeyboardButton("На неделю"))\
    .row(KeyboardButton("Цитата"))\
    .row(KeyboardButton("Сменить группу"), KeyboardButton("Настройки"))

# Клавиатура для выбора дня недели
rkm_select_day = ReplyKeyboardMarkup()\
    .row(KeyboardButton("ПН Нечёт"), KeyboardButton("ВТ Нечёт"), KeyboardButton("СР Нечёт"))\
    .row(KeyboardButton("ЧТ Нечёт"), KeyboardButton("ПТ Нечёт"), KeyboardButton("СБ Нечёт"))\
    .row(KeyboardButton("ПН Чёт"), KeyboardButton("ВТ Чёт"), KeyboardButton("СР Чёт"))\
    .row(KeyboardButton("ЧТ Чёт"), KeyboardButton("ПТ Чёт"), KeyboardButton("СБ Чёт"))\
    .row(KeyboardButton("Отмена"))

# Клавиатура для выбора недели
rkm_select_week = ReplyKeyboardMarkup()\
    .row(KeyboardButton("Нечётная"), KeyboardButton("Чётная"))\
    .row(KeyboardButton("Отмена"))

# Клавиатура настроек
rkm_settings = ReplyKeyboardMarkup()\
    .row(KeyboardButton("Включить цитаты"), KeyboardButton("Выключить цитаты"))\
    .row(KeyboardButton("Включить расписание"), KeyboardButton("Выключить расписание"))\
    .row(KeyboardButton("Включить зачёты"), KeyboardButton("Выключить зачёты"))\
    .row(KeyboardButton("Включить отладку"), KeyboardButton("Выключить отладку"))\
    .row(KeyboardButton("Выйти"))
