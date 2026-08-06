from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from api.data.bus.operators import (
    BusOperatorDetails,
)
from api.data.bus.service import (
    BusJourneyServiceDetails,
    BusServiceDetails,
    register_bus_journey_service_details_types,
)
from api.data.bus.stop import (
    BusCallStopDetails,
    BusStopDetails,
    get_bus_stops_from_atcos,
    register_bus_call_stop_details_types,
)
from api.data.bus.vehicle import (
    BusVehicleDetails,
    register_bus_vehicle_details_types,
)
from api.utils.database import register_type
from api.utils.times import make_timezone_aware
from psycopg import Connection


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
class BusJourneyIn:
    operator: BusOperatorDetails
    service: BusServiceDetails
    calls: list[BusCallIn]
    vehicle: Optional[BusVehicleDetails]


def string_of_bus_journey_in(conn: Connection, bus_journey: BusJourneyIn) -> str:
    return_string = f"{bus_journey.service.line} {bus_journey.service.outbound.description} ({bus_journey.service.operator.name})\n============="
    atcos = [str(call.atco) for call in bus_journey.calls]
    atco_bus_stop_dict = get_bus_stops_from_atcos(conn, atcos)
    for call in bus_journey.calls:
        stop = atco_bus_stop_dict[str(call.atco)]
        call_string = f"{stop.locality} | {stop.common_name}"
        if call.plan_arr is not None:
            call_string = f"{call_string} arr {call.plan_arr.isoformat()}"
        if call.plan_dep is not None:
            call_string = f"{call_string} dep {call.plan_dep.isoformat()}"
        return_string = f"{return_string}\n{call_string}"
    return return_string


def get_call_datetime(
    datetime_string: str,
    run_date: datetime,
    first_call_run_date: Optional[datetime],
) -> datetime:
    time_object = datetime.strptime(datetime_string, "HH:mm")

    if (
        first_call_run_date is not None
        and time_object.time() < first_call_run_date.time()
    ):
        date_object = run_date + timedelta(days=1)
    else:
        date_object = run_date

    datetime_object = datetime.combine(date_object.date(), time_object.time())
    return make_timezone_aware(datetime_object)


@dataclass
class BusCall:
    id: int
    stop: BusStopDetails
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def register_bus_call(
    call_id: int,
    journey_id: int,
    call_index: int,
    call_stop: BusStopDetails,
    plan_arr: Optional[datetime],
    act_arr: Optional[datetime],
    plan_dep: Optional[datetime],
    act_dep: Optional[datetime],
) -> BusCall:
    return BusCall(call_id, call_stop, plan_arr, act_arr, plan_dep, act_dep)


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


def register_bus_journey_call_details_types(conn: Connection):
    register_bus_call_stop_details_types(conn)
    register_type(conn, "BusJourneyCallDetails", register_bus_journey_call_details)


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


def register_bus_journey_details_types(conn: Connection):
    register_bus_journey_service_details_types(conn)
    register_bus_journey_call_details_types(conn)
    register_bus_vehicle_details_types(conn)
    register_type(conn, "BusJourneyDetails", register_bus_journey_details)
