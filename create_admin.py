from contextlib import closing
import os
import uuid

import psycopg2
from werkzeug.security import generate_password_hash


UUIDS = [uuid.uuid4(), uuid.uuid4()]
ADMIN_PASSWORD = generate_password_hash('admin')

NAME = 'welcome'
TEMPLATE = '''
Добро пожаловать в Praktix! 

Мы рады приветствовать вас в нашем онлайн кинотеатре!

Чтобы завершить регистрацию и начать наслаждаться нашей обширной коллекцией фильмов, пожалуйста, перейдите по ссылке ниже и подтвердите свой адрес электронной почты:

{{link}}


Если у вас есть какие-либо вопросы или вам нужна помощь, не стесняйтесь обращаться в нашу службу поддержки клиентов по адресу support@praktix.ru.

Нам не терпится познакомить вас со всем, что может предложить Praktix!

С уважением,
Команда Praktix
'''
VARIABLES = ['link']

DATA = [
    f"INSERT INTO roles (id, name) VALUES ('{UUIDS[0]}', 'admin') ON CONFLICT (id) DO NOTHING;",
    f"INSERT INTO roles (id, name) VALUES ('{uuid.uuid4()}', 'default') ON CONFLICT (id) DO NOTHING;",
    f"INSERT INTO users (id, email, password) VALUES ('{UUIDS[1]}', 'admin@test.com', '{ADMIN_PASSWORD}') ON CONFLICT (id) DO NOTHING;",
    f"INSERT INTO user_roles (id, user_id, role_id) VALUES ('{uuid.uuid4()}', '{UUIDS[1]}', '{UUIDS[0]}') ON CONFLICT (id) DO NOTHING;"
    f"INSERT INTO template.templates (id, name, text, variables, version) VALUES ('{uuid.uuid4()}', '{NAME}', '{TEMPLATE}', ARRAY {VARIABLES}, 1)"
]


def create_admin():
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),
    )
    with closing(conn) as pg_conn:
        with pg_conn:
            cur = pg_conn.cursor()
            try:
                for row in DATA:
                    cur.execute(row)
                    pg_conn.commit()
                print("Admin was added successfully")
            except psycopg2.Error as e:
                print(f"Error: {e}")
                conn.rollback()
            finally:
                cur.close()


if __name__ == '__main__':
    create_admin()
