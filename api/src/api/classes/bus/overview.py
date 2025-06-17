from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from psycopg import Connection

from api.classes.bus.journey import (
    BusCallDetails,
    register_bus_call_details_types,
)
from api.classes.bus.leg import (
    BusLegServiceDetails,
    register_bus_leg_service_details_types,
)
from api.classes.bus.operators import (
    BusOperatorDetails,
    register_bus_operator_details_types,
)
from api.utils.database import register_type


@dataclass
class BusVehicleLegDetails:
    id: int
    service: BusLegServiceDetails
    board: BusCallDetails
    alight: BusCallDetails
    duration: timedelta


def register_bus_vehicle_leg_details(
    leg_id: int,
    bus_service: BusLegServiceDetails,
    board_call: BusCallDetails,
    alight_call: BusCallDetails,
    leg_duration: timedelta,
) -> BusVehicleLegDetails:
    return BusVehicleLegDetails(
        leg_id, bus_service, board_call, alight_call, leg_duration
    )


def register_bus_vehicle_leg_details_types(conn: Connection) -> None:
    register_bus_leg_service_details_types(conn)
    register_bus_call_details_types(conn)
    register_type(
        conn, "BusVehicleLegDetails", register_bus_vehicle_leg_details
    )


@dataclass
class BusVehicleUserDetails:
    id: int
    number: str
    name: Optional[str]
    numberplate: str
    operator: BusOperatorDetails
    legs: list[BusVehicleLegDetails]
    duration: timedelta


def register_bus_vehicle_user_details(
    vehicle_id: int,
    vehicle_number: str,
    vehicle_name: Optional[str],
    vehicle_numberplate: str,
    vehicle_operator: BusOperatorDetails,
    vehicle_legs: list[BusVehicleLegDetails],
    vehicle_duration: timedelta,
) -> BusVehicleUserDetails:
    return BusVehicleUserDetails(
        vehicle_id,
        vehicle_number,
        vehicle_name,
        vehicle_numberplate,
        vehicle_operator,
        vehicle_legs,
        vehicle_duration,
    )


def register_bus_vehicle_user_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_bus_vehicle_leg_details_types(conn)
    register_type(
        conn, "BusVehicleUserDetails", register_bus_vehicle_user_details
    )
