from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from api.classes.bus.db.output import BusVehicleDetails
from api.classes.bus.operators import BusOperatorDetails
from api.classes.bus.service import BusServiceDetails


@dataclass
class BusCallIn:
    index: int
    atco: str
    stop_name: str
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def string_of_bus_call_in(bus_call: BusCallIn) -> str:
    if bus_call.plan_arr is not None:
        time_string = f" arr {bus_call.plan_arr.strftime("%H:%M")}"
    else:
        time_string = ""
    if bus_call.plan_dep is not None:
        time_string = f"{time_string} dep {bus_call.plan_dep.strftime("%H:%M")}"
    return f"{bus_call.stop_name}{time_string}"


@dataclass
class BusJourneyTimetable:
    id: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    calls: list[BusCallIn]


@dataclass
class BusJourneyIn:
    id: int
    operator: BusOperatorDetails
    service: BusServiceDetails
    calls: list[BusCallIn]
    vehicle: Optional[BusVehicleDetails]
