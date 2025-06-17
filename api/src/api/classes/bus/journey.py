from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from psycopg import Connection

from api.classes.bus.operators import (
    BusOperatorDetails,
    register_bus_operator_details_types,
)
from api.classes.bus.service import BusServiceDetails
from api.classes.bus.vehicle import (
    BusVehicleDetails,
    register_bus_vehicle_details_types,
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


def register_bus_call_stop_details(
    bus_stop_id: int,
    stop_atco: str,
    stop_name: str,
    stop_locality: str,
    stop_street: Optional[str],
    stop_indicator: Optional[str],
) -> BusCallStopDetails:
    return BusCallStopDetails(
        bus_stop_id,
        stop_atco,
        stop_name,
        stop_locality,
        stop_street,
        stop_indicator,
    )


def register_bus_call_stop_details_types(conn: Connection) -> None:
    register_type(conn, "BusCallStopDetails", register_bus_call_stop_details)


@dataclass
class BusCallDetails:
    id: int
    call_index: int
    stop: BusCallStopDetails
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def register_bus_call_details(
    bus_call_id: int,
    call_index: int,
    bus_stop: BusCallStopDetails,
    plan_arr: Optional[datetime],
    act_arr: Optional[datetime],
    plan_dep: Optional[datetime],
    act_dep: Optional[datetime],
) -> BusCallDetails:
    return BusCallDetails(
        bus_call_id, call_index, bus_stop, plan_arr, act_arr, plan_dep, act_dep
    )


def register_bus_call_details_types(conn: Connection) -> None:
    register_bus_call_stop_details_types(conn)
    register_type(conn, "BusCallDetails", register_bus_call_details)


@dataclass
class BusJourneyCallDetails:
    id: int
    index: int
    stop: BusCallStopDetails
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def register_bus_journey_call_details(
    call_id: int,
    call_index: int,
    bus_stop: BusCallStopDetails,
    plan_arr: Optional[datetime],
    act_arr: Optional[datetime],
    plan_dep: Optional[datetime],
    act_dep: Optional[datetime],
) -> BusJourneyCallDetails:
    return BusJourneyCallDetails(
        call_id, call_index, bus_stop, plan_arr, act_arr, plan_dep, act_dep
    )


def register_bus_journey_call_details_types(conn: Connection) -> None:
    register_bus_call_stop_details_types(conn)
    register_type(conn, "BusJourneyCallDetails", register_bus_journey_call_details)


@dataclass
class BusJourneyServiceDetails:
    id: int
    operator: BusOperatorDetails
    line: str
    bg_colour: str
    fg_colour: str


def register_bus_journey_service_details(
    bus_service_id: int,
    bus_operator: BusOperatorDetails,
    service_line: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusJourneyServiceDetails:
    return BusJourneyServiceDetails(
        bus_service_id,
        bus_operator,
        service_line,
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def register_bus_journey_service_details_types(conn: Connection) -> None:
    register_bus_operator_details_types(conn)
    register_type(
        conn, "BusJourneyServiceDetails", register_bus_journey_service_details
    )


@dataclass
class BusJourneyDetails:
    id: int
    service: BusJourneyServiceDetails
    calls: list[BusJourneyCallDetails]
    vehicle: Optional[BusVehicleDetails]


def register_bus_journey_details(
    journey_id: int,
    journey_service: BusJourneyServiceDetails,
    journey_calls: list[BusJourneyCallDetails],
    journey_vehicle: Optional[BusVehicleDetails],
) -> BusJourneyDetails:
    return BusJourneyDetails(
        journey_id, journey_service, journey_calls, journey_vehicle
    )


def register_bus_journey_details_types(conn: Connection) -> None:
    register_bus_journey_service_details_types(conn)
    register_bus_journey_call_details_types(conn)
    register_bus_vehicle_details_types(conn)
    register_type(conn, "BusJourneyDetails", register_bus_journey_details)
