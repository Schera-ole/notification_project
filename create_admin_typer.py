from contextlib import closing
import os
import uuid

import psycopg2
from werkzeug.security import generate_password_hash
import typer
from typing_extensions import Annotated


UUIDS = [uuid.uuid4(), uuid.uuid4()]
ADMIN_PASSWORD = generate_password_hash('admin')

VARIABLES = ['link']

DATA = [
    f"INSERT INTO roles (id, name) VALUES ('{UUIDS[0]}', 'admin') ON CONFLICT (id) DO NOTHING;",
    f"INSERT INTO roles (id, name) VALUES ('{uuid.uuid4()}', 'default') ON CONFLICT (id) DO NOTHING;",
    f"INSERT INTO users (id, email, password) VALUES ('{UUIDS[1]}', 'admin@test.com', '{ADMIN_PASSWORD}') ON CONFLICT (id) DO NOTHING;",
    f"INSERT INTO user_roles (id, user_id, role_id) VALUES ('{uuid.uuid4()}', '{UUIDS[1]}', '{UUIDS[0]}') ON CONFLICT (id) DO NOTHING;"
]


def create_admin(
        user: str,
        password: Annotated[str, typer.Option(prompt=True, confirmation_prompt=True, hide_input=True)]):
    conn = psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=user,
        password=password,
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
    typer.run(create_admin)
