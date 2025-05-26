from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from typing import Optional

from api.data.bus.operators import (
    BusOperator,
    get_bus_operator_from_national_operator_code,
)
from api.data.bus.overview import BusCallStopDetails
from api.data.bus.service import (
    BusJourneyService,
    BusServiceDetails,
    get_service_from_line_and_operator,
)
from api.data.bus.stop import (
    BusStopDetails,
    BusStopDeparture,
    get_bus_stops_from_atcos,
)
from api.data.bus.vehicle import BusVehicleDetails
from api.utils.request import get_soup
from api.utils.times import make_timezone_aware
from bs4 import BeautifulSoup
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
        time_string = f" arr {bus_call.plan_arr.strftime("%H:%M")}"
    else:
        time_string = ""
    if bus_call.plan_dep is not None:
        time_string = f"{time_string} dep {bus_call.plan_dep.strftime("%H:%M")}"
    return f"{bus_call.stop_name}{time_string}"


@dataclass
class BusJourneyTimetable:
    id: int
    operator: BusOperator
    service: BusServiceDetails
    calls: list[BusCallIn]


@dataclass
class BusJourneyIn:
    id: int
    operator: BusOperator
    service: BusServiceDetails
    calls: list[BusCallIn]
    vehicle: Optional[BusVehicleDetails]


def string_of_bus_journey_in(
    conn: Connection, bus_journey: BusJourneyIn
) -> str:
    return_string = f"{bus_journey.id}: {bus_journey.service.line} {bus_journey.service.outbound.description} ({bus_journey.service.operator.name})\n============="
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


def get_bus_journey_url(bustimes_journey_id: int) -> str:
    return f"https://bustimes.org/trips/{bustimes_journey_id}"


def get_bus_journey_page(bustimes_journey_id: int) -> Optional[BeautifulSoup]:
    url = get_bus_journey_url(bustimes_journey_id)
    return get_soup(url)


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


def get_bus_journey(
    conn: Connection,
    bustimes_journey_id: int,
    ref_stop: BusStopDetails,
    ref_departure: BusStopDeparture,
) -> Optional[tuple[BusJourneyTimetable, int]]:
    soup = get_bus_journey_page(bustimes_journey_id)
    if soup is None:
        print("Could not get journey page")
        return soup

    trip_script = soup.select_one("script#trip-data")
    if trip_script is None:
        print("Could not get trip script")
        return None

    trip_script_dict = json.loads(trip_script.text)
    service_operator_noc = trip_script_dict["operator"]["noc"]

    operator = get_bus_operator_from_national_operator_code(
        conn, service_operator_noc
    )
    if operator is None:
        print("Could not get operator")
        return None

    service_line = trip_script_dict["service"]["line_name"]
    bus_service = get_service_from_line_and_operator(
        conn, service_line, operator
    )

    if bus_service is None:
        print("Could not get service")
        return None

    service_calls = trip_script_dict["times"]
    is_after_ref = False
    first_call_datetime = None
    service_call_objects: list[BusCallIn] = []

    ref_departure_time = ref_departure.dep_time
    board_call_index = None

    for i, call in enumerate(service_calls):
        call_id = call["stop"]["atco_code"]
        call_name = call["stop"]["name"]

        plan_arr_string = call["aimed_arrival_time"]
        if plan_arr_string is not None:
            plan_arr = datetime.strptime(plan_arr_string, "%H:%M")
        else:
            plan_arr = None
        plan_dep_string = call["aimed_departure_time"]
        if plan_dep_string is not None:
            plan_dep = datetime.strptime(plan_dep_string, "%H:%M")
        else:
            plan_dep = None

        if plan_arr is not None:
            if not is_after_ref:
                if plan_arr.time() <= ref_departure_time.time():
                    plan_arr_date = ref_departure_time.date()
                else:
                    plan_arr_date = ref_departure_time.date() - timedelta(
                        days=1
                    )
            else:
                if plan_arr.time() <= ref_departure_time.time():
                    plan_arr_date = ref_departure_time.date() + timedelta(
                        days=1
                    )
                else:
                    plan_arr_date = ref_departure_time.date()
            plan_arr = datetime.combine(plan_arr_date, plan_arr.time())

        if plan_dep is not None:
            if not is_after_ref:
                if plan_dep.time() <= ref_departure_time.time():
                    plan_dep_date = ref_departure_time.date()
                else:
                    plan_dep_date = ref_departure_time.date() - timedelta(
                        days=1
                    )
            else:
                if plan_dep.time() <= ref_departure_time.time():
                    plan_dep_date = ref_departure_time.date() + timedelta(
                        days=1
                    )
                else:
                    plan_dep_date = ref_departure_time.date()
            plan_dep = datetime.combine(plan_dep_date, plan_dep.time())
        call_object = BusCallIn(
            i, call_id, call_name, plan_arr, None, plan_dep, None
        )

        if call_id == ref_stop.atco and not is_after_ref:
            is_after_ref = True
            board_call_index = i
        service_call_objects.append(call_object)
    if board_call_index is None:
        print("Could not get board call")
        return None
    journey = BusJourneyTimetable(
        bustimes_journey_id, operator, bus_service, service_call_objects
    )
    return (journey, board_call_index)


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


@dataclass
class BusJourneyDetails:
    id: int
    service: BusJourneyService
    calls: list[BusJourneyCallDetails]
    vehicle: Optional[BusVehicleDetails]


def register_bus_journey_details(
    journey_id: int,
    journey_service: BusJourneyService,
    journey_calls: list[BusJourneyCallDetails],
    journey_vehicle: Optional[BusVehicleDetails],
) -> BusJourneyDetails:
    return BusJourneyDetails(
        journey_id, journey_service, journey_calls, journey_vehicle
    )
