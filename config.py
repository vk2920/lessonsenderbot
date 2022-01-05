INSTITUTES = [
    "ИЯЭиП",
    "Политехнический институт",
    "Морской институт",
    "ИРиИБ",
    "ГПИ",
    "ИФЭиУ",
    "ИИТУТС",
    "Юридический институт",
    "ИОНиМО",
    "ИНТИ",
    "ИРГ",
    "ИДП",
]

GROUPS = [
    [],
    [],
    [],
    [],
    [   # ГПИ
        ["п/б-21-1-о", "п/б-21-2-о", "псд/б-21-1-о", "псд/б-21-2-о", "под/б-21-1-о",
         "пон/б-21-2-о", "поия/б-21-3-о", "помф/б-21-6-о", "поми/б-21-8-о", "порл/б-21-4-о",
         "поио/б-21-7-о", "пофк/б-21-3-о", "пофк/б-21-4-о", "фил/б-21-1-о", "фил/б-21-2-о", "фил/б-21-3-о"],
        ["помф/б-20-6-о", "поио/б-20-7-о", "порл/б-20-4-о", "пофк/б-20-3-о", "пофк/б-20-4-о",
         "псд/с-20-1-о", "псд/м-20-2-о", "под/б-20-1-о", "пон/б-20-2-о", "поия/б-20-3-1-о",
         "поия/б-20-3-2-о", "поия/б-20-4-1-о", "поия/б-20-4-2-о", "поия/б-20-5-о"],
        ["п/б-19-1-о", "помф/б-19-1-о", "поио/б-19-2-о", "порл/б-19-4-о", "пофк/б-19-3-о",
         "псд/с-19-1-о", "под/б-19-1-о", "пон/б-19-2-о", "поия/б-19-3-1-о", "поия/б-19-3-2-о"],
        ["п/б-18-1-о", "пофк/б-18-1-о", "пофк/б-18-2-о", "пофк/б-18-1-о", "псд/с-18-1-о",
         "псд/с-18-2-о", "под/б-18-1-о", "пон/б-18-2-о"],
        ["псд/с-17-1-о"],
    ],
    [],
    [   # ИИТУТС
        ["ис/б-21-1-о", "ис/б-21-2-о", "ис/б-21-3-о", "пи/б-21-1-о", "ивт/б-21-1-о",
         "ивт/б-21-2-о", "ивт/б-21-3-о", "пин/б-21-1-о", "утс/б-21-11-о", "утс/б-21-12-о"],
        ["ис/б-20-1-о", "ис/б-20-2-о", "ис/б-20-3-о", "пи/б-20-1-о", "ивт/б-20-1-о",
         "ивт/б-20-2-о", "пин/б-20-1-о", "утс/б-20-1-о", "утс/б-20-2-о"],
        ["ис/б-19-1-о", "ис/б-19-2-о", "пи/б-19-1-о", "ивт/б-19-1-о", "ивт/б-19-2-о",
         "пин/б-19-1-о", "утс/б-19-1-о", "утс/б-19-2-о"],
        ["ис/б-18-1-о", "ис/б-18-2-о", "пи/б-18-1-о", "утс/б-18-1-о", "ивт/б-18-1-о", "ивт/б-18-1-о"],
        ["ис/м-21-1-о", "пи/м-21-1-о", "утс/м-21-1-о", "мир/м-21-1-о", "ивт/м-21-1-о", "пин/м-21-1-о"],
        ["ис/м-20-1-о", "пи/м-20-1-о", "утс/м-20-1-о", "мир/м-20-1-о", "ивт/м-20-1-о", "пин/м-20-1-о"]
    ],
    [],
    [],
    [],
    [],
    [],
]

ADMINS = [
    470985286,
    1943247578,
]

ADMIN_PASSWD = "cd0d4907f4c357d4d29a2db036d429994b1217542efad6384011854360cf84c4" \
               "56b733f49a6b5b54ac9baa51acc3f727211b48493ed50ff856c46ae15f7faed5"

PARAMS = {
    'auto_phrases': 0,
    'auto_pairs': 1,
    'show_id': 2,
    'reminders': 3,
}

SETTINGS_DESCRIPTIONS_MSG = "Раздел пользовательских настроек:\n*Включить/Выключить цитаты* — позволяет боту " \
                            "автоматически присылать Вам цитатки с рандомной периодичностью\n*Включить/Выключить " \
                            "расписание* (_\rбета-функция_\r) — позволяет боту ежедневно присылать Вам расписание " \
                            "на день\n*Включить/Выключить зачёты* — позволяет боту автоматически напоминать Вам о " \
                            "предстоящих зачётах и экзаменах (за 1 и 3 дня)\n*Включить/Выключить отладку* — не даёт " \
                            "особых привилегий, позволяет видеть идентификаторы строк в БД"

DAYS_OF_WEEK = ["ВС", "ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
DAYS_OF_WEEK_FULL = ["воскресенье", "понедельник", "вторник", "среда",
                     "четверг", "пятница", "суббота", "воскресенье"]
DAYS_OF_WEEK_FULL_UPPER = ["Воскресенье", "Понедельник", "Вторник", "Среда",
                     "Четверг", "Пятница", "Суббота", "Воскресенье"]
