import psycopg2
import re

class ControlClientsDB:

    def __init__(self, dbname, user, password, host='127.0.0.1', port='5432'):
        '''Подключение к базе данных при инициализации объекта класса
        В БД автоматически создаются две таблицы'''
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port

        conn = psycopg2.connect(database=self.dbname, user=self.user, password=self.password, host=self.host,
                                port=self.port)
        with conn.cursor() as cur:
            cur.execute("""DROP TABLE IF EXISTS Phone;
                           DROP TABLE IF EXISTS Clients;""")

            cur.execute("""CREATE TABLE Clients
                          (id SERIAL PRIMARY KEY,
                          name CHAR(40) NOT NULL,
                          surname CHAR(40) NOT NULL,
                          email CHAR(50));""")

            cur.execute(r"""CREATE TABLE Phone
                           (id SERIAL PRIMARY KEY,
                            id_client INT NOT NULL,
                            phone CHAR(16) CHECK(phone ~* '\+?(7|8)(-?\d{3}){2}(-?\d{2}){2}') NOT NULL,
                            FOREIGN KEY (id_client) REFERENCES Clients (id) ON UPDATE CASCADE ON DELETE CASCADE);""")
            conn.commit()
        conn.close()
        print('||Таблицы Clients и Phone успешно созданы')


    def add_new_client(self, name, surname, email='no email'):
        """Добавляет нового клиента в БД"""
        conn = psycopg2.connect(database=self.dbname, user=self.user, password=self.password, host=self.host,
                                port=self.port)
        with conn.cursor() as cur:
            cur.execute(f"""INSERT INTO Clients (name, surname, email)
                            VALUES ('{name}', '{surname}', '{email}');""")
            conn.commit()
        conn.close()
        print(f'✓ Клиент {name} {surname} успешно добавлен')


    def add_phone_client(self, phone, id=None, name=None, surname=None):
        """Функция для добавления номера телефона клиенту по ID или Имени Фамилии"""
        if id is None and (name is None or surname is None):
            print('✖ Для добавления телефона быть введён id или имя с фамилией клиента')
            return

        conn = psycopg2.connect(database=self.dbname, user=self.user, password=self.password, host=self.host,
                                port=self.port)
        with conn.cursor() as cur:
            try:
                if id:
                    cur.execute(f"""INSERT INTO Phone (id_client, phone)
                                   VALUES ('{id}', '{phone}');""")

                else:
                    cur.execute(f"""INSERT INTO Phone (id_client, phone)
                                    VALUES ((SELECT id
                                             FROM Clients
                                             WHERE name = '{name}' and surname = '{surname}'), '{phone}');""")
                conn.commit()

            except psycopg2.errors.StringDataRightTruncation:
                print('✖ Ошибка при вводе номера телефона')
            except psycopg2.errors.NotNullViolation:
                print('??? Имя или id пользователя не найдено в таблице Clients')
            else:
                if id:
                    print(f"+++ Номер телефона {phone} успешно добавлен пользователю с id {id}")
                else:
                    print(f"+++ Номер телефона {phone} успешно добавлен пользователю с именем {name} {surname}")


    def update_data_client(self, id, name=None, surname=None, email=None, phone=None):
        """Функция для обновления данных пользователя по его id"""
        if name == surname == email == phone is None:
            print('??? Не указаны данные для обновления')
            return

        def replace_info(pole, info_):
            cur.execute(f"""UPDATE Clients
                            SET {pole} = %s
                            WHERE id = %s""", (info_, id))
            print_info = {'name': 'Имя', 'surname': 'Фамилия', 'email': 'Email'}
            print(f'---> {print_info[pole]} пользователя {info[0][1].strip()} {info[0][2].strip()} заменено на {info_}')

        conn = psycopg2.connect(database=self.dbname, user=self.user, password=self.password, host=self.host,
                                port=self.port)
        with conn.cursor() as cur:
            cur.execute(f"""SELECT * FROM Clients WHERE id = %s;""", (id,))
            info = cur.fetchall()
            if not info:
                print(f'??? Не найден пользователь с id {id}')
                conn.close()
                return

            if name:
                replace_info('name', name)
            if surname:
                replace_info('surname', surname)
            if email:
                replace_info('email', email)
            if phone:
                if re.findall(r'\+?(7|8)(-?\d{3}){2}(-?\d{2}){2}', phone):
                    cur.execute(f"""UPDATE Phone
                                    SET phone = '{phone}'
                                    WHERE id_client = %s""", (id,))
                    print(f'---> Телефон пользователя {info[0][1].strip()} {info[0][2].strip()} заменен на {phone}')

                else:
                    print('XXX Неправильно введён номер телефона XXX')
            conn.commit()

        conn.close()


    def delete_info(self, id, phone=None):
        """Функция для удаления всех данных о пользователе или только о его номере телефона по его id
        Удаляет все данные, если введён только id, удаляет только номер телефона, если введён id и phone"""
        conn = psycopg2.connect(database=self.dbname, user=self.user, password=self.password, host=self.host,
                                port=self.port)
        with conn.cursor() as cur:
            cur.execute("""SELECT * FROM Clients WHERE id = %s""", (id, ))
            info = cur.fetchall()
            if info:
                if phone is not None:
                    cur.execute("""DELETE FROM Phone
                                   WHERE id_client = %s and phone = %s""", (id, phone))
                    print(f'✖ Номер телефона {phone} у пользователя {info[0][1].strip()} {info[0][2].strip()} удален')
                else:
                    cur.execute("""DELETE FROM Clients
                                   WHERE id = %s""", (id,))

                    print(f'✖ Все данные о пользователе {info[0][1].strip()} {info[0][2].strip()} удалены')
                conn.commit()
            else:
                print(f'??? Пользователя с {id} не найдено')
        conn.close()


    def search_info_client(self, id=None, name=None, surname=None, email=None, phone=None):
        """Функция выводит всю информацию о клиенте"""
        if id == name == surname == email == phone is None:
            print('Для поиска необходима информация о клиенте')
            return

        info = {id: [id, 'Clients.id'],
                name: [name, 'name'],
                surname: [surname, 'surname'],
                email: [email, 'email'],
                phone: [phone, 'phone']}
        key = info[next(key for key in list(info.keys()) if key is not None)]
        conn = psycopg2.connect(database=self.dbname, user=self.user, password=self.password, host=self.host,
                                port=self.port)

        with conn.cursor() as cur:

            def search_client(info_, pole):
                cur.execute(f"""SELECT Clients.id,
                                CONCAT_WS(' ', TRIM(name), TRIM(surname)), email, STRING_AGG(phone, ', ') AS phone
                                FROM Clients JOIN Phone ON Clients.id = Phone.id_client
                                WHERE {pole} = %s
                                GROUP BY Clients.id """, (info_,))

                info = cur.fetchall()
                print(f'Информация о введёном пользователе\n'
                      f'\tПолное имя: {info[0][1]}\n'
                      f'\tEmail: {info[0][2].strip()}\n'
                      f'\tТелефон: {info[0][3]}')

            try:
                search_client(*key)
            except:
                print('??? Информации о клиенте не нашлось')
        conn.close()



BD = ControlClientsDB('postgres', 'postgres', '1234')

BD.add_new_client('Valera', 'Ivanov')
BD.add_new_client('DON', 'Glebov')

BD.add_phone_client('+8-920-409-34-23', name='DON', surname='Glebov')
BD.add_phone_client('+8-920-409-34-23', id=1)
BD.add_phone_client('+8-000-000-34-23', id=1)
BD.add_phone_client('+8-920-409-34-23', name='Victor')
BD.add_phone_client('+000-920-409-34-23', id=1)

BD.update_data_client(2, 'Dmitry', 'Voronov', 'amdf@gmail.com', '+8-902-391-23-54')

BD.delete_info(1, '+8-000-000-34-23')

BD.search_info_client(phone='+8-920-409-34-23')
BD.search_info_client(name='Victor')