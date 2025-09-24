from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from psycopg import Connection

from api.classes.bus.operators import (
    BusOperatorDetails,
)
from api.classes.bus.service import BusServiceDetails
from api.classes.bus.vehicle import (
    BusVehicleDetails,
)
from api.utils.database import register_type


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
        time_string = f" arr {bus_call.plan_arr.strftime('%H:%M')}"
    else:
        time_string = ""
    if bus_call.plan_dep is not None:
        time_string = f"{time_string} dep {bus_call.plan_dep.strftime('%H:%M')}"
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


################################################################################
# DB input types                                                               #
################################################################################

DbBusCallInData = tuple[
    int,
    str,
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
]


################################################################################
# DB output types                                                              #
################################################################################


@dataclass
class BusCallStopDetails:
    id: int
    atco: str
    name: str
    locality: str
    street: Optional[str]
    indicator: Optional[str]


def register_bus_call_stop_details(conn: Connection) -> None:
    register_type(conn, "BusCallStopDetails", BusCallStopDetails)


@dataclass
class BusCallDetails:
    id: int
    call_index: int
    stop: BusCallStopDetails
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def register_bus_call_details(conn: Connection) -> None:
    register_type(conn, "BusCallDetails", BusCallDetails)


@dataclass
class BusJourneyCallDetails:
    id: int
    index: int
    stop: BusCallStopDetails
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def register_bus_journey_call_details(conn: Connection) -> None:
    register_type(conn, "BusJourneyCallDetails", BusJourneyCallDetails)


@dataclass
class BusJourneyServiceDetails:
    id: int
    operator: BusOperatorDetails
    line: str
    bg_colour: str
    fg_colour: str


def register_bus_journey_service_details(conn: Connection) -> None:
    register_type(conn, "BusJourneyServiceDetails", BusJourneyServiceDetails)


@dataclass
class BusJourneyDetails:
    id: int
    service: BusJourneyServiceDetails
    calls: list[BusJourneyCallDetails]
    vehicle: Optional[BusVehicleDetails]


def register_bus_journey_details(conn: Connection) -> None:
    register_type(conn, "BusJourneyDetails", BusJourneyDetails)
