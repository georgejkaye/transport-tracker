from dataclasses import dataclass
from typing import Optional

from api.utils.database import register_type
from psycopg import Connection


@dataclass
class BusOperator:
    id: int
    name: str
    national_code: str
    bg_colour: Optional[str]
    fg_colour: Optional[str]


def register_bus_operator(
    id: int,
    name: str,
    national_code: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusOperator:
    return BusOperator(
        id, name, national_code, bg_colour or "#ffffff", fg_colour or "#000000"
    )


def get_bus_operators(conn: Connection) -> list[BusOperator]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    rows = conn.execute("SELECT GetBusOperators()").fetchall()
    return [row[0] for row in rows]


def get_bus_operators_from_name(
    conn: Connection, search_string: str
) -> list[BusOperator]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    rows = conn.execute(
        "SELECT GetBusOperatorsByName(%s)", [search_string]
    ).fetchall()
    return [row[0] for row in rows]


def get_bus_operator_from_name(
    conn: Connection, search_string: str
) -> Optional[BusOperator]:
    operators = get_bus_operators_from_name(conn, search_string)
    if len(operators) != 1:
        return None
    return operators[0]


def get_bus_operator_from_national_operator_code(
    conn: Connection, search_string: str
) -> Optional[BusOperator]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    rows = conn.execute(
        "SELECT GetBusOperatorsByNationalOperatorCode(%s)", [search_string]
    ).fetchall()
    if len(rows) != 1:
        return None
    return [row[0] for row in rows][0]
