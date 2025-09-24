from dataclasses import dataclass
from typing import Optional

from psycopg import Connection

from api.classes.bus.operators import (
    BusOperatorDetails,
)
from api.utils.database import register_type


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


def register_bus_service_details(conn: Connection) -> None:
    register_type(conn, "BusServiceDetails", BusServiceDetails)


def short_string_of_bus_service(service: BusServiceDetails) -> str:
    description = service.outbound.description
    if description == "":
        description = service.inbound.description
    return f"{service.line} {description} ({service.operator.name})"
