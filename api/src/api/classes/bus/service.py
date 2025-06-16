from dataclasses import dataclass
from typing import Optional

from api.classes.bus.operators import (
    BusOperatorDetails,
    register_bus_operator_details_types,
)
from api.utils.database import register_type
from psycopg import Connection


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


def register_bus_service_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_type(conn, "BusServiceDetails", register_bus_service_details)


def short_string_of_bus_service(service: BusServiceDetails) -> str:
    description = service.outbound.description
    if description == "":
        description = service.inbound.description
    return f"{service.line} {description} ({service.operator.name})"
