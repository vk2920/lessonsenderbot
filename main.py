import logging
import os
import datetime
import random
import asyncio

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import exceptions
from aiogram.utils.markdown import bold, italic, code, link
import emoji

import config
import database
from debugs import debug_log


class StartSetting(StatesGroup):  # Группа состояний для первичной настройки
    select_institute = State()  # Состояние для выбора института
    # select_direction = State()  # Состояние для выбора направления
    select_course = State()  # Состояние для выбора курса
    select_group = State()  # Состояние для выбора группы


class UserStates(StatesGroup):
    day_of_week = State()


class AdminStates(StatesGroup):
    main = State()


API_TOKEN = os.environ['BOT_TOKEN']
ADMINS = [470985286, 1943247578]

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

db = database.DataBase()

std_keyboard = ReplyKeyboardMarkup()
std_keyboard.row(KeyboardButton("Конкретный день"), KeyboardButton("Пары"))
std_keyboard.row(KeyboardButton("Сегодня"), KeyboardButton("Завтра"))
std_keyboard.row(KeyboardButton("Чёт"), KeyboardButton("Всё"), KeyboardButton("Нечёт"))
std_keyboard.row(KeyboardButton("Сменить группу"), KeyboardButton("Цитата"))

admin_keyboard = ReplyKeyboardMarkup()
admin_keyboard.row(KeyboardButton("Конкретный день"), KeyboardButton("Пары"))
admin_keyboard.row(KeyboardButton("Сегодня"), KeyboardButton("Завтра"))
admin_keyboard.row(KeyboardButton("Чёт"), KeyboardButton("Всё"), KeyboardButton("Нечёт"))
admin_keyboard.row(KeyboardButton("Сменить группу"), KeyboardButton("Админ"), KeyboardButton("Цитата"))

day_keyboard = ReplyKeyboardMarkup()
day_keyboard.row(KeyboardButton("ПН Нечёт"), KeyboardButton("ВТ Нечёт"), KeyboardButton("СР Нечёт"))
day_keyboard.row(KeyboardButton("ЧТ Нечёт"), KeyboardButton("ПТ Нечёт"), KeyboardButton("СБ Нечёт"))
day_keyboard.row(KeyboardButton("ПН Чёт"), KeyboardButton("ВТ Чёт"), KeyboardButton("СР Чёт"))
day_keyboard.row(KeyboardButton("ЧТ Чёт"), KeyboardButton("ПТ Чёт"), KeyboardButton("СБ Чёт"))

days_of_week = ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


async def auto_phrase_sender():
    while True:
        chat_id = db.r_get_random_chat_id()
        try:
            print(f"Получен ID чата: {chat_id}")
            if chat_id != 0:
                await bot.send_message(chat_id, get_random_phrase_to_msg(), parse_mode=types.ParseMode.MARKDOWN)
        except Exception as _ex:
            print("Ошибка отправки запланированного сообщения", _ex)
        await asyncio.sleep(3597)


def get_random_phrase_to_msg():
    phrase = db.r_get_random_phrase()
    return f"*«{phrase[0]}»*\n© {phrase[1]}"


def print_pairs(pairs: list, day_of_week: int, even_week: bool, with_id=False):
    if len(pairs) == 0:
        return bold(days_of_week[day_of_week] +
                    (" чётной недели" if even_week else " нечётной недели") + ". На заводе не работаем") + "\n"
    msg = bold("Вот твоё расписание на выбранный день (" + days_of_week[day_of_week] +
               (" чётной недели" if even_week else " нечётной недели") + "):") + "\n"
    for pair in pairs:
        pair = list(pair)
        if pair[6] == "":
            pair[6] = "Преподаватель не определён"

        if pair[4] == 1:
            pair[4] = "8:30 ~ 10:00\n1. "
        elif pair[4] == 2:
            pair[4] = "10:10 ~ 11:40\n2. "
        elif pair[4] == 3:
            pair[4] = "11:50 ~ 13:20\n3. "
        elif pair[4] == 4:
            pair[4] = "14:00 ~ 15:30\n4. "
        elif pair[4] == 5:
            pair[4] = "15:40 ~ 17:10\n5. "
        elif pair[4] == 6:
            pair[4] = "17:20 ~ 18:50\n6. "
        elif pair[4] == 7:
            pair[4] = "19:00 ~ 20:30\n7. "

        msg += str(pair[4]) + str(pair[5]) + (bold(" ID:" + str(pair[0])) if with_id else "") + "\n    " +\
            italic(str(pair[6])) + "\n    " + code(str(pair[7]) +
                                                   ("" if pair[8] == "" else (" в ауд. " + pair[8]))) + "\n\n"
    return msg


