from psycopg import Connection

from api.classes.interactive import PickMultiple
from api.db.functions.select.user import select_user_public_data_fetchall
from api.db.types.user.user import TransportUserPublicOutData
from api.utils.interactive import get_choices_from_input


def string_of_user_for_input_select(user: TransportUserPublicOutData) -> str:
    return f"{user.user_name} ({user.display_name})"


def input_users(conn: Connection) -> list[TransportUserPublicOutData]:
    users = select_user_public_data_fetchall(conn)
    input_choice = get_choices_from_input(
        "User", users, string_of_user_for_input_select
    )
    match input_choice:
        case PickMultiple(users):
            return users
        case _:
            return []
