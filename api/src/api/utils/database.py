import abc
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, DecimalException
from typing import Any, Optional
from dotenv import load_dotenv
from psycopg import Connection, Cursor
from psycopg.types.composite import CompositeInfo, register_composite

from api.utils.environment import get_env_variable, get_secret

load_dotenv()


class DbConnection:
    def __init__(self):
        pass

    def __enter__(self):
        self.conn = Connection.connect(
            dbname=get_env_variable("DB_NAME"),
            user=get_env_variable("DB_USER"),
            password=get_secret("DB_PASSWORD"),
            host=get_env_variable("DB_HOST"),
        )
        self.cur = self.conn.cursor()
        return (self.conn, self.cur)

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.cur.close()
        self.conn.close()


def connect():
    return DbConnection()


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


def str_or_null_to_datetime(x: str | None, tz=None) -> datetime | None:
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
    cur: Cursor,
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
        cur.execute(statement.encode())


def register_type(conn: Connection, name: str, factory=None):
    info = CompositeInfo.fetch(conn, name)
    if info is not None:
        register_composite(info, conn, factory)
    else:
        raise RuntimeError(f"Could not find composite type {name}")
