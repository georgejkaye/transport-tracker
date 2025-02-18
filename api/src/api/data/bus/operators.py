from dataclasses import dataclass
from typing import Optional

from api.utils.database import register_type
from psycopg import Connection


@dataclass
class BusOperator:
    id: int
    name: str
    code: str
    national_code: str
    bg_colour: Optional[str]
    fg_colour: Optional[str]


def register_bus_operator(
    id: int,
    name: str,
    code: str,
    national_code: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusOperator:
    return BusOperator(id, name, code, national_code, bg_colour, fg_colour)


def get_operators_from_name(
    conn: Connection, search_string: str
) -> list[BusOperator]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    rows = conn.execute("SELECT GetBusOperators(%s)", [search_string])
    return [row[0] for row in rows]


def get_operator_from_name(
    conn: Connection, search_string: str
) -> Optional[BusOperator]:
    operators = get_operators_from_name(conn, search_string)
    if len(operators) != 1:
        return None
    return operators[0]
