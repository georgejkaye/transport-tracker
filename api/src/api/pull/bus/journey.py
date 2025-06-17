import json
from datetime import datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup
from psycopg import Connection

from api.classes.bus.journey import BusCallIn, BusJourneyTimetable
from api.classes.bus.stop import BusStopDeparture, BusStopDetails
from api.db.bus.operators import get_bus_operator_from_national_operator_code
from api.db.bus.service import get_service_from_line_and_operator
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
