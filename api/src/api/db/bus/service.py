from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.bus.operators import BusOperatorDetails
from api.classes.bus.service import (
    BusServiceDetails,
    register_bus_service_details_types,
    short_string_of_bus_service,
)
from api.utils.interactive import (
    PickSingle,
    input_select_paginate,
)


def input_bus_service(
    services: list[BusServiceDetails],
) -> Optional[BusServiceDetails]:
    selection = input_select_paginate(
        "Choose service", services, display=short_string_of_bus_service
    )
    match selection:
        case PickSingle(service):
            return service
        case _:
            return None


def get_service_from_line_and_operator_national_code(
    conn: Connection, service_line: str, service_operator: str
) -> Optional[BusServiceDetails]:
    with conn.cursor(row_factory=class_row(BusServiceDetails)) as cur:
        rows = cur.execute(
            "SELECT GetBusServicesByNationalOperatorCode(%s, %s)",
            [service_operator, service_line],
        ).fetchall()
        if len(rows) == 0:
            return None
        if len(rows) > 1:
            return input_bus_service(rows)
        else:
            return rows[0]


def get_service_from_line_and_operator(
    conn: Connection, service_line: str, service_operator: BusOperatorDetails
) -> Optional[BusServiceDetails]:
    register_bus_service_details_types(conn)
    with conn.cursor(row_factory=class_row(BusServiceDetails)) as cur:
        rows = cur.execute(
            "SELECT GetBusServicesByOperatorId(%s, %s)",
            [service_operator.id, service_line],
        ).fetchall()
        if len(rows) == 0:
            return None
        if len(rows) > 1:
            return input_bus_service(rows)
        else:
            return rows[0]


def get_service_from_line_and_operator_name(
    conn: Connection, service_line: str, service_operator: str
) -> Optional[BusServiceDetails]:
    register_bus_service_details_types(conn)
    with conn.cursor(row_factory=class_row(BusServiceDetails)) as cur:
        rows = cur.execute(
            "SELECT GetBusServicesByOperatorName(%s, %s)",
            [service_operator, service_line],
        ).fetchall()
        if len(rows) == 0:
            return None
        if len(rows) > 1:
            return input_bus_service(rows)
        else:
            return rows[0]
