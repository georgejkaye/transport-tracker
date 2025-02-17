from calendar import c
from typing import Optional
from api.data.bus.stop import (
    BusStop,
    get_bus_stop_page,
    get_bus_stops,
    get_departures_from_bus_stop_soup,
    short_string_of_bus_stop,
)
from api.utils.database import connect
from api.utils.interactive import PickSingle, input_select, input_text
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


def get_bus_leg_input(conn: Connection) -> Optional[BusStop]:
    board_stop = get_bus_stop_input(conn, prompt="Board stop")
    if board_stop is None:
        print("Could not get board stop")
        exit(-1)

    alight_stop = get_bus_stop_input(conn, prompt="Alight stop")
    if alight_stop is None:
        print("Could not get alight stop")
        exit(-1)


if __name__ == "__main__":
    with connect("transport", "transport", "transport", "localhost") as (
        conn,
        _,
    ):
        bus_stop = get_bus_stop_input(conn)
        if bus_stop is not None:
            soup = get_bus_stop_page(bus_stop)
            if soup is not None:
                departures = get_departures_from_bus_stop_soup(soup)
                for departure in departures:
                    print(departure)