def get_pairs(message: types.Message):
    msg = get_today_by_id(message.from_user.id)
    msg += get_next_day_by_id(message.from_user.id)
    return msg


def get_today(group: str):
    even_week = int(datetime.date.today().strftime("%V")) % 2 == 0
    today = datetime.datetime.today().weekday() + 1
    msg = ""
    if today != 6:  # Если сегодня не воскресенье
        pairs = db.r_get_pairs_by_group(day_of_week=today, even_week=even_week, group=group)
        msg += print_pairs(pairs, today, even_week)
    return msg


def get_today_by_id(user_id: int):
    even_week = int(datetime.date.today().strftime("%V")) % 2 == 0
    today = datetime.datetime.today().weekday()
    msg = ""
    if today != 6:  # Если сегодня не воскресенье
        group = db.r_get_user_group(tg_id=user_id)
        pairs = db.r_get_pairs_by_group(day_of_week=today + 1, even_week=even_week, group=group)
        msg += print_pairs(pairs, today + 1, even_week, with_id=(user_id in ADMINS))
    return msg


def get_next_day(group: str):
    even_week = int(datetime.date.today().strftime("%V")) % 2 == 0
    tomorrow = datetime.datetime.today().weekday() + 1
    msg = ""

    if tomorrow == 6:  # Если завтра воскресенье, то перейдём на понедельник
        tomorrow = 0
        even_week = not even_week

    if tomorrow != 6:  # Если завтра не воскресенье
        pairs = db.r_get_pairs_by_group(day_of_week=tomorrow + 1, even_week=even_week, group=group)
        msg += print_pairs(pairs, tomorrow + 1, even_week)
    return msg


def get_next_day_by_id(user_id: int):
    even_week = int(datetime.date.today().strftime("%V")) % 2 == 0
    today = datetime.datetime.today().weekday()
    if today == 6:
        tomorrow = 0
        even_week = not even_week
    else:
        tomorrow = today + 1

    msg = ""

    if tomorrow == 6:  # Если завтра воскресенье, то перейдём на понедельник
        tomorrow = 0
        even_week = not even_week

    if tomorrow != 6:  # Если завтра не воскресенье
        group = db.r_get_user_group(tg_id=user_id)
        pairs = db.r_get_pairs_by_group(day_of_week=tomorrow + 1, even_week=even_week, group=group)
        msg += print_pairs(pairs, tomorrow + 1, even_week, with_id=(user_id in ADMINS))
    return msg


def get_week(group, even_week, with_id=False):
    msg = ""
    for i in range(1, 7):
        msg += bold(days_of_week[i]) + "\n"
        pairs = db.r_get_pairs_by_group(day_of_week=i, even_week=even_week, group=group)
        msg += print_pairs(pairs=pairs, day_of_week=i, even_week=even_week, with_id=with_id)
        msg += "\n"
    return msg


@dp.message_handler(commands='start')  # Реакция на активацию бота, переход на выбор института
async def start_bot(message: types.Message):
    debug_log(message, debug_message="Первое сообщение (или команда перенастройки)")
    markup = ReplyKeyboardMarkup()
    for i in range(0, len(config.institutes), 2):
        try:
            markup.row(KeyboardButton(config.institutes[i]), KeyboardButton(config.institutes[i + 1]))
        except IndexError as _ex:
            markup.add(KeyboardButton(config.institutes[i]))

    markup.add(KeyboardButton("Выход"))

    await message.answer(f"Привет, {message.from_user.first_name})\nМеня зовут Базилик.\nСейчас я хочу, чтобы ты "
                         f"рассказал мне немного о своей студенческой жизни, чтобы я знал, какое расписание для тебя "
                         f"будет актуально.\nДля начала выбери свой институт.\n(Не бойся выбирать ИИТУТС, я никому об "
                         f"этом не расскажу " + emoji.emojize(":wink:", use_aliases=True) + f")", reply_markup=markup)
    # await message.answer(f"Не хочется этого рассказывать, но я немножко глуп...\nПроблема заключается в том, что я не"
    #                      f" могу узнать актуальное расписание с сайта СевГУ.\n\nЕсли ты хочешь попробовать свои силы,"
    #                      f" то советую почитать " +
    #                      link("объявление", "https://github.com/vk2920/lessonsenderbot/blob/main/README.md"),
    #                      reply_markup=markup)
    await StartSetting.select_institute.set()


