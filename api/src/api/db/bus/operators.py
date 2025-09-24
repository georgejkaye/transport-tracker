from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.bus.operators import (
    BusOperatorDetails,
)


def get_bus_operators(conn: Connection) -> list[BusOperatorDetails]:
    rows = conn.execute("SELECT GetBusOperators()").fetchall()
    return [row[0] for row in rows]


def get_bus_operators_from_name(
    conn: Connection, search_string: str
) -> list[BusOperatorDetails]:
    with conn.cursor(row_factory=class_row(BusOperatorDetails)) as cur:
        rows = cur.execute(
            "SELECT GetBusOperatorsByName(%s)", [search_string]
        ).fetchall()
        conn.commit()
        return rows


def get_bus_operator_from_name(
    conn: Connection, search_string: str
) -> Optional[BusOperatorDetails]:
    operators = get_bus_operators_from_name(conn, search_string)
    if len(operators) != 1:
        return None
    return operators[0]


def get_bus_operator_from_national_operator_code(
    conn: Connection, search_string: str
) -> Optional[BusOperatorDetails]:
    with conn.cursor(row_factory=class_row(BusOperatorDetails)) as cur:
        rows = cur.execute(
            "SELECT * FROM GetBusOperatorsByNationalOperatorCode(%s)",
            [search_string],
        ).fetchone()
        conn.commit()
        return rows
