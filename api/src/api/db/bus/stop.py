from psycopg import Connection

from api.classes.bus.stop import (
    BusStopData,
    BusStopDetails,
    register_bus_stop_details_types,
)


def insert_bus_stops(conn: Connection, bus_stops: list[BusStopData]) -> None:
    bus_stop_tuples = [
        (
            bus_stop.atco,
            bus_stop.naptan,
            bus_stop.common_name,
            bus_stop.landmark,
            bus_stop.street,
            bus_stop.crossing,
            bus_stop.indicator,
            bus_stop.bearing,
            bus_stop.locality,
            bus_stop.parent_locality,
            bus_stop.grandparent_locality,
            bus_stop.town,
            bus_stop.suburb,
            bus_stop.latitude,
            bus_stop.longitude,
        )
        for bus_stop in bus_stops
    ]
    conn.execute(
        "SELECT * FROM InsertBusStops(%s::BusStopInData[])", [bus_stop_tuples]
    )
    conn.commit()


def get_bus_stops(conn: Connection, search_string: str) -> list[BusStopDetails]:
    register_bus_stop_details_types(conn)
    rows = conn.execute(
        "SELECT GetBusStopsByName(%s)", [search_string]
    ).fetchall()
    return [row[0] for row in rows]


def get_bus_stops_from_atcos(
    conn: Connection, atcos: list[str]
) -> dict[str, BusStopDetails]:
    register_bus_stop_details_types(conn)
    rows = conn.execute("SELECT GetBusStopsByAtco(%s)", [atcos])
    atco_bus_stop_dict: dict[str, BusStopDetails] = {}
    for row in rows:
        bus_stop = row[0]
        atco_bus_stop_dict[bus_stop.atco] = bus_stop
    return atco_bus_stop_dict