@dp.message_handler(state=StartSetting.select_institute)  # Выбор института, переход на выбор курса
async def start_setting_select_institute(message: types.Message, state: FSMContext):
    debug_log(message, debug_message="Выбор института, переход к выбору курса")
    if message.text not in config.institutes:
        await message.reply("Увы, но у нас нет такого института\nНажми на кнопку с названием твоего института")
    else:
        institute_index = config.institutes.index(message.text)
        async with state.proxy() as data:
            data['institute_index'] = institute_index

        markup = ReplyKeyboardMarkup()
        markup.row(KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3"))
        markup.row(KeyboardButton("4"), KeyboardButton("5"), KeyboardButton("6"))

        markup.add(KeyboardButton("Выход"))

        await message.reply("Я запомнил твой институт\nТеперь выбери курс",
                            reply_markup=markup)
        await StartSetting.next()


@dp.message_handler(state=StartSetting.select_course)  # Выбор курса, переход к выбору группы
async def start_setting_select_institute(message: types.Message, state: FSMContext):
    debug_log(message, debug_message="Выбор курса, переход к выбору группы")
    if message.text.lower() == "выход":
        await state.finish()
        await message.answer("Был совершён выход из режима настройки\n\n"
                             "Если группа уже была настроена, то ничего не изменилось\n"
                             "Если группа не была настроена, то она остаётся не настроенной.\n"
                             "Не волнуйся, если твоей группы нет, то и расписания для неё пока нет.")
        return 0
    if not message.text.isnumeric():
        await message.reply("Упс... Кажется что-то пошло не так\nПерепроверь введённый номер курса, "
                            "это должно быть просто число.")
        return 0

    course = int(message.text)
    async with state.proxy() as data:
        institute_index = data['institute_index']
        data['course'] = course

    try:
        group_list = config.groups[institute_index][course - 1]
    except IndexError as _ex:
        await message.answer("Увы, но этот институт пока недоступен\nЖдите обновлений")
        return 0

    markup = ReplyKeyboardMarkup()
    for i in range(0, len(group_list), 2):
        group1 = group_list[i].split("/")
        group1 = group1[0].upper() + "/" + group1[1]
        group2 = group_list[i + 1].split("/")
        group2 = group2[0].upper() + "/" + group2[1]
        markup.row(KeyboardButton(group1), KeyboardButton(group2))

    markup.add(KeyboardButton("Выход"))

    await message.reply("Я запомнил твой курс\nТеперь выбери группу)",
                        reply_markup=markup)
    await StartSetting.next()


@dp.message_handler(state=StartSetting.select_group)  # Выбор группы, завершение настройки
async def start_setting_select_group(message: types.Message, state: FSMContext):
    debug_log(message, debug_message="Выбор группы, завершение настройки")
    if message.text.lower() == "выход":
        await state.finish()
        await message.answer("Был совершён выход из режима настройки\n\n"
                             "Если группа уже была настроена, то ничего не изменилось\n"
                             "Если группа не была настроена, то она остаётся не настроенной.\n"
                             "Не волнуйся, если твоей группы нет, то и расписания для неё пока нет.")
        return 0
    async with state.proxy() as data:
        group_list = config.groups[data['institute_index']][data['course'] - 1]
    if message.text.lower() in group_list:
        await message.answer("Я получил твою группу, сейчас сохраню и настройка будет завершена",
                             reply_markup=ReplyKeyboardRemove())
        db.w_register_user_by_id(message.from_user.id, message.from_user.first_name, message.text.lower())
        await message.answer("Группа сохранена)\nПриятного пользования", reply_markup=std_keyboard)
        await state.finish()
    else:
        await message.reply("Последний этап остался...\nВыбери свою группу на клавиатуре")


@dp.message_handler(state=UserStates.day_of_week)  # Реакция бота на выбор конкретного учебного дня
async def day_of_week_msg(message: types.Message, state: FSMContext):
    debug_log(message, "Вызов функции после выбора дня недели, отправка расписания на конкретный день")
    if message.text.lower().split(" ")[0] not in ["пн", "вт", "ср", "чт", "пт", "сб"]:
        await message.reply("Тут что-то не то\nДавай ты не будешь меня задерживать тут и нормально выберешь нужный "
                            "день недели)", reply_markup=day_keyboard)
        return 0
    if message.text.lower().split(" ")[1] not in ["чёт", "нечёт"]:
        await message.reply("Тут что-то не то\nДавай ты не будешь меня задерживать тут и нормально выберешь нужный "
                            "день недели)", reply_markup=day_keyboard)
        return 0

    group = db.r_get_user_group(message.from_user.id)
    day_of_week = ["", "пн", "вт", "ср", "чт", "пт", "сб"].index(message.text.lower().split(" ")[0])
    even_week = message.text.lower().split(" ")[1] == "чёт"
    pairs = db.r_get_pairs_by_group(day_of_week, even_week, group)
    await message.answer(print_pairs(pairs, day_of_week, even_week,
                                     with_id=(message.from_user.id in ADMINS)).replace("\\", ""),
                         reply_markup=std_keyboard, parse_mode=types.ParseMode.MARKDOWN)
    await state.finish()


@dp.message_handler(state=AdminStates.main)
async def admin_actions(message: types.Message, state: FSMContext):
    cmd = message.text.lower().split(" ")[0]
    if cmd == "выход":
        await state.finish()
        await message.answer("Покидаем панель управления...",
                             reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard))
    elif cmd == "удалить":
        if len(message.text.lower().split(" ")) != 2 or not message.text.lower().split(" ")[1].isnumeric():
            await message.answer("*Удалить _<ID пары для удаления>_*", parse_mode=types.ParseMode.MARKDOWN,
                                 reply_markup=ReplyKeyboardRemove())
            return 0

        pair = db.r_get_pair_by_pair_id(int(message.text.split(" ")[1]))
        if pair:
            db.w_remove_pair_by_pair_id(int(message.text.split(" ")[1]))
            await message.answer(f"Пара по дисциплине *{pair[5]}* _({pair[1]}, {pairs[3]}, {pair[4]})_ удалена",
                                 parse_mode=types.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
            return 0

        await message.answer(f"Ууупс... А в БД нет нужной пары", parse_mode=types.ParseMode.MARKDOWN,
                             reply_markup=ReplyKeyboardRemove())
        return 0
    elif cmd == "перенести":
        if len(message.text.lower().split(" ")) != 4 or not message.text.lower().split(" ")[1].isnumeric()\
                or not message.text.lower().split(" ")[2].isnumeric()\
                or not message.text.lower().split(" ")[3].isnumeric():
            await message.answer("*Перенести _<ID пары для переноса> <день недели> <номер пары>_*\n"
                                 "День недели — число, от 1 до 6 (от ПН до СБ)\n"
                                 "Номер пары — порядковыё номер пары в течение дня (определяет время пары)",
                                 parse_mode=types.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
            return 0

        pair = db.r_get_pair_by_pair_id(int(message.text.split(" ")[1]))
        if pair:
            db.w_move_pair_by_pair_id(int(message.text.split(" ")[1]), int(message.text.split(" ")[2]),
                                      int(message.text.split(" ")[3]))
            await message.answer(f"Пара по дисциплине *{pair[5]}* _({pair[1]}, {pair[3]}, {pair[4]})_ перенесена\n"
                                 f"И стала парой *{pair[5]}* _({pair[1]}, {message.text.split(' ')[2]}, "
                                 f"{message.text.split(' ')[3]})_", parse_mode=types.ParseMode.MARKDOWN,
                                 reply_markup=ReplyKeyboardRemove())
            return 0

        await message.answer(f"Ууупс... А в БД нет нужной пары", parse_mode=types.ParseMode.MARKDOWN,
                             reply_markup=ReplyKeyboardRemove())
        return 0
    elif cmd == "сменить_аудиторию":
        if len(message.text.lower().split(" ")) != 3 or not message.text.lower().split(" ")[1].isnumeric():
            await message.answer("*Сменить_аудиторию _<ID пары> <Аудитория>_*\n"
                                 "Аудитория — аудитория, в которой будет проводиться пара",
                                 parse_mode=types.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
            return 0

        pair = db.r_get_pair_by_pair_id(int(message.text.split(" ")[1]))
        if pair:
            db.w_change_pair_location_by_pair_id(int(message.text.split(" ")[1]), int(message.text.split(" ")[2]),
                                                 int(message.text.split(" ")[3]))
            await message.answer(f"Пара по дисциплине *{pair[5]}* _({pair[1]}, {pairs[3]}, {pair[4]})_ перенесена"
                                 f"в аудиторию {message.text.upper().split(' ')[2]}",
                                 parse_mode=types.ParseMode.MARKDOWN, reply_markup=ReplyKeyboardRemove())
            return 0

        await message.answer(f"Ууупс... А в БД нет нужной пары", parse_mode=types.ParseMode.MARKDOWN,
                             reply_markup=ReplyKeyboardRemove())
        return 0
    else:
        await message.answer("Что-то пошло не по плану, у меня нет команды *" + message.text.split(" ")[0] + "*")
        await message.answer("Возможно, ты просто забыл выйти из панели управления")
        return 0


@dp.message_handler()  # Реакция бота на сообщение для выполнения определённой команды
async def command_execute(message: types.Message):
    debug_log(message, "Вызов функции выполнения команды для зарегистрированного пользователя")
    db.w_set_chat_id(user_id=message.from_user.id, chat_id=message.chat.id)
    try:
        cmd = message.text.lower()
        if cmd == "сегодня":
            await message.answer(get_today_by_id(message.from_user.id).replace("\\", ""),
                                 reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard),
                                 parse_mode=types.ParseMode.MARKDOWN)
        elif cmd == "завтра":
            await message.answer(get_next_day_by_id(message.from_user.id).replace("\\", ""),
                                 reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard),
                                 parse_mode=types.ParseMode.MARKDOWN)
        elif cmd == "нечёт":
            group = db.r_get_user_group(message.from_user.id)
            await message.answer(get_week(group, False, with_id=(message.from_user.id in ADMINS)).replace("\\", ""),
                                 reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard),
                                 parse_mode=types.ParseMode.MARKDOWN)
        elif cmd == "чёт":
            group = db.r_get_user_group(message.from_user.id)
            await message.answer(get_week(group, True, with_id=(message.from_user.id in ADMINS)).replace("\\", ""),
                                 reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard),
                                 parse_mode=types.ParseMode.MARKDOWN)
        elif cmd == "всё":
            group = db.r_get_user_group(message.from_user.id)
            await message.answer(get_week(group, False, with_id=(message.from_user.id in ADMINS)).replace("\\", "")
                                 + "\n\n" + get_week(group, True,
                                                     with_id=(message.from_user.id in ADMINS)).replace("\\", ""),
                                 reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard),
                                 parse_mode=types.ParseMode.MARKDOWN)
        elif cmd == "пары":
            await message.answer(get_today_by_id(message.from_user.id).replace("\\", "") + "\n\n" +
                                 get_next_day_by_id(message.from_user.id).replace("\\", ""),
                                 reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard),
                                 parse_mode=types.ParseMode.MARKDOWN)
        elif cmd == "конкретный день":
            await message.answer("И снова привет)\nЯ внезапно прилетел из параллельной вселенной, чтобы выполнить "
                                 "свой долг\nЕсли я не ошибаюсь, тебе нужно расписание на конкретный день\n"
                                 "Что ж...  Выбирай день на виртуальной клавиатуре и получишь своё расписание)",
                                 reply_markup=day_keyboard)
            await UserStates.day_of_week.set()
        elif cmd == "сменить группу":
            markup = ReplyKeyboardMarkup()
            for i in range(0, len(config.institutes), 2):
                markup.row(KeyboardButton(config.institutes[i]), KeyboardButton(config.institutes[i + 1]))

            await message.answer(f"Ты что-то хотел? А, точно, группу сменить. Помнишь, как выбирал свою группу в "
                                 f"начале?\nДавай повторим этот процесс)", reply_markup=markup)
            await StartSetting.select_institute.set()
        elif cmd == "админ":
            if message.from_user.id not in ADMINS:
                await message.answer("Мы с тобой очень хорошо знакомы...\n"
                                     "Но я пока не могу предоставить тебе такой доступ")
                return 0
            await AdminStates.main.set()
            await message.answer("Панель управления базой данных, будь аккуратнее, мы уже давно на проде",
                                 reply_markup=ReplyKeyboardRemove())
        elif cmd == "цитата":
            await message.answer(get_random_phrase_to_msg(),
                                 reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard),
                                 parse_mode=types.ParseMode.MARKDOWN)
        else:
            await message.reply("Ну и чё ты написал?\nЧто я должен сделать?\n"
                                "Ладно, я притворюсь, что этого не было")

    except exceptions.MessageIsTooLong as _ex:
        logging.warning(_ex)
        await message.answer("Я бы и рад скинуть тебе твоё расписание... \n"
                             "Но оно слишком большое, и ТГ не позволяет сделать этого (\n"
                             "Попробуй не пытаться узнать расписание на 2 недели\n"
                             "Возможно, такой ход помощет нам обрести связь)",
                             reply_markup=(admin_keyboard if message.from_user.id in ADMINS else std_keyboard))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(auto_phrase_sender())

    executor.start_polling(dp, skip_updates=True)
