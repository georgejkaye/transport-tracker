from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.interactive import PickMultiple
from api.classes.user import User, register_user
from api.utils.database import register_type
from api.utils.interactive import (
    input_checkbox,
)


def insert_user(
    conn: Connection, user_name: str, display_name: str, hashed_password: str
) -> None:
    conn.execute(
        "SELECT InsertUser(%s, %s, %s)",
        [user_name, display_name, hashed_password],
    )
    conn.commit()


def get_user(conn: Connection, user_name: str) -> Optional[User]:
    register_type(conn, "UserOutData", register_user)
    with conn.cursor(row_factory=class_row(User)) as cur:
        result = cur.execute(
            "SELECT GetUserByUsername(%s)", [user_name]
        ).fetchone()
        if result is None:
            return None
        return result


def get_users(conn: Connection) -> list[User]:
    register_type(conn, "UserOutData", register_user)
    rows = conn.execute("SELECT GetUsers()").fetchall()
    return [row[0] for row in rows]


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
