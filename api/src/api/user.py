from dataclasses import dataclass
from typing import Optional

from api.utils.database import register_type
from api.utils.interactive import (
    PickMultiple,
    input_checkbox,
)
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


@dataclass
class UserPublic:
    id: int
    user_name: str
    display_name: str


def register_user_public(
    user_id: int, user_name: str, display_name: str
) -> UserPublic:
    return UserPublic(user_id, user_name, display_name)
