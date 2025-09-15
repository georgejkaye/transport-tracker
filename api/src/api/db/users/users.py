from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.interactive import PickMultiple
from api.classes.users.users import User
from api.utils.interactive import input_checkbox


def insert_user(
    conn: Connection, user_name: str, display_name: str, hashed_password: str
) -> None:
    conn.execute(
        "SELECT insert_user(%s, %s, %s)",
        [user_name, display_name, hashed_password],
    )
    conn.commit()


def get_user(conn: Connection, user_name: str) -> Optional[User]:
    with conn.cursor(row_factory=class_row(User)) as cur:
        result = cur.execute(
            "SELECT * FROM select_user_by_username(%s)", [user_name]
        ).fetchone()
        if result is None:
            return None
        return result


def get_users(conn: Connection) -> list[User]:
    with conn.cursor(row_factory=class_row(User)) as cur:
        rows = cur.execute("SELECT * FROM select_users()").fetchall()
        return rows


def input_user(conn: Connection) -> Optional[list[User]]:
    users = get_users(conn)
    if len(users) == 0:
        print("No users found")
        return None
    user = input_checkbox(
        "Select user",
        users,
        display=lambda user: f"{user.user_name} ({user.display_name})",
    )
    match user:
        case PickMultiple(users):
            return users
        case _:
            return None
