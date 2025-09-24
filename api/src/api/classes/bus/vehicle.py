from dataclasses import dataclass
from typing import Optional

from psycopg import Connection

from api.classes.bus.operators import (
    BusOperatorDetails,
)
from api.utils.database import register_type


@dataclass
class BusVehicleIn:
    operator_id: int
    vehicle_number: str
    bustimes_id: str
    numberplate: str
    model: Optional[str]
    livery_style: Optional[str]
    name: Optional[str]


def string_of_bus_vehicle_in(bus_vehicle: BusVehicleIn) -> str:
    string_brackets = f"({bus_vehicle.numberplate}"
    if bus_vehicle.name is not None:
        string_brackets = f"{string_brackets}/{bus_vehicle.name}"
    string_brackets = f"{string_brackets})"
    return (
        f"{bus_vehicle.vehicle_number} {string_brackets} - {bus_vehicle.model}"
    )


################################################################################
# DB input types                                                               #
################################################################################

DbBusModelInData = tuple[Optional[str]]


DbBusVehicleInData = tuple[
    int, str, str, str, Optional[str], Optional[str], Optional[str]
]


################################################################################
# DB output types                                                              #
################################################################################


@dataclass
class BusVehicleDetails:
    id: int
    operator: BusOperatorDetails
    vehicle_number: str
    bustimes_id: str
    numberplate: str
    model: Optional[str]
    livery_style: Optional[str]
    name: Optional[str]


def register_bus_vehicle_details(conn: Connection) -> None:
    register_type(conn, "BusVehicleDetails", BusVehicleDetails)
