import hashlib
import logging
import datetime
import asyncio
import os

from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import *
from database import db
from debugs import logger, debug_log
from rkm import *


# Состояния для первичной настройки
class StartSetting(StatesGroup):
    select_institute = State()
    select_course = State()
    select_group = State()


# Состояния для пользовательских действий
class UserStates(StatesGroup):
    select_week = State()
    select_day = State()
    settings = State()


# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и "слушателя" сообщений
bot = Bot(token=os.environ['BOT_TOKEN'])
dp = Dispatcher(bot, storage=MemoryStorage())

debug_save_error = logger.log


# Подготовить список пар для возврата пользователю в виде сообщения
def print_pairs(pairs: list, day_of_week: int, even_week: bool, with_id=False):
    """
    Функция для генерации читабельного списака пар
    :param pairs: Список пар, полученный из БД
    :param day_of_week: День недели (число от 1 до 6)
    :param even_week: Чётность недели (True, если чётная, False в противном случае)
    :param with_id: Сервисный аргумент. Включает указание ID записи в БД (для админов)
    :return: Список пар в читабельном виде
    """

    # Исправление для невозможности выйти за пределы массива в конфиге
    day_of_week = day_of_week % 7

    # Если нет пар, вернём сообщение об отсутствии пар
    if len(pairs) == 0:
        return f"*{DAYS_OF_WEEK_FULL_UPPER[day_of_week]} {('' if even_week else 'не')}чётной недели." \
               f" На заводе не работаем*\n"

    # В противном случае сделаем "шапку" для сообщения
    msg = f"*Вот твоё расписание на выбранный день ({DAYS_OF_WEEK_FULL[day_of_week]} "\
        f"{'' if even_week else 'не'}чётной недели):*\n"

    # И пробежимся по списку пар, чтобы каждую занести в сообщение
    for pair in pairs:
        # Преобразуем кортеж в список, чтобы исправить порядковые номера пар
        pair = list(pair)

        # Заглушка на случай, если преподаватель не указан в строке таблицы
        if pair[6] == "":
            pair[6] = "Преподаватель не определён"

        # Исправим порядковые номера пар (допишем время проведения)
        if pair[4] == 0:
            pair[4] = "Весь день\n0. "
        elif pair[4] == 1:
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

        # Конструкция адской сложности для дозаписи информации о паре в сообщение
        msg += f"{str(pair[4])}{str(pair[5])}{(f'* ID: {str(pair[0])}*' if with_id else '')}\n"\
            f"    _\r{str(pair[6])}_\r\n    `{pair[7]}{('' if pair[8] == '' else f' в ауд. {pair[8]}')}`\n\n"
    
    # Вернём готовое сообщение со всеми парами
    return msg


# Извлечение из БД списка пар на текущий день по ID пользователя
def get_pairs_today(user_id: int):
    """
    :param user_id: ID пользователя в ТГ
    :return: Список пар на текущий день для конкретного пользователя
    """
    even_week = int(datetime.date.today().strftime("%V")) % 2 == 0
    today = datetime.date.today().weekday() + 1
    msg = ""
    if today != 7:  # Если сегодня не воскресенье
        group = db.r_get_user_group(tg_id=user_id)
        if group:
            pairs = db.r_get_pairs_by_group(day_of_week=today, even_week=even_week, group=group)
            msg += print_pairs(pairs, today, even_week,
                               with_id=db.r_get_user_setting(PARAMS['show_id'], user_id))
        else:
            msg += "*Не удалось получить информацию о группе*\n" \
                   "Попробуйте исправить это при помощи кнопки \"Сменить группу\""

    else:
        msg = "*Спрашивать расписание на воскресенье... Гениально*"

    return msg


