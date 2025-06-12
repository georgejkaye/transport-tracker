from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from psycopg import Connection

from api.db.bus.operators import (
    BusOperatorDetails,
    register_bus_operator_details,
    register_bus_operator_details_types,
)
from api.db.bus.stop import BusStopDetails
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
class BusServiceDetails:
    id: int
    operator: BusOperatorDetails
    line: str
    outbound: BusServiceDescription
    inbound: BusServiceDescription
    bg_colour: Optional[str]
    fg_colour: Optional[str]


def register_bus_service_details(
    bus_service_id: int,
    bus_operator: BusOperatorDetails,
    service_line: str,
    description_outbound: str,
    service_outbound_vias: list[str],
    description_inbound: str,
    service_inbound_vias: list[str],
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusServiceDetails:
    return BusServiceDetails(
        bus_service_id,
        bus_operator,
        service_line,
        BusServiceDescription(description_outbound, service_outbound_vias),
        BusServiceDescription(description_inbound, service_inbound_vias),
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def register_bus_service_details_types(conn: Connection):
    register_bus_operator_details_types(conn)
    register_type(conn, "BusServiceDetails", register_bus_service_details)


def short_string_of_bus_service(service: BusServiceDetails) -> str:
    description = service.outbound.description
    if description is None:
        description = service.inbound.description
    return f"{service.line} {description} ({service.operator.name})"


@dataclass
class BusJourneyServiceDetails:
    id: int
    operator: BusOperatorDetails
    line: str
    bg_colour: str
    fg_colour: str


def register_bus_journey_service_details(
    bus_service_id: int,
    bus_operator: BusOperatorDetails,
    service_line: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusJourneyServiceDetails:
    return BusJourneyServiceDetails(
        bus_service_id,
        bus_operator,
        service_line,
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def register_bus_journey_service_details_types(conn: Connection):
    register_bus_operator_details_types(conn)
    register_type(
        conn, "BusJourneyServiceDetails", register_bus_journey_service_details
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
    conn: Connection, service_line: str, service_operator: BusOperatorDetails
) -> Optional[BusServiceDetails]:
    register_bus_service_details_types(conn)
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
) -> Optional[BusServiceDetails]:
    register_bus_service_details_types(conn)
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
