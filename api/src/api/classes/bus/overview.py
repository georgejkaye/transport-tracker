from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from psycopg import Connection

from api.classes.bus.journey import (
    BusCallDetails,
)
from api.classes.bus.leg import (
    BusLegServiceDetails,
)
from api.classes.bus.operators import (
    BusOperatorDetails,
)
from api.utils.database import register_type


@dataclass
class BusVehicleLegDetails:
    id: int
    service: BusLegServiceDetails
    board: BusCallDetails
    alight: BusCallDetails
    duration: timedelta


def register_bus_vehicle_leg_details(conn: Connection) -> None:
    register_type(conn, "BusVehicleLegDetails", BusVehicleLegDetails)


@dataclass
class BusVehicleUserDetails:
    vehicle_id: int
    identifier: str
    name: Optional[str]
    numberplate: str
    operator: BusOperatorDetails
    legs: list[BusVehicleLegDetails]
    duration: timedelta


def register_bus_vehicle_user_details(conn: Connection) -> None:
    register_type(conn, "BusVehicleUserDetails", BusVehicleUserDetails)
