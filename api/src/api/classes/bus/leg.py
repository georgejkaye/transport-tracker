from dataclasses import dataclass
from datetime import timedelta

from psycopg import Connection

from api.classes.bus.journey import (
    BusCallDetails,
    BusJourneyIn,
)
from api.classes.bus.operators import (
    BusOperatorDetails,
)
from api.classes.bus.vehicle import (
    BusVehicleDetails,
)
from api.utils.database import register_type


@dataclass
class BusLegIn:
    journey: BusJourneyIn
    board_stop_index: int
    alight_stop_index: int


@dataclass
class BusLegServiceDetails:
    id: int
    line: str
    operator: BusOperatorDetails
    outbound_description: str
    inbound_description: str
    bg_colour: str
    fg_colour: str


def register_bus_leg_service_details(conn: Connection) -> None:
    register_type(conn, "BusLegServiceDetails", BusLegServiceDetails)


@dataclass
class BusLegUserDetails:
    leg_id: int
    service: BusLegServiceDetails
    vehicle: BusVehicleDetails
    calls: list[BusCallDetails]
    duration: timedelta


def register_bus_leg_user_details(conn: Connection) -> None:
    register_type(conn, "BusLegUserDetails", BusLegUserDetails)
