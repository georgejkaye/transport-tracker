from dataclasses import dataclass
from datetime import timedelta
from api.classes.bus.vehicle import (
    BusVehicleDetails,
    register_bus_vehicle_details_types,
)
from psycopg import Connection
from typing import Optional

from api.classes.bus.journey import (
    BusCallDetails,
    BusJourneyIn,
    register_bus_call_details_types,
)
from api.classes.bus.operators import (
    BusOperatorDetails,
    register_bus_operator_details_types,
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


def register_bus_leg_service_details(
    service_id: int,
    service_line: str,
    bus_operator: BusOperatorDetails,
    outbound_description: str,
    inbound_description: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusLegServiceDetails:
    return BusLegServiceDetails(
        service_id,
        service_line,
        bus_operator,
        outbound_description,
        inbound_description,
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def register_bus_leg_service_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_type(
        conn, "BusLegServiceDetails", register_bus_leg_service_details
    )


@dataclass
class BusLegUserDetails:
    id: int
    service: BusLegServiceDetails
    vehicle: BusVehicleDetails
    calls: list[BusCallDetails]
    duration: timedelta


def register_bus_leg_user_details(
    leg_id: int,
    bus_service: BusLegServiceDetails,
    bus_vehicle: BusVehicleDetails,
    calls: list[BusCallDetails],
    duration: timedelta,
) -> BusLegUserDetails:
    return BusLegUserDetails(leg_id, bus_service, bus_vehicle, calls, duration)


def register_bus_leg_user_details_types(conn: Connection) -> None:
    register_bus_leg_service_details_types(conn)
    register_bus_call_details_types(conn)
    register_type(conn, "BusLegUserDetails", register_bus_leg_user_details)


def register_leg_types(conn: Connection) -> None:
    register_bus_leg_service_details_types(conn)
    register_bus_vehicle_details_types(conn)
    register_bus_call_details_types(conn)
    register_type(conn, "BusLegUserDetails", register_bus_leg_user_details)