# Извлечение из БД списка пар на текущий день по ID пользователя
def get_pairs_tomorrow(user_id: int):
    """
    :param user_id: ID пользователя в ТГ
    :return: Список пар на текущий день для конкретного пользователя
    """
    even_week = int(datetime.date.today().strftime("%V")) % 2 == 0
    today = datetime.date.today().weekday() + 1
    msg = ""
    if today != 6:  # Если сегодня не суббота
        group = db.r_get_user_group(tg_id=user_id)
        if group:
            pairs = db.r_get_pairs_by_group(day_of_week=today+1, even_week=even_week, group=group)
            msg += print_pairs(pairs, today+1, even_week,
                               with_id=db.r_get_user_setting(PARAMS['show_id'], user_id))
        else:
            msg += "*Не удалось получить информацию о группе*\n" \
                   "Попробуйте исправить это при помощи кнопки \"Сменить группу\""
    else:
        # Пофиксим дату
        today = 1
        even_week = not even_week

        # И получим расписание
        group = db.r_get_user_group(tg_id=user_id)
        if group:
            pairs = db.r_get_pairs_by_group(day_of_week=today+1, even_week=even_week, group=group)
            msg += print_pairs(pairs, today+1, even_week,
                               with_id=db.r_get_user_setting(PARAMS['show_id'], user_id))
        else:
            msg += "*Не удалось получить информацию о группе*\n" \
                   "Попробуйте исправить это при помощи кнопки \"Сменить группу\""

    return msg


# Извлечение из БД списка пар на текущий день по ID пользователя
def get_pairs(user_id: int, day_of_week: int, even_week: bool):
    """
    :param user_id: ID пользователя в ТГ
    :param day_of_week: Порядковый номер дня недели
    :param even_week: Чётность недели (True для чётной недели, False для нечётной)
    :return: Список пар на выбранный день для конкретного пользователя
    """
    msg = ""
    if day_of_week != 7:  # Если сегодня не воскресенье
        group = db.r_get_user_group(tg_id=user_id)
        if group:
            pairs = db.r_get_pairs_by_group(day_of_week=day_of_week, even_week=even_week, group=group)
            msg += print_pairs(pairs, day_of_week, even_week,
                               with_id=db.r_get_user_setting(PARAMS['show_id'], user_id))
        else:
            msg += "*Не удалось получить информацию о группе*\n" \
                   "Попробуйте исправить это при помощи кнопки \"Сменить группу\""
    return msg


# Переводит "объект" цитаты в строку для отправки сообщением
def phrase_to_msg(phrase):
    return f"*{phrase[0]}*\n© {phrase[1]}"


# ======== -------- Первичная настройка / Смена группы -------- ======== #
# Реакция на активацию бота, переход на выбор института
@dp.message_handler(commands='start')
async def start_bot(message: Message):
    # Кинем сообщение в лог
    debug_log(message, debug_message="Старт бота от пользователя")

    try:
        # Получим список институтов из БД
        institutes = db.r_get_institute_list()

        # Сделаем клавиатуру для выбора института
        rkm_select_institute = ReplyKeyboardMarkup()
        for i in range(0, len(institutes), 2):
            try:
                rkm_select_institute.row(KeyboardButton(institutes[i]),
                                         KeyboardButton(institutes[i + 1]))
            except IndexError as _ex:
                rkm_select_institute.add(KeyboardButton(institutes[i]))

        # Установим первое состояние первичной настройки
        await StartSetting.select_institute.set()

        # Отправим приветственное сообщение и установим клавиатуру для выбора института
        await message.answer(f"Привет, {message.from_user.first_name})\nВыбери свой институт)",
                             reply_markup=rkm_select_institute)
    except Exception as _ex:
        debug_save_error(message, _ex, "Ошибка на async def start_bot()")
        await message.reply(f"Увы, я сейчас не могу обработать этот запрос, "
                            f"попробуйте чуть позднее\n\n```{_ex}```", parse_mode=ParseMode.MARKDOWN)


# Сохранение института, переход на выбор курса
@dp.message_handler(state=StartSetting.select_institute)
async def start_setting_select_institute(message: Message, state: FSMContext):
    # Кинем сообщение в лог
    debug_log(message, debug_message="Выбор института, переход к выбору курса")

    try:
        # Проверим существование выбранного института
        institutes = db.r_get_institute_list()
        if message.text not in institutes:
            await message.reply("Увы, но у нас нет такого института\n"
                                "Нажми на кнопку с названием твоего института")
        else:
            # Если всё ок, сохраним инфу в состояние
            async with state.proxy() as data:
                data['institute'] = message.text

            # Сменим состояние на второе состояние первичной настройки
            await StartSetting.next()

            # И отправим сообщение поользователю (вместе с клавиатурой для выбора курса)
            await message.reply("Я запомнил твой институт\nТеперь выбери курс",
                                reply_markup=rkm_select_course)
    except Exception as _ex:
        debug_save_error(message, _ex, "Ошибка на async def start_setting_select_institute()")
        await message.reply(f"Увы, я сейчас не могу обработать этот запрос, "
                            f"попробуйте чуть позднее\n\n```{_ex}```", parse_mode=ParseMode.MARKDOWN)


