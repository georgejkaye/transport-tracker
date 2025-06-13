import sys

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, DecimalException
from typing import Any, Callable, Optional
from dotenv import load_dotenv
from psycopg import Connection
from psycopg.types.composite import CompositeInfo, register_composite

from api.utils.environment import get_env_variable, get_secret

load_dotenv()


@dataclass
class DbConnectionData:
    db_name: Optional[str]
    db_user: Optional[str]
    db_password: Optional[str]
    db_host: Optional[str]


def get_db_connection_data_from_args(
    db_name_index: int = 1,
    db_user_index: int = 2,
    db_password_index: int = 3,
    db_host_index: int = 4,
):
    if len(sys.argv) > max(
        db_name_index, db_user_index, db_password_index, db_host_index
    ):
        return DbConnectionData(
            sys.argv[db_name_index],
            sys.argv[db_user_index],
            sys.argv[db_password_index],
            sys.argv[db_host_index],
        )
    return DbConnectionData(None, None, None, None)


class DbConnection:
    def __init__(self, data: DbConnectionData):
        self.db_name = data.db_name or get_env_variable("DB_NAME")
        self.db_user = data.db_user or get_env_variable("DB_USER")
        self.db_password = data.db_password or get_secret("DB_PASSWORD")
        self.db_host = data.db_host or get_env_variable("DB_HOST")

    def __enter__(self):
        self.conn = Connection.connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
        )
        return self.conn

    def __exit__(self):
        self.conn.close()


def connect(data: DbConnectionData) -> DbConnection:
    return DbConnection(data)


def connect_with_env() -> DbConnection:
    return DbConnection(DbConnectionData(None, None, None, None))


@dataclass
class NoEscape:
    string: str


def int_or_none_to_str_or_none(x: Optional[int]) -> Optional[str]:
    if x is None:
        return None
    return str(x)


def optional_to_decimal(x: Optional[Any]) -> Optional[Decimal]:
    if x is None:
        return None
    try:
        dec = Decimal(str(x))
        return dec
    except DecimalException:
        return None


def str_or_none_to_str(x: str | None | NoEscape) -> str:
    if x is None or x == "":
        return "NULL"
    match x:
        case NoEscape(string):
            return string
        case _:
            pass
    replaced = x.replace("\u2019", "'")
    return f"$${replaced}$$"


def datetime_or_none_to_str(x: datetime | None) -> Optional[str]:
    if x is None:
        return None
    else:
        return x.isoformat()


def number_or_none_to_str(x: int | float | Decimal | None) -> Optional[str]:
    if x is None:
        return None
    else:
        return str(x)


def datetime_or_none_to_raw_str(x: datetime | None) -> str:
    if x is None:
        return "NULL"
    else:
        return f"'{x.isoformat()}'"


def str_or_null_to_datetime(
    x: str | None, tz: Optional[Any] = None
) -> datetime | None:
    if x is None:
        return None
    try:
        dt = datetime.fromisoformat(x)
        if tz:
            dt = dt.astimezone(tz)
        return dt
    except Exception:
        return None


def list_of_str_and_none_to_postgres_str(
    values: list[str | None | NoEscape],
) -> list[str]:
    return [str_or_none_to_str(value) for value in values]


def insert(
    conn: Connection,
    table: str,
    fields: list[str],
    values: list[list[str | None | NoEscape]],
    additional_query: str = "",
):
    partition_length = 500
    partitions = [
        values[i * partition_length : (i + 1) * partition_length]
        for i in range((len(values) + partition_length - 1) // partition_length)
    ]
    rows = ",".join(fields)
    for partition in partitions:
        value_strings = list(
            map(
                lambda x: f"({','.join(list_of_str_and_none_to_postgres_str(x))})",
                partition,
            )
        )
        statement: str = f"""
            INSERT into {table}({rows})
            VALUES {",".join(value_strings)}
            {additional_query}
        """
        conn.execute(statement.encode())


def register_type(
    conn: Connection, name: str, factory: Optional[Callable[..., Any]] = None
):
    info = CompositeInfo.fetch(conn, name)
    if info is not None:
        register_composite(info, conn, factory)
    else:
        raise RuntimeError(f"Could not find composite type {name}")
