from dataclasses import dataclass
from typing import Optional


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