# Получение курса, переход к выбору группы
@dp.message_handler(state=StartSetting.select_course)
async def start_setting_select_course(message: Message, state: FSMContext):
    # Кинем сообщение в лог
    debug_log(message, debug_message="Выбор курса, переход к выбору группы")

    try:
        # Если отправлено не число, то сразу выйдем с соответствующим предупреждением
        # Состояние не изменим, то есть пользователь может сразу же выбрать правильный ответ
        if not message.text.isnumeric():
            await message.reply("Упс... Кажется что-то пошло не так\nПерепроверь введённый номер курса,"
                                " это должно быть просто число.", reply_markup=rkm_select_course)
            return 0

        # Если всё-таки число, то преобразуем его в нормальный вид и созхраним в состояние
        course = int(message.text)
        async with state.proxy() as data:
            data['course'] = course

            # Извлечём индекс института
            institute = data['institute']

        # Достанем список групп из конфига
        groups = db.r_get_group_list(institute, course)

        # И сгенерируем клавиатуру
        rkm_select_group = ReplyKeyboardMarkup()
        for i in range(0, len(groups), 2):
            try:
                rkm_select_group.row(KeyboardButton(groups[i]), KeyboardButton(groups[i+1]))
            except IndexError as _ex:
                rkm_select_group.row(KeyboardButton(groups[i]))

        # Изменим состояние для получения ответа на финальный вопрос
        await StartSetting.next()

        # И отправим сообщение
        await message.reply("Я запомнил твой курс\nТеперь выбери группу)",
                            reply_markup=rkm_select_group)
    except Exception as _ex:
        debug_save_error(message, _ex, "Ошибка на async def start_setting_select_course()")
        await message.reply(f"Увы, я сейчас не могу обработать этот запрос, "
                            f"попробуйте чуть позднее\n\n```{_ex}```", parse_mode=ParseMode.MARKDOWN)


# Получение выбранной группы и завершение регистрации пользователя
@dp.message_handler(state=StartSetting.select_group)
async def start_setting_select_group(message: Message, state: FSMContext):
    # Кинем сообщение в лог
    debug_log(message, debug_message="Выбор группы, завершение настройки")

    try:
        # Получим ID выбранной группы (если группы ещё нет, то вернётся 0)
        group_id = db.r_get_group_id(message.text)

        # Если группа существует в БД, сохраним данные пользователя в БД
        if group_id != 0:
            await message.answer("Я получил твою группу, сейчас сохраню и настройка будет завершена",
                                 reply_markup=ReplyKeyboardRemove())
            if db.w_register_user_by_id(message.from_user.id, message.from_user.first_name, group_id):
                # Сбросим состояние в нормальное
                await state.finish()
                await message.answer("Группа сохранена)\nПриятного пользования",
                                     reply_markup=rkm_std)
            else:
                await message.answer("Ошибка сохранения, исключение `pymysql.err.OperationalError`")
        else:  # Если такой группы нет (или пользователь ввёл что-то неладное)
            await message.reply("Последний этап остался...\nВыбери свою группу на клавиатуре")
    except Exception as _ex:
        debug_save_error(message, _ex, "Ошибка на async def start_setting_select_group()")
        await message.reply(f"Увы, я сейчас не могу обработать этот запрос, "
                            f"попробуйте чуть позднее\n\n```{_ex}```", parse_mode=ParseMode.MARKDOWN)


