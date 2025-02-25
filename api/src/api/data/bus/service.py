from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from typing import Optional

from api.data.bus.operators import BusOperator, get_operator_from_name
from api.data.bus.stop import BusStop, BusStopDeparture
from api.utils.database import register_type
from api.utils.interactive import PickSingle, input_select
from api.utils.request import get_soup
from api.utils.times import get_local_timezone, make_timezone_aware
from bs4 import BeautifulSoup
from psycopg import Connection


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
    return f"{service.line} {service.outbound} ({service.operator.name})"


@dataclass
class BusCall:
    id: int
    stop: BusStop
    plan_arr: datetime
    plan_dep: datetime


@dataclass
class BusCallIn:
    atco: int
    plan_arr: Optional[datetime]
    plan_dep: Optional[datetime]


@dataclass
class BusJourney:
    id: int
    service: BusService
    calls: list[BusCall]


@dataclass
class BusJourneyIn:
    id: int
    service: BusService
    calls: list[BusCallIn]


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
) -> Optional[BusJourneyIn]:
    soup = get_bus_journey_page(bustimes_journey_id)
    if soup is None:
        return soup

    trip_script = soup.select_one("script#trip-data")
    if trip_script is None:
        return None

    trip_script_dict = json.loads(trip_script.text)
    service_operator = trip_script_dict["operator"]["name"]

    operator = get_operator_from_name(conn, service_operator)
    if operator is None:
        return None

    service_line = trip_script_dict["service"]["line_name"]
    bus_service = get_service_from_line_and_operator_name(
        conn, service_line, service_operator
    )
    if bus_service is None:
        return None

    service_calls = trip_script_dict["times"]
    is_after_ref = False
    first_call_datetime = None
    for call in service_calls:
        call_id = call["stop"]["atco_code"]
        if is_after_ref or call_id == ref_stop.atco:
            is_after_ref = True

        plan_arr_string = call["aimed_arrival_time"]
        if plan_arr_string is not None:
            plan_arr = datetime.strptime(plan_arr_string, "HH:mm")
        else:
            plan_arr = None
        plan_dep_string = call["aimed_departure_time"]
        if plan_dep_string is not None:
            plan_dep = datetime.strptime(plan_dep_string, "HH:mm")
        else:
            plan_dep = None
        call_object = BusCallIn(call_id, plan_arr, plan_dep)
        service_call_objects.append(call_object)

    return BusJourneyIn(bustimes_journey_id, bus_service, service_call_objects)


def register_bus_operator(
    bus_operator_id: int,
    bus_operator_name: str,
    bus_operator_code: str,
    bus_operator_national_code: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusOperator:
    return BusOperator(
        bus_operator_id,
        bus_operator_name,
        bus_operator_code,
        bus_operator_national_code,
        bg_colour or "#000000",
        fg_colour or "#ffffff",
    )


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
    selection = input_select(
        "Choose service", services, display=short_string_of_bus_service
    )
    match selection:
        case PickSingle(service):
            return service
        case _:
            return None


def get_service_from_line_and_operator_name(
    conn: Connection, service_line: str, service_operator: str
) -> Optional[BusService]:
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusServiceOutData", register_bus_service)
    rows = conn.execute(
        "SELECT * FROM GetBusServicesByOperatorName(%s, %s)",
        [service_operator, service_line],
    ).fetchall()
    if len(rows) == 0:
        return None
    services = [row[0] for row in rows]
    if len(services) > 1:
        return input_bus_service(services)
    else:
        return services[0]
