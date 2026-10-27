from datetime import datetime, timedelta
from typing import Optional

from psycopg import Connection

from api.classes.bus.journey import string_of_bus_call_in
from api.classes.bus.stop import short_string_of_bus_stop_details
from api.classes.interactive import PickSingle
from api.db.functions.insert.bus.leg import insert_bus_leg_fetchone
from api.db.functions.select.bus.operator import (
    select_bus_operator_details_by_national_operator_code_fetchone,
)
from api.db.functions.select.bus.service import (
    select_bus_service_details_by_operator_id_and_line_name_fetchone,
)
from api.db.functions.select.bus.stop import (
    select_bus_stop_details_by_name_fetchall,
)
from api.db.functions.select.bus.vehicle import (
    select_bus_vehicle_details_fetchall,
)
from api.db.types.bus.journey import (
    BusCallInData,
    BusJourneyInData,
)
from api.db.types.bus.leg import BusLegInData
from api.db.types.bus.operator import BusOperatorDetails
from api.db.types.bus.stop import BusStopDetails
from api.db.types.bus.vehicle import BusVehicleDetails
from api.db.types.register import register_types
from api.db.types.user.user import TransportUserPublicOutData
from api.pull.bus.pages.bustimes import accept_bustimes_cookies
from api.pull.bus.pages.journey.classes import BustimesJourney
from api.pull.bus.pages.journey.reader import get_bustimes_journey
from api.pull.bus.pages.operator.reader import get_bustimes_operator
from api.pull.bus.pages.stop.classes import BusStopDeparture
from api.pull.bus.pages.stop.reader import (
    get_departures_from_bus_stop,
    short_string_of_bus_stop_departure,
)
from api.pull.bus.pages.trip.reader import get_bus_trip
from api.pull.selenium.driver import Driver, DriverManager
from api.record.classes import BustimesJourneyData
from api.record.user import get_users_from_input
from api.utils.database import connect_with_env
from api.utils.interactive import (
    get_choice_from_input_paginate,
    get_day_from_input,
    get_month_from_input,
    get_text_from_input,
    get_time_from_input,
    get_year_from_input,
    print_error,
    print_information,
)


def get_bustimes_url() -> str:
    return "https://bustimes.org"


def get_bus_stop_from_input(
    conn: Connection, prompt: str = "Bus stop name"
) -> Optional[BusStopDetails]:
    search_string = get_text_from_input("Bus stop name")
    if search_string is None:
        return None
    bus_stops = select_bus_stop_details_by_name_fetchall(conn, search_string)
    bus_stop_choice = get_choice_from_input_paginate(
        "Select bus stop", bus_stops, display=short_string_of_bus_stop_details
    )
    match bus_stop_choice:
        case PickSingle(bus_stop):
            return bus_stop
        case _:
            return None


def get_bus_stop_departure_from_input(
    departures: list[BusStopDeparture],
) -> Optional[BusStopDeparture]:
    departure_choice = get_choice_from_input_paginate(
        "Select departure",
        departures,
        display=short_string_of_bus_stop_departure,
    )
    match departure_choice:
        case PickSingle(departure):
            return departure
        case _:
            return None


def get_alight_call_and_index_from_input(
    calls: list[BusCallInData], board_call_index: int
) -> Optional[tuple[BusCallInData, int]]:
    possible_alight_calls = calls[board_call_index + 1 :]
    alight_choice = get_choice_from_input_paginate(
        "Alight call",
        list(enumerate(possible_alight_calls)),
        lambda x: string_of_bus_call_in(x[1]),
    )
    match alight_choice:
        case PickSingle((i, choice)):
            return (choice, i + board_call_index + 1)
        case _:
            return None


def get_bus_vehicle_from_input(
    vehicles: list[BusVehicleDetails],
) -> Optional[BusVehicleDetails]:
    result = get_choice_from_input_paginate(
        "Select vehicle", vehicles, lambda v: f"{v.vehicle_numberplate}"
    )
    match result:
        case PickSingle(vehicle):
            return vehicle
        case _:
            return None