# ======== -------- Рабочие состояния бота -------- ======== #
# Изменение настроек пользователя
@dp.message_handler(state=UserStates.settings)
async def user_state_settings(message: Message, state: FSMContext):
    # Кинем сообщение в лог
    debug_log(message, debug_message="Действие, выполненное в настройках")

    try:
        # Преобразуем команду в нижний регистр для простоты обработки
        cmd = message.text.lower()

        # Сравним команду с каждой из допустимых
        if cmd == "включить цитаты":
            pass
        elif cmd == "выключить цитаты":
            pass
        elif cmd == "включить расписание":
            pass
        elif cmd == "выключить расписание":
            pass
        elif cmd == "включить зачёты":
            pass
        elif cmd == "выключить зачёты":
            pass
        elif cmd == "включить отладку":
            pass
        elif cmd == "выключить отладку":
            pass
        elif cmd == "выйти":
            await state.finish()
            await message.answer("Мы вышли из раздела настроек", reply_markup=rkm_std)
        else:
            await message.reply("Я не знаю такого действия")
    except Exception as _ex:
        debug_save_error(message, _ex, "Ошибка на async def user_state_settings()")
        await message.reply(f"Увы, я сейчас не могу обработать этот запрос, "
                            f"попробуйте чуть позднее\n\n```{_ex}```", parse_mode=ParseMode.MARKDOWN)


# Выбор недели для получения расписания на всю неделю
@dp.message_handler(state=UserStates.select_week)
async def user_state_select_week(message: Message, state: FSMContext):
    # Кинем сообщение в лог
    debug_log(message, debug_message="Выбор недели")

    try:
        # Преобразуем команду в нижний регистр для простоты обработки
        cmd = message.text.lower()

        # Сравним команду с каждой из допустимых
        if cmd == "нечётная":
            week = False
        elif cmd == "чётная":
            week = True
        elif cmd == "отмена":
            await state.finish()
            await message.answer("Получение расписания на неделю отменено",
                                 reply_markup=rkm_std)
            return 0
        else:
            await message.reply("Кажется, что-то введено неправильно :'(")
            return 0

        await state.finish()
        for i in range(1, 7):
            await message.answer(get_pairs(message.from_user.id, i, week),
                                 parse_mode=ParseMode.MARKDOWN, reply_markup=rkm_std)
    except Exception as _ex:
        debug_save_error(message, _ex, "Ошибка на async def user_state_select_week()")
        await message.reply(f"Увы, я сейчас не могу обработать этот запрос, "
                            f"попробуйте чуть позднее\n\n```{_ex}```", parse_mode=ParseMode.MARKDOWN)


# Выбор дня недели для получения расписания на конкретный день
@dp.message_handler(state=UserStates.select_day)
async def user_state_select_day(message: Message, state: FSMContext):
    # Кинем сообщение в лог
    debug_log(message, debug_message="Получение расписания на конкретный день")

    try:
        # Если пользователь хочет отменить это действие, сбросим состояние
        if message.text.lower() == "отмена":
            await state.finish()
            await message.answer("Получение расписания на конкретный день отменено",
                                 reply_markup=rkm_std)
            return 0

        # Преобразуем команду в нижний регистр для простоты обработки
        cmd = message.text.lower().split(" ")

        # Определим порядковый номер дня недели (если он есть)
        if cmd[0].upper() in DAYS_OF_WEEK:
            day_of_week = DAYS_OF_WEEK.index(cmd[0].upper())
        else:
            # Иначе откажемся от выполнения запроса и завершим процесс
            await message.reply("Тут что-то неправильно\n"
                                "Я не могу определить день недели")
            return 0

        # Если день недели получили, перейдём к определению чётности недели
        if cmd[1] == "нечёт":
            week = False
        elif cmd[1] == "чёт":
            week = True
        else:  # На случай ошибки ввода)
            await message.reply("Кажется, что-то введено неправильно :'(\n"
                                "Не могу определить чётность недели")
            return 0

        # Если всё ок, то сбросим состояние и выкинем пользователю расписание
        await state.finish()
        await message.answer(get_pairs(message.from_user.id, day_of_week, week),
                             parse_mode=ParseMode.MARKDOWN, reply_markup=rkm_std)

    except Exception as _ex:
        debug_save_error(message, _ex)
        await message.reply(f"Увы, я сейчас не могу обработать этот запрос, "
                            f"попробуйте чуть позднее\n\n```{_ex}```", parse_mode=ParseMode.MARKDOWN)


