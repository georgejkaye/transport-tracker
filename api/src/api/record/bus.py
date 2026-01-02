from datetime import datetime, timedelta
from typing import Optional

from psycopg import Connection

from api.classes.bus.journey import (
    string_of_bus_call_in,
)
from api.classes.bus.stop import (
    BusStopDeparture,
    short_string_of_bus_stop_departure,
    short_string_of_bus_stop_details,
)
from api.db.functions.insert.bus import insert_bus_leg_fetchone
from api.db.functions.select.bus import (
    select_bus_stop_details_by_name_fetchall,
    select_bus_vehicle_details_fetchall,
)
from api.db.types.bus import (
    BusCallInData,
    BusJourneyInData,
    BusLegInData,
    BusOperatorDetails,
    BusStopDetails,
    BusVehicleDetails,
)
from api.db.types.register import register_types
from api.pull.bus.journey import get_bus_journey_and_board_call_index
from api.pull.bus.stop import get_departures_from_bus_stop
from api.record.user import input_users
from api.utils.database import (
    connect_with_env,
)
from api.utils.interactive import (
    PickSingle,
    get_choice_from_input_paginate,
    get_datetime_from_input,
    get_day_from_input,
    get_month_from_input,
    get_text_from_input,
    get_time_from_input,
    get_year_from_input,
    print_error,
    print_information,
)


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
    suggested_vehicle: Optional[str],
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


def get_board_datetime() -> Optional[datetime]:
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
    return datetime(
        board_year, board_month, board_day, board_time.hour, board_time.minute
    )


def get_search_datetime_and_offset(
    board_datetime: datetime,
) -> tuple[datetime, timedelta]:
    today = datetime.today()
    if board_datetime.date() >= today.date():
        return (board_datetime, timedelta(0))
    board_day_of_week = board_datetime.weekday()
    today_day_of_week = today.weekday()
    day_of_week_diff = board_day_of_week - today_day_of_week
    if day_of_week_diff < 0:
        day_of_week_diff = day_of_week_diff + 7
    new_board_date = today.date() + timedelta(days=day_of_week_diff)
    new_board_datetime = datetime.combine(
        new_board_date, board_datetime.time(), board_datetime.tzinfo
    )
    print_information(
        f"{board_datetime.strftime('%d/%m/%Y %H:%M:%S')} is before today, "
        + f"using {new_board_datetime.strftime('%d/%m/%Y %H:%M:%S')} instead"
    )
    datetime_offset = new_board_datetime - board_datetime
    return (new_board_datetime, datetime_offset)


def get_bus_leg_from_input(conn: Connection) -> Optional[BusLegInData]:
    board_stop = get_bus_stop_from_input(conn, prompt="Board stop")
    if board_stop is None:
        print_error("Could not get board stop")
        return None
    board_datetime = get_datetime_from_input()
    if board_datetime is None:
        print_error("Could not get board datetime")
        return None
    (search_datetime, search_offset) = get_search_datetime_and_offset(
        board_datetime
    )
    departures = get_departures_from_bus_stop(
        board_stop, search_datetime, search_offset
    )
    if len(departures) == 0:
        print_error("No departures from bus stop")
        return None
    departure = get_bus_stop_departure_from_input(departures)
    if departure is None:
        print_error("Could not get departure")
        return None
    journey_and_board_call_index = get_bus_journey_and_board_call_index(
        conn,
        departure.bustimes_journey_id,
        board_stop,
        departure,
    )
    if journey_and_board_call_index is None:
        print_error("Could not get journey")
        return None
    (journey_timetable, board_call_index) = journey_and_board_call_index
    alight_call_and_index = get_alight_call_and_index_from_input(
        journey_timetable.calls, board_call_index
    )
    if alight_call_and_index is None:
        return None
    (_, alight_call_index) = alight_call_and_index
    vehicle = get_bus_vehicle(
        conn,
        journey_timetable.operator,
        departure.vehicle if search_offset == 0 else None,
    )
    journey = BusJourneyInData(
        journey_timetable.id,
        journey_timetable.service.bus_service_id,
        journey_timetable.calls,
        vehicle.bus_vehicle_id if vehicle is not None else None,
    )
    leg = BusLegInData(journey, board_call_index, alight_call_index)
    return leg


def record_bus_leg(conn: Connection):
    users = input_users(conn)
    if len(users) == 0:
        return
    leg = get_bus_leg_from_input(conn)
    if leg is None:
        print_error("Could not get bus leg")
        return
    insert_bus_leg_result = insert_bus_leg_fetchone(
        conn, [user.user_id for user in users], leg
    )
    if insert_bus_leg_result is None:
        print_error("Could not insert bus leg")
        return
    print_information(f"Recorded bus leg {insert_bus_leg_result.bus_leg_id}")


if __name__ == "__main__":
    with connect_with_env() as conn:
        register_types(conn)
        record_bus_leg(conn)
