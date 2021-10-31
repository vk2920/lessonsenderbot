import logging
import os
import sys

import pymysql


class DataBase:
    def __init__(self):
        try:
            self._connection = pymysql.connect(
                os.environ['DB_HOST'],
                os.environ['DB_USER'],
                os.environ['DB_PASSWD'],
                os.environ['DB_NAME']
            )
        except Exception as _ex:
            logging.error("Ошибка подключения к БД, возможные причины чуть ниже")
            logging.error("    1. Траблы с подключением")
            logging.error("    2. Траблы с данными в переменных окружения (или их нет)")
            logging.error(f"Хост: {os.environ['DB_HOST']}, User: {os.environ['DB_USER']}, Password: "
                          f"{os.environ['DB_PASSWD']}, DB: {os.environ['DB_NAME']}")
            # sys.exit()

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
        except pymysql.OperationalError as _ex:
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
        except pymysql.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.r_get_user_group(tg_id)

    def r_get_random_chat_id(self):
        try:
            with self._connection.cursor() as cur:
                sql = "SELECT chat_id FROM public.users ORDER BY RANDOM() LIMIT 1"
                cur.execute(sql)
                chat_id = list(cur.fetchone())[0]
                if chat_id is not None and chat_id != "" and chat_id != 0:
                    return int(chat_id)
                else:
                    return 0
        except pymysql.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.r_get_random_chat_id()

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
        except pymysql.OperationalError as _ex:
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
        except pymysql.OperationalError as _ex:
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
        except pymysql.OperationalError as _ex:
            logging.error("Ошибка подключения, переподключение...")
            # Реинициализация объекта для переподключения к БД
            self.__init__()
            return self.w_remove_pair_by_pair_id(pair_id)
