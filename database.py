import logging
import os
import sys

import pymysql


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
            logging.error(f" Хост: {os.environ['DB_HOST']},\n User: {os.environ['DB_USER']},\n Password: "
                          f"{os.environ['DB_PASSWD']},\n DB: {os.environ['DB_NAME']}")
            logging.error(" А вот и содержимое исключения:")
            logging.error(_ex)
            sys.exit()

    def r_get_pairs_by_group(self, day_of_week: int, even_week: bool, group: str):
        """
        :param day_of_week: порядковый номер дня недели (int, 1~6)
        :param even_week: True, если неделя чётная, иначе False
        :param group: группа в формате "ИС/б-21-3-о", где
             -- ИС — направление подготовки
             -- б — бакалавриат (м — магистратура)
             -- 21 — год зачисления на первый курс
             -- 3 — номер потока
             -- о — очная форма обучения (з — заочная)
        :return: список пар на запрошенный день
        """
        try:
            pairs_list = []
            with self._connection.cursor() as cur:
                sql = f"SELECT * FROM public.pairs WHERE " + \
                      f"group_name = '{group}' AND even_week = {even_week} AND " + \
                      f"day_of_week = {day_of_week} ORDER BY ordinal"
                cur.execute(sql)
                for row in cur.fetchall():
                    pairs_list.append(row)
            return pairs_list
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.r_get_pairs_by_group(day_of_week, even_week, group)

    def r_get_user_group(self, tg_id: int):
        try:
            with self._connection.cursor() as cur:
                cur.execute(f"""SELECT group_name FROM public.users WHERE tg_id = {tg_id} LIMIT 1""")
                group = list(cur.fetchone())[0]
                return group
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.r_get_user_group(tg_id)

    def r_get_random_chat_id(self):
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT chat_id, phrases FROM public.users ORDER BY RAND() LIMIT 1"
                cur.execute(sql)
                user = list(cur.fetchone())
                if user[0] is not None and user[0] != "" and user[0] != 0:
                    user[0] = int(user[0])
                    user[1] = int(user[1])
                    return user
                else:
                    return 0
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.r_get_random_chat_id()

    def r_get_all_users(self):
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT chat_id FROM public.users;"
                cur.execute(sql)
                users = list(cur.fetchall())
                user_ids = list()
                for user in users:
                    user_ids.append(user[0])
                return user_ids
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.r_get_all_users()

    def r_get_pairs_chat_ids(self):
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT chat_id, group_name FROM public.users WHERE pairs = 1"
                cur.execute(sql)
                user_list = list(cur.fetchall())
                users_dict = dict()
                for user in user_list:
                    if user[0] is not None and user[0] != "" and user[0] != 0:
                        user[0] = int(user[0])
                        if user[1] is not None and user[1] != "":
                            if users_dict.get(user[1], "no") == "no":
                                users_dict[user[1]] = list()
                            users_dict[user[1]].append(user[0])

                return users_dict

        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.r_get_pairs_chat_ids()

    def r_get_random_phrase(self):
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT phrase, author FROM public.phrases WHERE active = 1 ORDER BY RAND() LIMIT 1"
                cur.execute(sql)
                phrase = cur.fetchone()
                return phrase
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.r_get_random_phrase()

    def w_set_chat_id(self, user_id: int, chat_id: int):
        """
        :param user_id: ID пользователя в ТГ
        :param chat_id: ID чата с данным пользователем
        :return: True, если запись произведена успешно, иначе False
        """
        try:
            with self._connection.cursor() as cur:
                sql = f"UPDATE public.users SET chat_id = {chat_id} WHERE tg_id = {user_id}"
                cur.execute(sql)
            self._connection.commit()
            return True
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.w_set_chat_id(user_id, chat_id)

    def w_register_user_by_id(self, tg_id: int, name: str, group: str):
        """
        :param tg_id: id пользователя в ТГ (int)
        :param name: ФИО пользователя
        :param group: группа пользователя в формате
        :return: True, если запись произведена успешно, иначе False
        """
        try:
            with self._connection.cursor() as cur:
                sql = f"SELECT tg_id FROM public.users WHERE tg_id = {tg_id}"
                cur.execute(sql)
                if len(list(cur.fetchall())) != 0:
                    sql = f"UPDATE public.users SET group_name = '{group}' WHERE tg_id = {tg_id}"
                else:
                    sql = f"INSERT INTO public.users (tg_id, name, group_name) VALUES ({tg_id}, '{name}', '{group}');"
                cur.execute(sql)
                self._connection.commit()
            return True
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.w_register_user_by_id(tg_id, name, group)

    # Административные метода класса DataBase
    def w_remove_pair_by_pair_id(self, pair_id: int):
        try:
            with self._connection.cursor() as cur:
                sql = f"DELETE FROM public.pairs WHERE id = {pair_id}"
                cur.execute(sql)
                self._connection.commit()
                return True
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.w_remove_pair_by_pair_id(pair_id)

    def r_get_pair_by_pair_id(self, pair_id: int):
        try:
            with self._connection.cursor() as cur:
                sql = f"SELECT * FROM public.pairs WHERE id = {pair_id}"
                cur.execute(sql)
                self._connection.commit()
                return cur.fetchone()
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.w_remove_pair_by_pair_id(pair_id)

    def w_move_pair_by_pair_id(self, pair_id: int, day_of_week: int, ordinal: int):
        try:
            with self._connection.cursor() as cur:
                sql = f"UPDATE public.pairs SET day_of_week = {day_of_week}, ordinal = {ordinal} WHERE id = {pair_id}"
                cur.execute(sql)
                self._connection.commit()
                return True
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.w_move_pair_by_pair_id(pair_id, day_of_week, ordinal)

    def w_change_pair_location_by_pair_id(self, pair_id: int, location: str):
        try:
            with self._connection.cursor() as cur:
                sql = f"UPDATE public.pairs SET location = {location} WHERE id = {pair_id};"
                cur.execute(sql)
                self._connection.commit()
                return True
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.w_change_pair_location_by_pair_id(pair_id, location)

    def w_add_pair(self, group: str, even_week: bool, day_of_week: int, ordinal: int, lesson: str, teacher: str,
                   pair_type: str, location: str):
        try:
            with self._connection.cursor() as cur:
                sql = f"INSERT INTO public.pairs (group, even_week, day_of_week, ordinal, lesson, teacher, type, " \
                      f"location) VALUES ('{group}', {even_week}, {day_of_week}, {ordinal}, '{lesson}', '{teacher}'," \
                      f"'{pair_type}', '{location}');"
                cur.execute(sql)
                self._connection.commit()
                cur.execute("SELECT id FROM public.pairs ORDER BY id DESK LIMIT 1;")
                return True
        except pymysql.err.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.w_add_pair(group, even_week, day_of_week, ordinal, lesson, teacher, pair_type, location)


db = DataBase()