from datetime import datetime, timedelta
from typing import Optional
from psycopg import Connection

from api.utils.database import connect, get_db_connection_data_from_args
from api.utils.interactive import (
    PickSingle,
    information,
    input_day,
    input_month,
    input_select,
    input_select_paginate,
    input_text,
    input_time,
    input_year,
)
from api.user import User, input_user
from api.db.bus.journey import (
    BusCallIn,
    BusJourneyIn,
    get_bus_journey,
    string_of_bus_call_in,
)
from api.db.bus.leg import BusLegIn, insert_leg
from api.db.bus.operators import BusOperatorDetails
from api.db.bus.stop import (
    BusStopDetails,
    BusStopDeparture,
    get_bus_stops,
    get_departures_from_bus_stop,
    short_string_of_bus_stop,
    short_string_of_bus_stop_departure,
)
from api.db.bus.vehicle import (
    BusVehicleDetails,
    get_bus_vehicles_by_id,
    get_bus_vehicles_by_operator_and_id,
    string_of_bus_vehicle_out,
)


def get_bus_stop_input(
    conn: Connection, prompt: str = "Bus stop name"
) -> Optional[BusStopDetails]:
    search_string = input_text("Bus stop name")
    if search_string is None:
        return None
    bus_stops = get_bus_stops(conn, search_string)
    bus_stop_choice = input_select_paginate(
        "Select bus stop", bus_stops, display=short_string_of_bus_stop
    )
    match bus_stop_choice:
        case PickSingle(bus_stop):
            return bus_stop
        case _:
            return None


def get_bus_stop_departure_input(
    departures: list[BusStopDeparture],
) -> Optional[BusStopDeparture]:
    departure_choice = input_select_paginate(
        "Select departure",
        departures,
        display=short_string_of_bus_stop_departure,
    )
    match departure_choice:
        case PickSingle(departure):
            return departure
        case _:
            return None


def get_alight_stop_input(
    calls: list[BusCallIn], board_call_index: int
) -> Optional[tuple[BusCallIn, int]]:
    possible_alight_calls = calls[board_call_index + 1 :]
    alight_choice = input_select_paginate(
        "Alight call",
        list(enumerate(possible_alight_calls)),
        lambda x: string_of_bus_call_in(x[1]),
    )
    match alight_choice:
        case PickSingle((i, choice)):
            return (choice, i + board_call_index + 1)
        case _:
            return None


def input_vehicle(
    vehicles: list[BusVehicleDetails],
) -> Optional[BusVehicleDetails]:
    result = input_select("Select vehicle", vehicles, string_of_bus_vehicle_out)
    match result:
        case PickSingle(vehicle):
            return vehicle
        case _:
            return None


def get_bus_vehicle(
    conn: Connection, bus_operator: BusOperatorDetails
) -> Optional[BusVehicleDetails]:
    vehicle_id = input_text("Vehicle id")
    if vehicle_id is None:
        return None
    vehicles = get_bus_vehicles_by_operator_and_id(
        conn, bus_operator, vehicle_id
    )
    if len(vehicles) == 1:
        return vehicles[0]
    if len(vehicles) > 1:
        vehicle = input_vehicle(vehicles)
        if vehicle is not None:
            return vehicle
    information(
        f"Vehicle {vehicle_id} not found for operator {bus_operator.name}, falling back to all operators"
    )
    vehicles = get_bus_vehicles_by_id(conn, vehicle_id)
    if len(vehicles) == 0:
        information(f"No vehicles found with id {vehicle_id}")
        return None
    return input_vehicle(vehicles)


def get_bus_leg_input(
    conn: Connection, users: list[User]
) -> Optional[BusLegIn]:
    board_stop = get_bus_stop_input(conn, prompt="Board stop")
    if board_stop is None:
        print("Could not get board stop")
        exit(-1)

    board_year = input_year()
    if board_year is None:
        return None

    board_month = input_month()
    if board_month is None:
        return None

    board_day = input_day(board_month, board_year)
    if board_day is None:
        return None

    board_time = input_time()
    if board_time is None:
        return None

    board_datetime = datetime(
        board_year, board_month, board_day, board_time.hour, board_time.minute
    )

    today = datetime.today()

    if board_datetime.date() < today.date():
        board_day_of_week = board_datetime.weekday()
        today_day_of_week = today.weekday()
        day_of_week_diff = board_day_of_week - today_day_of_week
        if day_of_week_diff < 0:
            day_of_week_diff = day_of_week_diff + 7
        new_board_date = today.date() + timedelta(days=day_of_week_diff)

        new_board_datetime = datetime.combine(
            new_board_date, board_datetime.time()
        )
        information(
            f"{board_datetime.strftime("%d/%m/%Y %H:%M:%S")} is before today, "
            + f"using {new_board_datetime.strftime("%d/%m/%Y %H:%M:%S")} instead"
        )
        datetime_offset = new_board_datetime - board_datetime
        board_datetime = new_board_datetime
    else:
        datetime_offset = timedelta(0)

    departures = get_departures_from_bus_stop(
        board_stop, board_datetime, datetime_offset
    )
    if len(departures) == 0:
        information("No departures from bus stop")
        return None

    departure = get_bus_stop_departure_input(departures)
    if departure is None:
        return None

    journey_and_board_call_index = get_bus_journey(
        conn,
        departure.bustimes_journey_id,
        board_stop,
        departure,
    )
    if journey_and_board_call_index is None:
        print("Could not get journey")
        return None

    (journey_timetable, board_call_index) = journey_and_board_call_index

    alight_call_and_index = get_alight_stop_input(
        journey_timetable.calls, board_call_index
    )
    if alight_call_and_index is None:
        return None

    (_, alight_call_index) = alight_call_and_index

    vehicle = get_bus_vehicle(conn, journey_timetable.operator)

    journey = BusJourneyIn(
        journey_timetable.id,
        journey_timetable.operator,
        journey_timetable.service,
        journey_timetable.calls,
        vehicle,
    )
    leg = BusLegIn(journey, board_call_index, alight_call_index)
    insert_leg(conn, users, leg)
    return leg


if __name__ == "__main__":
    connection_data = get_db_connection_data_from_args()
    with connect(connection_data) as conn:
        users = input_user(conn)
        if users is not None:
            get_bus_leg_input(conn, users)
