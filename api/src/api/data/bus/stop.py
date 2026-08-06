from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from api.utils.database import register_type
from psycopg import Connection


@dataclass
class BusStopData:
    atco: str
    naptan: str
    common_name: str
    landmark: Optional[str]
    street: str
    crossing: Optional[str]
    indicator: Optional[str]
    bearing: str
    locality: str
    parent_locality: Optional[str]
    grandparent_locality: Optional[str]
    town: Optional[str]
    suburb: Optional[str]
    latitude: Decimal
    longitude: Decimal


def insert_bus_stops(conn: Connection, bus_stops: list[BusStopData]):
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
    conn.execute("SELECT * FROM InsertBusStops(%s::BusStopInData[])", [bus_stop_tuples])
    conn.commit()


@dataclass
class BusStopDetails:
    id: int
    atco: str
    naptan: str
    common_name: str
    landmark: str
    street: str
    crossing: Optional[str]
    indicator: Optional[str]
    bearing: str
    locality: str
    parent_locality: Optional[str]
    grandparent_locality: Optional[str]
    town: Optional[str]
    suburb: Optional[str]
    latitude: Decimal
    longitude: Decimal


def register_bus_stop_details(
    id: int,
    atco: str,
    naptan: str,
    common_name: str,
    landmark: str,
    street: str,
    crossing: Optional[str],
    indicator: Optional[str],
    bearing: str,
    locality: str,
    parent_locality: Optional[str],
    grandparent_locality: Optional[str],
    town: Optional[str],
    suburb: Optional[str],
    latitude: float,
    longitude: float,
) -> BusStopDetails:
    return BusStopDetails(
        id,
        atco,
        naptan,
        common_name,
        landmark,
        street,
        crossing,
        indicator,
        bearing,
        locality,
        parent_locality,
        grandparent_locality,
        town,
        suburb,
        Decimal(latitude),
        Decimal(longitude),
    )


def register_bus_stop_details_types(conn: Connection):
    register_type(conn, "BusStopDetails", register_bus_stop_details)


def short_string_of_bus_stop(bus_stop: BusStopDetails) -> str:
    if bus_stop.indicator is None:
        indicator_text = ""
    else:
        indicator_text = f" ({bus_stop.indicator})"
    return (
        f"{bus_stop.common_name}{indicator_text}, {bus_stop.locality} ({bus_stop.atco})"
    )


def get_bus_stops(conn: Connection, search_string: str) -> list[BusStopDetails]:
    register_bus_stop_details_types(conn)
    rows = conn.execute("SELECT GetBusStopsByName(%s)", [search_string]).fetchall()
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


@dataclass
class BusCallStopDetails:
    id: int
    atco: str
    name: str
    locality: str
    street: Optional[str]
    indicator: Optional[str]


def register_bus_call_stop_details(
    bus_stop_id: int,
    stop_atco: str,
    stop_name: str,
    stop_locality: str,
    stop_street: Optional[str],
    stop_indicator: Optional[str],
) -> BusCallStopDetails:
    return BusCallStopDetails(
        bus_stop_id,
        stop_atco,
        stop_name,
        stop_locality,
        stop_street,
        stop_indicator,
    )


def register_bus_call_stop_details_types(conn: Connection):
    register_type(conn, "BusCallStopDetails", register_bus_call_stop_details)
