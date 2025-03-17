from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from psycopg import Connection

from api.data.bus.operators import (
    BusOperator,
    register_bus_operator,
)
from api.data.bus.stop import BusStop
from api.utils.database import register_type
from api.utils.interactive import (
    PickSingle,
    input_select_paginate,
)


@dataclass
class BusServiceDescription:
    description: str
    vias: list[str]


@dataclass
class BusService:
    id: int
    operator: BusOperator
    line: str
    outbound: BusServiceDescription
    inbound: BusServiceDescription
    bg_colour: Optional[str]
    fg_colour: Optional[str]


def short_string_of_bus_service(service: BusService) -> str:
    return f"{service.line} {service.outbound.description} ({service.operator.name})"


def register_bus_service(
    bus_service_id: int,
    bus_operator: BusOperator,
    service_line: str,
    service_description_outbound: str,
    service_outbound_vias: list[str],
    service_description_inbound: str,
    service_inbound_vias: list[str],
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusService:
    return BusService(
        bus_service_id,
        bus_operator,
        service_line,
        BusServiceDescription(
            service_description_outbound, service_outbound_vias
        ),
        BusServiceDescription(
            service_description_inbound, service_inbound_vias
        ),
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def input_bus_service(services: list[BusService]) -> Optional[BusService]:
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
) -> Optional[BusService]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusServiceOutData", register_bus_service)
    rows = conn.execute(
        "SELECT GetBusServicesByNationalOperatorCode(%s, %s)",
        [service_operator, service_line],
    ).fetchall()
    if len(rows) == 0:
        return None
    services = [row[0] for row in rows]
    if len(services) > 1:
        return input_bus_service(services)
    else:
        return services[0]


def get_service_from_line_and_operator(
    conn: Connection, service_line: str, service_operator: BusOperator
) -> Optional[BusService]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusServiceOutData", register_bus_service)
    rows = conn.execute(
        "SELECT GetBusServicesByOperatorId(%s, %s)",
        [service_operator.id, service_line],
    ).fetchall()
    if len(rows) == 0:
        return None
    services = [row[0] for row in rows]
    if len(services) > 1:
        return input_bus_service(services)
    else:
        return services[0]


def get_service_from_line_and_operator_name(
    conn: Connection, service_line: str, service_operator: str
) -> Optional[BusService]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusServiceOutData", register_bus_service)
    rows = conn.execute(
        "SELECT GetBusServicesByOperatorName(%s, %s)",
        [service_operator, service_line],
    ).fetchall()
    if len(rows) == 0:
        return None
    services = [row[0] for row in rows]
    if len(services) > 1:
        return input_bus_service(services)
    else:
        return services[0]
