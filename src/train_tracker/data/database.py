from dotenv import load_dotenv
from psycopg2 import connect as db_connect
from psycopg2._psycopg import connection, cursor

from train_tracker.data.environment import get_env_variable, get_secret

load_dotenv()


def connect() -> tuple[connection, cursor]:
    conn = db_connect(
        dbname=get_env_variable("DB_NAME"),
        user=get_env_variable("DB_USER"),
        password=get_secret("DB_PASSWORD"),
        host=get_env_variable("DB_HOST"),
    )
    cur = conn.cursor()
    return (conn, cur)


def disconnect(conn, cur):
    conn.close()
    cur.close()


def str_or_none_to_str(x: str | None) -> str:
    if x is None or x == "":
        return "NULL"
    else:
        replaced = x.replace("\u2019", "'")
        return f"$${replaced}$$"


def list_of_str_and_none_to_postgres_str(values: list[str | None]) -> list[str]:
    return list(map(str_or_none_to_str, values))


def insert(
    cur: cursor,
    table: str,
    fields: list[str],
    values: list[list[str | None]],
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
        statement = f"""
            INSERT into {table}({rows})
            VALUES {",".join(value_strings)}
            {additional_query}
        """
        cur.execute(statement)
