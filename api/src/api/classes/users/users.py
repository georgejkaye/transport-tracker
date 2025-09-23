from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    user_name: str
    display_name: str
    hashed_password: str


def register_user(
    user_id: int, user_name: str, display_name: str, hashed_password: str
) -> User:
    return User(user_id, user_name, display_name, hashed_password)


@dataclass
class UserPublic:
    user_id: int
    user_name: str
    display_name: str


def register_user_public(
    user_id: int, user_name: str, display_name: str
) -> UserPublic:
    return UserPublic(user_id, user_name, display_name)
