import json
from datetime import datetime, timedelta
from typing import Any, Optional

from bs4 import BeautifulSoup
from psycopg import Connection

from api.classes.bus.journey import BusJourneyTimetable
from api.classes.bus.stop import BusStopDeparture, BusStopDetails
from api.db.functions.select.bus import (
    select_bus_operator_details_by_national_operator_code_fetchone,
    select_bus_service_details_by_operator_id_and_line_name_fetchone,
)
from api.db.types.bus import BusCallInData
from api.utils.request import get_soup
from api.utils.times import make_timezone_aware


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


def get_bus_call_datetime(
    after_board_call: bool,
    raw_call_datetime: datetime,
    board_departure_datetime: datetime,
) -> datetime:
    if not after_board_call:
        if raw_call_datetime.time() <= board_departure_datetime.time():
            bus_call_date = board_departure_datetime.date()
        else:
            bus_call_date = board_departure_datetime.date() - timedelta(days=1)
    else:
        if raw_call_datetime.time() <= board_departure_datetime.time():
            bus_call_date = board_departure_datetime.date() + timedelta(days=1)
        else:
            bus_call_date = board_departure_datetime.date()
    return datetime.combine(bus_call_date, raw_call_datetime.time())


def get_bus_journey_calls(
    service_calls: list[dict[str, Any]],
    board_stop: BusStopDetails,
    board_stop_departure: BusStopDeparture,
) -> tuple[Optional[int], list[BusCallInData]]:
    journey_calls: list[BusCallInData] = []
    after_board_call = False
    board_departure_datetime = board_stop_departure.dep_time
    board_call_index = None
    for i, call in enumerate(service_calls):
        stop_atco = call["stop"]["atco_code"]
        stop_name = call["stop"]["name"]
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
            plan_arr = get_bus_call_datetime(
                after_board_call, plan_arr, board_departure_datetime
            )
        if plan_dep is not None:
            plan_dep = get_bus_call_datetime(
                after_board_call, plan_dep, board_departure_datetime
            )
        journey_call = BusCallInData(
            i, stop_name, stop_atco, plan_arr, None, plan_dep, None
        )
        if stop_atco == board_stop.atco_code and not after_board_call:
            after_board_call = True
            board_call_index = i
        journey_calls.append(journey_call)
    return (board_call_index, journey_calls)


def get_bus_journey_and_board_call_index(
    conn: Connection,
    bustimes_journey_id: int,
    board_stop: BusStopDetails,
    board_stop_departure: BusStopDeparture,
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
    operator = select_bus_operator_details_by_national_operator_code_fetchone(
        conn, service_operator_noc
    )
    if operator is None:
        print("Could not get operator")
        return None
    service_line = trip_script_dict["service"]["line_name"]
    bus_service = (
        select_bus_service_details_by_operator_id_and_line_name_fetchone(
            conn, operator.bus_operator_id, service_line
        )
    )
    if bus_service is None:
        print("Could not get service")
        return None
    (board_call_index, journey_calls) = get_bus_journey_calls(
        trip_script_dict["times"], board_stop, board_stop_departure
    )
    if board_call_index is None:
        print("Could not get board call")
        return None
    journey = BusJourneyTimetable(
        bustimes_journey_id, operator, bus_service, journey_calls
    )
    return (journey, board_call_index)