# ======== -------- Основное состояние бота -------- ======== #
# Реакция на команду и её выполнение
@dp.message_handler()
async def execute_command(message: Message):
    # Кинем сообщение в лог
    debug_log(message, debug_message="Запуск функции для выполнения команды")

    # Преобразуем сообщение в нижний регистр для упрощения обработки
    cmd = message.text.lower()

    # Сверим команду с каждой из возможных для определения дальнейших действий
    if cmd == "сегодня":  # Если пользователь хочет получить расписание на текущий учебный день
        await message.answer(get_pairs_today(message.from_user.id), parse_mode=ParseMode.MARKDOWN,
                             reply_markup=rkm_std)

    elif cmd == "завтра":  # Если пользователь хочет получить расписание на следующий учебный день
        await message.answer(get_pairs_tomorrow(message.from_user.id),
                             parse_mode=ParseMode.MARKDOWN, reply_markup=rkm_std)

    elif cmd == "конкретный день":  # Если пользователь хочет получить расписание на конкретный учебный день
        await UserStates.select_day.set()
        await message.answer("Теперь нужно выбрать день недели",
                             reply_markup=rkm_select_day)

    elif cmd == "на неделю":  # Если пользователь хочет получить расписание на определённую неделю
        await UserStates.select_week.set()
        await message.answer("Теперь нужно выбрать неделю\nРасписание на 2 недели очень "
                             "часто оказывается слишком большим для пересылки в ТГ",
                             reply_markup=rkm_select_week)

    elif cmd == "цитата":  # Если пользователь хочет получить цитатку
        await message.answer(phrase_to_msg(db.r_get_random_phrase()),
                             parse_mode=ParseMode.MARKDOWN, reply_markup=rkm_std)

    elif cmd == "сменить группу":  # Если пользователь хочет сменить группу
        # Кинем сообщение в лог
        debug_log(message, debug_message="Пользователь хочет сменить группу")

        # Получим список институтов из БД
        institutes = db.r_get_institute_list()

        if len(institutes) != 0:
            # Сделаем клавиатуру для выбора института
            rkm_select_institute = ReplyKeyboardMarkup()
            for i in range(0, len(institutes), 2):
                try:
                    rkm_select_institute.row(KeyboardButton(institutes[i]),
                                             KeyboardButton(institutes[i + 1]))
                except IndexError as _ex:
                    rkm_select_institute.add(KeyboardButton(institutes[i]))

            # Установим первое состояние первичной настройки
            await StartSetting.select_institute.set()

            # Отправим приветственное сообщение и установим клавиатуру для выбора института
            await message.answer(f"Выбери свой институт)", reply_markup=rkm_select_institute)

        else:
            await message.answer("Упс, в базе данных нет групп ни одного института")

    elif cmd == "настройки":  # Если пользователь хочет перейти в настройки
        await UserStates.settings.set()
        await message.answer(SETTINGS_DESCRIPTIONS_MSG, parse_mode=ParseMode.MARKDOWN,
                             reply_markup=rkm_settings)

    elif message.from_user.id in ADMINS:
        cmd = cmd.split(" ")
        if cmd[0] == "get_logs" and len(cmd) == 1:
            await message.answer(logger.get_logs(200))
        elif cmd[0] == "get_logs" and len(cmd) == 2 and cmd[1].isnumeric():
            await message.answer(logger.get_logs(int(cmd[1])))
        elif cmd[0] == "send" and len(cmd) >= 3 and cmd[1].isnumeric():
            try:
                await bot.send_message(int(cmd[1]), " ".join(cmd[2::]))
                await message.answer("Сообщение отправлено")
            except Exception as _ex:
                debug_save_error(message, _ex)
                await message.answer(f"Ошибка отправки сообщения\n\n```{_ex}```")
        elif cmd[0] == "send" and len(cmd) >= 3 and cmd[1] == "*":
            for user_id in db.r_get_all_users():
                try:
                    await bot.send_message(user_id, " ".join(cmd[2::]))
                    await message.answer(f"Сообщение пользователю {user_id} отправлено")
                except Exception as _ex:
                    debug_save_error(message, _ex)
                    await message.answer(f"Ошибка отправки сообщения пользователю {user_id}\n\n```{_ex}```")
            await message.answer("Действие выполнено, сообщения об ошибках выше")

    else:
        await message.reply("Я не понимаю эту команду...", reply_markup=rkm_std)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
