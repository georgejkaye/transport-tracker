from calendar import c
from datetime import datetime
from typing import Optional
from unittest.mock import NonCallableMagicMock
from api.data.bus.stop import (
    BusStop,
    BusStopDeparture,
    get_bus_stop_page,
    get_bus_stops,
    get_departures_from_bus_stop,
    get_departures_from_bus_stop_soup,
    short_string_of_bus_stop,
    short_string_of_bus_stop_departure,
)
from api.utils.database import connect
from api.utils.interactive import (
    PickSingle,
    input_day,
    input_month,
    input_select,
    input_text,
    input_time,
    input_year,
)
from psycopg import Connection


def get_bus_stop_input(
    conn: Connection, prompt: str = "Bus stop name"
) -> Optional[BusStop]:
    search_string = input_text("Bus stop name")
    if search_string is None:
        return None
    bus_stops = get_bus_stops(conn, search_string)
    bus_stop_choice = input_select(
        "Select bus stop",
        bus_stops,
        display=short_string_of_bus_stop,
        cancel=True,
    )
    match bus_stop_choice:
        case PickSingle(bus_stop):
            return bus_stop
        case _:
            return None


def get_bus_stop_departure_input(
    departures: list[BusStopDeparture],
) -> Optional[BusStopDeparture]:
    departure_choice = input_select(
        "Select departure",
        departures,
        display=short_string_of_bus_stop_departure,
        cancel=True,
    )
    match departure_choice:
        case PickSingle(departure):
            return departure
        case _:
            return None


def get_bus_leg_input(conn: Connection) -> Optional[BusStop]:
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
    board_stop = get_bus_stop_departure_input(departures)


if __name__ == "__main__":
    with connect("transport", "transport", "transport", "localhost") as (
        conn,
        _,
    ):
        get_bus_leg_input(conn)
