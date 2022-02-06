import logging
import os
import sys

import pymysql

from config import PARAMS


class DataBase:
    def __init__(self):
        try:
            # pymysql.install_as_MySQLdb()
            self._connection = pymysql.connect(
                host=os.environ['DB_HOST'],
                port=int(os.environ['DB_PORT']),
                user=os.environ['DB_USER'],
                password=os.environ['DB_PASSWD'],
                database=os.environ['DB_NAME']
            )
        except pymysql.err.OperationalError as _ex:
            logging.error(" Ошибка подключения к БД, возможные причины чуть ниже")
            logging.error("     1. Траблы с подключением")
            logging.error("     2. Траблы с данными в переменных окружения (или их нет)")
            logging.error(f"\n Хост: {os.environ['DB_HOST']}\n User: {os.environ['DB_USER']}\n Password: "
                          f"{os.environ['DB_PASSWD']}\n DB: {os.environ['DB_NAME']}")
            logging.error(" А вот и содержимое исключения:")
            logging.error(_ex)
            sys.exit()

    def r_get_pairs_by_group(self, day_of_week: int, even_week: bool, group: int, errs: int = 0):
        """
        :param day_of_week: порядковый номер дня недели (int, 1~6)
        :param even_week: True, если неделя чётная, иначе False
        :param group: порядковый номер группы в БД
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: список пар на запрошенный день, или False в случае ошибки
        """
        try:
            pairs_list = []
            with self._connection.cursor() as cur:
                sql = f"SELECT * FROM public.pairs WHERE group_id = {group} AND even_week = {even_week} " \
                      f"AND day_of_week = {day_of_week} ORDER BY ordinal"
                cur.execute(sql)
                for row in cur.fetchall():
                    pairs_list.append(row)
            return pairs_list
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.r_get_pairs_by_group(day_of_week, even_week, group, errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_user_group(self, tg_id: int, errs: int = 0) -> int:
        """
        Функция для получения номера группы, которой принадлежит пользователь
        :param tg_id: ID пользователя в ТГ
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: Порядковый номер группы, которой принадлежит пользователь или False в случае ошибки
        """
        try:
            with self._connection.cursor() as cur:
                cur.execute(f"SELECT group_id FROM public.users WHERE id = {tg_id} LIMIT 1;")
                group = int(list(cur.fetchone())[0])
                return group
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.r_get_user_group(tg_id, errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_user_setting(self, param: int, tg_id: int, errs: int = 0) -> bool:
        """
        Получает информацию о конкретной настройке пользователя
        :param param: Номер параметра (константа из конфиг-файла)
        :param tg_id: ID пользователя в ТГ
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: Значение параметра (True / False) или False в случае ошибки
        """
        try:
            if param == PARAMS['auto_phrases']:
                sql = f"SELECT setting_auto_phrases FROM public.users WHERE id = {tg_id} LIMIT 1;"

            elif param == PARAMS['auto_pairs']:
                sql = f"SELECT setting_auto_pairs FROM public.users WHERE id = {tg_id} LIMIT 1;"

            elif param == PARAMS['show_id']:
                sql = f"SELECT setting_show_pairs_ids FROM public.users WHERE id = {tg_id} LIMIT 1;"

            elif param == PARAMS['reminders']:
                sql = f"SELECT setting_tests_reminders FROM public.users WHERE id = {tg_id} LIMIT 1;"

            else:
                return False

            with self._connection.cursor() as cur:
                cur.execute(sql)
                return bool(cur.fetchone()[0])
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return bool(self.r_get_user_setting(param, tg_id, errs=errs+1))
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_random_chat_id(self, errs: int = 0) -> int:
        """
        Достаёт из БД случайный ID пользователя в ТГ (ID чата ЛС с этим пользователем)
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: ID пользователя в ТГ
        """
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT id FROM public.users ORDER BY RAND() LIMIT 1"
                cur.execute(sql)
                user = cur.fetchone()[0]
                if user is not None and user != "" and user != 0:
                    return user
                else:
                    return 0
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.r_get_random_chat_id(errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_all_users(self, errs: int = 0):
        """
        Достаёт из БД ID всех пользователей в ТГ
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: список из ID пользователей в ТГ
        """
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT chat_id FROM public.users;"
                cur.execute(sql)
                users = list(cur.fetchall())
                user_ids = list()
                for user in users:
                    if not (user[0] is None):
                        user_ids.append(user[0])
                print("Список пользователей для отправки объявления: " + str(user_ids))
                return user_ids
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.r_get_all_users(errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_random_phrase(self, errs: int = 0):
        """
        Достаёт из БД случайную цитату
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: цитата (цитата, автор)
        """
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT phrase, author FROM public.phrases WHERE active = 1 ORDER BY RAND() LIMIT 1;"
                cur.execute(sql)
                phrase = cur.fetchone()
                return phrase
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.r_get_random_phrase(errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_institute_list(self, errs: int = 0):
        """
        Достаёт из БД список доступных институтов (по таблице групп)
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: список строк с названиями институтов
        """
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT DISTINCT institute FROM public.groups;"
                cur.execute(sql)
                institutes = cur.fetchall()
                institute_list = list()
                for institute in institutes:
                    institute_list.append(institute[0])
                return institute_list
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.r_get_institute_list(errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_group_list(self, institute: str, course: int, errs: int = 0):
        """
        Достаёт из БД список групп выбранного института на выбранном курсе
        :param institute: Название института
        :param course: Порядковый номер курса
        :param errs: Количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: Список строк (наименования групп)
        """
        try:
            with self._connection.cursor() as cur:
                sql = f"SELECT DISTINCT group_name FROM public.groups "\
                      f"WHERE institute = %s AND course = {course};"
                cur.execute(sql, (institute))
                groups = cur.fetchall()
                group_list = list()
                for group in groups:
                    group_list.append(group[0])
                return group_list
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.r_get_group_list(institute, course, errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_group_id(self, group_name: str, errs: int = 0) -> int:
        """
        Получает из БД порядковый номер группы по названию
        :param group_name: Название группы
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: Порядковый номер группы
        """
        try:
            with self._connection.cursor() as cur:
                sql = f"SELECT id FROM public.groups WHERE group_name = %s;"
                cur.execute(sql, (group_name))
                return cur.fetchone()[0]
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.r_get_group_id(group_name, errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def w_register_user_by_id(self, tg_id: int, name: str, group_id: int, errs: int = 0):
        """
        :param tg_id: id пользователя в ТГ (int)
        :param name: ФИО пользователя
        :param group_id: ID группы пользователя
        :param errs: количество ошибок (применяется для ограничения рекурсивного
            выполнения при проблемах с подключением)
        :return: True, если запись произведена успешно, иначе False
        """
        try:
            with self._connection.cursor() as cur:
                tg_id = str(tg_id)
                group_id = str(group_id)
                sql = f"SELECT id FROM public.users WHERE id = {tg_id}"
                cur.execute(sql)
                if len(list(cur.fetchall())) != 0:
                    sql = f"UPDATE public.users SET group_id = {group_id}, name = '{name}' WHERE id = {tg_id}"
                else:
                    sql = f"INSERT INTO public.users (id, name, group_id) VALUES ({tg_id}, '{name}', {group_id});"
                cur.execute(sql)
                self._connection.commit()
            return True
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.w_register_user_by_id(tg_id, name, group, errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    # Административные методы класса DataBase
    def w_remove_pair_by_pair_id(self, pair_id: int, errs: int = 0):
        try:
            with self._connection.cursor() as cur:
                sql = f"DELETE FROM public.pairs WHERE id = {pair_id}"
                cur.execute(sql)
                self._connection.commit()
                return True
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.w_remove_pair_by_pair_id(pair_id, errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def r_get_pair_by_pair_id(self, pair_id: int, errs: int = 0):
        try:
            with self._connection.cursor() as cur:
                sql = f"SELECT * FROM public.pairs WHERE id = {pair_id}"
                cur.execute(sql)
                self._connection.commit()
                return cur.fetchone()
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.w_remove_pair_by_pair_id(pair_id, errs=erss+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def w_move_pair_by_pair_id(self, pair_id: int, day_of_week: int, ordinal: int, errs: int = 0):
        try:
            with self._connection.cursor() as cur:
                sql = f"UPDATE public.pairs SET day_of_week = {day_of_week}, ordinal = {ordinal} WHERE id = {pair_id}"
                cur.execute(sql)
                self._connection.commit()
                return True
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.w_move_pair_by_pair_id(pair_id, day_of_week, ordinal, errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def w_change_pair_location_by_pair_id(self, pair_id: int, location: str, errs: int = 0):
        try:
            with self._connection.cursor() as cur:
                sql = f"UPDATE public.pairs SET location = {location} WHERE id = {pair_id};"
                cur.execute(sql)
                self._connection.commit()
                return True
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.w_change_pair_location_by_pair_id(pair_id, location, errs=errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def w_add_pair(self, group: str, even_week: bool, day_of_week: int, ordinal: int, lesson: str, teacher: str,
                   pair_type: str, location: str, errs: int = 0):
        try:
            with self._connection.cursor() as cur:
                sql = f"INSERT INTO public.pairs (group, even_week, day_of_week, ordinal, lesson, teacher, type, " \
                      f"location) VALUES (%s, {1 if even_week else 0}, {day_of_week}, {ordinal}, %s, %s, %s, %s);"
                cur.execute(sql, (group, lesson, teacher, pair_type, location))
                self._connection.commit()
                cur.execute("SELECT id FROM public.pairs ORDER BY id DESK LIMIT 1;")
                return True
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.w_add_pair(group, even_week, day_of_week, ordinal, lesson, teacher, pair_type,
                                       location, errs+1)
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def w_recreate_db(self):
        try:
            with self._connection.cursor() as cur:
                with open('database.sql', 'r') as f:
                    sql = f.read()
                cur.execute(sql)
                return True
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.w_recreate_db()
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False

    def w_execute_current_sql(self):
        try:
            with self._connection.cursor() as cur:
                with open('execute.sql', 'r') as f:
                    sql = f.read()
                cur.execute(sql)
                return True
        except pymysql.err.OperationalError as _ex:
            if errs <= 3:
                logging.error("Ошибка подключения, переподключение...")
                # Реинициализация объекта для переподключения к БД
                self.__init__()
                return self.w_execute_current_sql()
            else:
                logging.error("Ошибка работы с БД. Выход из метода")
                return False


db = DataBase()
