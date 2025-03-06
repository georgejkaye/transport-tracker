from datetime import datetime
import sys
from typing import Optional
from psycopg import Connection

from api.utils.database import connect
from api.utils.interactive import (
    PickSingle,
    input_day,
    input_month,
    input_select_paginate,
    input_text,
    input_time,
    input_year,
)

from api.user import User, input_user

from api.data.bus.leg import BusLegIn, insert_leg
from api.data.bus.operators import BusOperator
from api.data.bus.service import (
    BusCallIn,
    BusJourney,
    get_bus_journey,
    string_of_bus_call_in,
)
from api.data.bus.stop import (
    BusStop,
    BusStopDeparture,
    get_bus_stops,
    get_departures_from_bus_stop,
    short_string_of_bus_stop,
    short_string_of_bus_stop_departure,
)
from api.data.bus.vehicle import BusVehicle, get_bus_vehicle_by_operator_and_id


def get_bus_stop_input(
    conn: Connection, prompt: str = "Bus stop name"
) -> Optional[BusStop]:
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


def get_bus_vehicle(
    conn: Connection, bus_operator: BusOperator
) -> Optional[BusVehicle]:
    vehicle_id = input_text("Vehicle id")
    if vehicle_id is None:
        return None
    vehicle = get_bus_vehicle_by_operator_and_id(conn, bus_operator, vehicle_id)
    return vehicle


def get_bus_leg_input(conn: Connection, user: User) -> Optional[BusJourney]:
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

    board_day = input_day(board_year, board_month)
    if board_day is None:
        return None

    board_time = input_time()
    if board_time is None:
        return None

    board_datetime = datetime(
        board_year, board_month, board_day, board_time.hour, board_time.minute
    )

    departures = get_departures_from_bus_stop(board_stop, board_datetime)
    departure = get_bus_stop_departure_input(departures)
    if departure is None:
        return None

    journey_and_board_call_index = get_bus_journey(
        conn, departure.bustimes_journey_id, board_stop, departure
    )
    if journey_and_board_call_index is None:
        return None

    (journey, board_call_index) = journey_and_board_call_index

    alight_stop = get_alight_stop_input(journey.calls, board_call_index)
    if alight_stop is None:
        return None

    vehicle = get_bus_vehicle(conn, journey.operator)

    leg = BusLegIn(
        user.user_id, journey, board_stop.atco, alight_stop.atco, vehicle
    )

    insert_leg(conn, leg)


if __name__ == "__main__":
    with connect("transport", "transport", "transport", "localhost") as (
        conn,
        _,
    ):
        user = Traveller(1, "george")
        get_bus_leg_input(conn, user)