def get_bus_vehicle(
    conn: Connection,
    bus_operator: BusOperatorDetails,
    suggested_vehicle: Optional[str] = None,
) -> Optional[BusVehicleDetails]:
    vehicle_id = get_text_from_input("Vehicle id", suggested_vehicle)
    if vehicle_id is None or vehicle_id == "":
        return None
    vehicles = select_bus_vehicle_details_fetchall(
        conn, bus_operator.bus_operator_id, vehicle_id
    )
    if len(vehicles) == 1:
        return vehicles[0]
    if len(vehicles) > 1:
        vehicle = get_bus_vehicle_from_input(vehicles)
        if vehicle is not None:
            return vehicle
    print_information(
        f"Vehicle {vehicle_id} not found for operator {bus_operator.operator_name}, falling back to all operators"
    )
    vehicles = select_bus_vehicle_details_fetchall(conn, None, vehicle_id)
    if len(vehicles) == 0:
        print_error(f"No vehicles found with id {vehicle_id}")
        return None
    return get_bus_vehicle_from_input(vehicles)


def get_board_call_index_from_bustimes_journey(
    journey: BustimesJourney, board_atco: str
) -> Optional[int]:
    for i, call in enumerate(journey.calls):
        if call.stop_id == board_atco:
            return i
    return None


def get_bus_journey_from_bustimes_journey(
    conn: Connection,
    driver: Driver,
    departure: BusStopDeparture,
    board_stop: BusStopDetails,
) -> Optional[BustimesJourneyData]:
    journey = get_bustimes_journey(
        driver,
        departure.dep_time.date(),
        board_stop.atco_code,
        departure.bustimes_id,
    )
    if journey is None:
        print(f"Could not get journey {departure.bustimes_id}")
        return None
    board_call_index = get_board_call_index_from_bustimes_journey(
        journey, board_stop.atco_code
    )
    if board_call_index is None:
        print("Could not get board index")
        return None
    journey_calls = [
        BusCallInData(
            i,
            call.stop_name,
            call.stop_id,
            call.plan_arr,
            call.act_arr,
            call.plan_dep,
            call.act_dep,
        )
        for i, call in enumerate(journey.calls)
    ]
    bustimes_operator = get_bustimes_operator(driver, journey.operator.slug)
    if bustimes_operator is None:
        print_information("Could not get operator")
        return None
    operator = select_bus_operator_details_by_national_operator_code_fetchone(
        conn, bustimes_operator.national_operator_code
    )
    if operator is None:
        print_information("Could not get operator")
        return None
    service = select_bus_service_details_by_operator_id_and_line_name_fetchone(
        conn, operator.bus_operator_id, journey.route.name
    )
    if service is None:
        print_information(
            f"Could not get service {journey.route.name} and operator {operator.operator_name}"
        )
        return None
    return BustimesJourneyData(
        journey_calls, board_call_index, operator, service, journey.vehicle
    )


def get_bus_journey_from_bustimes_trip(
    conn: Connection,
    driver: Driver,
    departure: BusStopDeparture,
    board_stop: BusStopDetails,
) -> Optional[BustimesJourneyData]:
    trip_id = departure.bustimes_id
    journey_calls = []
    trip_and_board_call_index = get_bus_trip(
        driver,
        conn,
        trip_id,
        board_stop,
        departure,
    )
    if trip_and_board_call_index is None:
        print(f"Could not get trip {trip_id}")
        return None
    journey_timetable, board_call_index = trip_and_board_call_index
    journey_calls = journey_timetable.calls
    operator = journey_timetable.operator
    service = journey_timetable.service
    return BustimesJourneyData(
        journey_calls, board_call_index, operator, service, None
    )


