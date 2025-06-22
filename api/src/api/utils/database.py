import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from psycopg import Connection
from psycopg.rows import TupleRow
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
) -> DbConnectionData:
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

    def __enter__(self) -> Connection[TupleRow]:
        self.conn = Connection.connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
        )
        return self.conn

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.conn.close()


def connect(data: DbConnectionData) -> DbConnection:
    return DbConnection(data)


def connect_with_env() -> DbConnection:
    return DbConnection(DbConnectionData(None, None, None, None))


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


def register_type[T](conn: Connection, name: str, factory: type) -> None:
    info = CompositeInfo.fetch(conn, name)
    if info is not None:
        register_composite(info, conn, factory)
    else:
        raise RuntimeError(f"Could not find composite type {name}")
