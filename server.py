import http.server
import json
import socketserver
import datetime

import database


PORT = 8080

db = database.DataBase()

groups = {
    'is_b_21_3_o': "ис/б-21-3-о",
}


def print_pairs(pairs: list):
    msg = []
    for pair in pairs:
        msgi = dict()
        msgi['id'] = pair[0]
        msgi['group'] = pair[1]
        msgi['even_week'] = (pair[2] == 1)
        msgi['day_of_week'] = pair[3]
        msgi['ordinal'] = pair[4]
        msgi['lesson'] = pair[5]
        if pair[6] != "":
            msgi['teacher'] = pair[6]
        if pair[7] != "":
            msgi['type'] = pair[7]
        if pair[8] != "":
            msgi['location'] = pair[8]
        msg.append(msgi)

    msg = json.dumps(msg, ensure_ascii=False)
    return msg


def get_today(group: str):
    even_week = int(datetime.date.today().strftime("%V")) % 2 == 0
    today = datetime.datetime.today().weekday() + 1
    msg = ""
    if today != 6:  # Если сегодня не воскресенье
        pairs = db.r_get_pairs_by_group(day_of_week=today, even_week=even_week, group=group)
        msg += print_pairs(pairs)
    return msg


def get_concret_day(even_week: bool, day_of_week: int, group: str):
    pairs = db.r_get_pairs_by_group(day_of_week, even_week, group)
    return print_pairs(pairs)


def get_week(group, even_week):
    msg = ""
    for i in range(1, 7):
        msg += bold(days_of_week[i]) + "\n"
        pairs = db.r_get_pairs_by_group(day_of_week=i, even_week=even_week, group=group)
        msg += print_pairs(pairs=pairs)
        msg += "\n"
    return msg


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        path = self.path  # Получим строку запроса

        # Отделим лишние символы
        if path[0] == "/":
            path = path[1::]
        if path[0] == "?":
            path = path[1::]

        path = path.split("&")  # Отделим команды друг от друга

        commands = dict()

        for cmd in path:
            cmd = cmd.split("=")
            if len(cmd) == 2:
                commands[cmd[0]] = cmd[1]

        response = ""

        try:
            # Определим требуемое действие
            if commands.get('action') == "read" and commands.get('read') == "pairs":  # Если нужно узнать расписание

                if commands.get('group') in groups.keys():  # Если для группы разрешено использование API

                    # Если указан конкретный день, получим распу на запрошенный день
                    if commands.get('even_week') in ['true', 'false'] and commands.get('dof', 'no_dof') != 'no_dof' \
                            and commands.get('dof', 'no_dof').isnumeric():
                        response = get_concret_day((commands.get('even_week', 'no_dof') == 'true'),
                                                   int(commands.get('dof', 'no_dof')),
                                                   groups.get(commands.get('group')))

                    # Иначе вернём расписание на текущий день
                    else:
                        response = get_today("ис/б-21-3-о")

            if commands.get('action') == "read" and commands.get('read') == "phrase":
                response = get_random_phrase_to_msg(api=True)
        except Exception as _ex:
            response = "Err500<br>\n" + str(_ex)

        self.wfile.write(str.encode(response, "utf-16"))
        return 0


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Serving at port", PORT)
        httpd.serve_forever()
