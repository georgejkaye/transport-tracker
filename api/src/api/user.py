from dataclasses import dataclass
from typing import Optional

from api.utils.database import register_type
from api.utils.interactive import PickSingle, input_select
from psycopg import Connection


@dataclass
class User:
    user_id: int
    user_name: str
    display_name: str
    hashed_password: str


def insert_user(
    conn: Connection, user_name: str, display_name: str, hashed_password: str
):
    conn.execute(
        "SELECT InsertUser(%s, %s, %s)",
        [user_name, display_name, hashed_password],
    )
    conn.commit()


def register_user(
    user_id: int, user_name: str, display_name: str, hashed_password: str
) -> User:
    return User(user_id, user_name, display_name, hashed_password)


def get_user(conn: Connection, user_name: str) -> Optional[User]:
    register_type(conn, "UserOutData", register_user)
    result = conn.execute(
        "SELECT GetUserByUsername(%s)", [user_name]
    ).fetchone()
    if result is None:
        return None
    return result[0]


def get_users(conn: Connection) -> list[User]:
    register_type(conn, "UserOutData", register_user)
    rows = conn.execute("SELECT GetUsers()").fetchall()
    return [row[0] for row in rows]


def input_user(conn: Connection) -> Optional[User]:
    users = get_users(conn)
    user = input_select(
        "Select user",
        users,
        display=lambda user: f"{user.user_name} ({user.display_name})",
    )
    match user:
        case PickSingle(user):
            return user
        case _:
            return None