def get_board_datetime() -> Optional[tuple[datetime, timedelta]]:
    board_year = get_year_from_input()
    if board_year is None:
        return None
    board_month = get_month_from_input()
    if board_month is None:
        return None
    board_day = get_day_from_input(board_month, board_year)
    if board_day is None:
        return None
    board_time = get_time_from_input()
    if board_time is None:
        return None
    board_datetime = datetime(
        board_year, board_month, board_day, board_time.hour, board_time.minute
    )
    today = datetime.today()
    if board_datetime.date() < today.date() - timedelta(days=28):
        board_day_of_week = board_datetime.weekday()
        today_day_of_week = today.weekday()
        day_of_week_diff = board_day_of_week - today_day_of_week
        if day_of_week_diff < 0:
            day_of_week_diff = day_of_week_diff + 7
        new_board_date = today.date() + timedelta(days=day_of_week_diff)

        new_board_datetime = datetime.combine(
            new_board_date, board_datetime.time()
        )
        print_information(
            f"{board_datetime.strftime('%d/%m/%Y %H:%M:%S')} is 28 days before today, "
            + f"using {new_board_datetime.strftime('%d/%m/%Y %H:%M:%S')} instead"
        )
        datetime_offset = new_board_datetime - board_datetime
        board_datetime = new_board_datetime
    else:
        datetime_offset = timedelta(0)
    return (board_datetime, datetime_offset)


def get_bus_vehicle_from_bustimes_data(
    conn: Connection,
    bustimes_journey_data: BustimesJourneyData,
) -> Optional[BusVehicleDetails]:
    if (
        bustimes_journey_data.vehicle is None
        or bustimes_journey_data.vehicle.identifier is None
    ):
        return get_bus_vehicle(conn, bustimes_journey_data.operator)
    vehicle_options = select_bus_vehicle_details_fetchall(
        conn,
        bustimes_journey_data.operator.bus_operator_id,
        bustimes_journey_data.vehicle.identifier,
    )
    if len(vehicle_options) == 0:
        print_information(
            f"Could not find vehicle {bustimes_journey_data.vehicle.identifier} for {bustimes_journey_data.operator.operator_name}, skipping"
        )
        return None
    return vehicle_options[0]


def get_bus_leg_from_input(
    conn: Connection, users: list[TransportUserPublicOutData]
) -> Optional[BusLegInData]:
    board_stop = get_bus_stop_from_input(conn, prompt="Board stop")
    if board_stop is None:
        print_information("Could not get board stop")
        return None
    datetime_result = get_board_datetime()
    if datetime_result is None:
        print_information("Could not get board datetime")
        return None
    board_datetime, datetime_offset = datetime_result
    with DriverManager() as driver:
        driver.get_page_html(get_bustimes_url(), accept_bustimes_cookies)
        departures = get_departures_from_bus_stop(
            driver, board_stop, board_datetime, datetime_offset
        )
        if len(departures) == 0:
            print_information("No departures from bus stop")
            return None
        departure = get_bus_stop_departure_from_input(departures)
        if departure is None:
            return None
        if departure.live:
            bustimes_journey_data = get_bus_journey_from_bustimes_journey(
                conn, driver, departure, board_stop
            )
        else:
            bustimes_journey_data = get_bus_journey_from_bustimes_trip(
                conn, driver, departure, board_stop
            )
        if bustimes_journey_data is None:
            return None
        alight_call_and_index = get_alight_call_and_index_from_input(
            bustimes_journey_data.calls, bustimes_journey_data.board_call_index
        )
        if alight_call_and_index is None:
            return None
        _, alight_call_index = alight_call_and_index
        vehicle = get_bus_vehicle_from_bustimes_data(
            conn, bustimes_journey_data
        )
        journey = BusJourneyInData(
            bustimes_journey_data.service.bus_service_id,
            bustimes_journey_data.calls,
            vehicle.bus_vehicle_id if vehicle is not None else None,
        )
        leg = BusLegInData(
            journey, bustimes_journey_data.board_call_index, alight_call_index
        )
        return leg


def record_bus_leg(conn: Connection) -> None:
    users = get_users_from_input(conn)
    if len(users) == 0:
        return
    leg = get_bus_leg_from_input(conn, users)
    if leg is None:
        print_information("Could not get bus leg")
        return
    insert_bus_leg_result = insert_bus_leg_fetchone(
        conn, [user.user_id for user in users], leg
    )
    if insert_bus_leg_result is None:
        print_information("Could not insert bus leg")
        return
    print_information(f"Recorded bus leg {insert_bus_leg_result.bus_leg_id}")


if __name__ == "__main__":
    with connect_with_env() as conn:
        register_types(conn)
        record_bus_leg(conn)
