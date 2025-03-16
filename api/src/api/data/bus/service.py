import json

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
from psycopg import Connection

from api.data.bus.operators import (
    BusOperator,
    get_bus_operator_from_national_operator_code,
    register_bus_operator,
)
from api.data.bus.stop import (
    BusStop,
    BusStopDeparture,
    get_bus_stops_from_atcos,
)
from api.utils.database import register_type
from api.utils.interactive import (
    PickSingle,
    input_select_paginate,
)
from api.utils.request import get_soup
from api.utils.times import make_timezone_aware


@dataclass
class BusServiceDescription:
    description: str
    vias: list[str]


@dataclass
class BusService:
    id: int
    operator: BusOperator
    line: str
    outbound: BusServiceDescription
    inbound: BusServiceDescription
    bg_colour: Optional[str]
    fg_colour: Optional[str]


def short_string_of_bus_service(service: BusService) -> str:
    return f"{service.line} {service.outbound.description} ({service.operator.name})"


@dataclass
class BusCall:
    id: int
    stop: BusStop
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


@dataclass
class BusCallIn:
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
class BusJourney:
    id: int
    service: BusService
    calls: list[BusCall]


@dataclass
class BusJourneyIn:
    id: int
    operator: BusOperator
    service: BusService
    calls: list[BusCallIn]


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


@dataclass
class BusLeg:
    id: int
    journey: BusJourney
    calls: list[BusCall]


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
    ref_stop: BusStop,
    ref_departure: BusStopDeparture,
) -> Optional[tuple[BusJourneyIn, int]]:
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
            call_id, call_name, plan_arr, None, plan_dep, None
        )

        if call_id == ref_stop.atco and not is_after_ref:
            is_after_ref = True
            board_call_index = i
        service_call_objects.append(call_object)
    if board_call_index is None:
        print("Could not get board call")
        return None
    journey = BusJourneyIn(
        bustimes_journey_id, operator, bus_service, service_call_objects
    )
    return (journey, board_call_index)


def register_bus_service(
    bus_service_id: int,
    bus_operator: BusOperator,
    service_line: str,
    service_description_outbound: str,
    service_outbound_vias: list[str],
    service_description_inbound: str,
    service_inbound_vias: list[str],
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusService:
    return BusService(
        bus_service_id,
        bus_operator,
        service_line,
        BusServiceDescription(
            service_description_outbound, service_outbound_vias
        ),
        BusServiceDescription(
            service_description_inbound, service_inbound_vias
        ),
        bg_colour or "#ffffff",
        fg_colour or "#000000",
    )


def input_bus_service(services: list[BusService]) -> Optional[BusService]:
    selection = input_select_paginate(
        "Choose service", services, display=short_string_of_bus_service
    )
    match selection:
        case PickSingle(service):
            return service
        case _:
            return None


def get_service_from_line_and_operator_national_code(
    conn: Connection, service_line: str, service_operator: str
) -> Optional[BusService]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusServiceOutData", register_bus_service)
    rows = conn.execute(
        "SELECT GetBusServicesByNationalOperatorCode(%s, %s)",
        [service_operator, service_line],
    ).fetchall()
    if len(rows) == 0:
        return None
    services = [row[0] for row in rows]
    if len(services) > 1:
        return input_bus_service(services)
    else:
        return services[0]


def get_service_from_line_and_operator(
    conn: Connection, service_line: str, service_operator: BusOperator
) -> Optional[BusService]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusServiceOutData", register_bus_service)
    rows = conn.execute(
        "SELECT GetBusServicesByOperatorId(%s, %s)",
        [service_operator.id, service_line],
    ).fetchall()
    if len(rows) == 0:
        return None
    services = [row[0] for row in rows]
    if len(services) > 1:
        return input_bus_service(services)
    else:
        return services[0]


def get_service_from_line_and_operator_name(
    conn: Connection, service_line: str, service_operator: str
) -> Optional[BusService]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusServiceOutData", register_bus_service)
    rows = conn.execute(
        "SELECT GetBusServicesByOperatorName(%s, %s)",
        [service_operator, service_line],
    ).fetchall()
    if len(rows) == 0:
        return None
    services = [row[0] for row in rows]
    if len(services) > 1:
        return input_bus_service(services)
    else:
        return services[0]
