from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from psycopg import Connection


@dataclass
class BusStopData:
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


def insert_bus_stops(conn: Connection, bus_stops: list[BusStopData]):
    print(bus_stops[0])
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
        "SELECT * FROM InsertBusStops(%s::BusStopData[])", [bus_stop_tuples]
    )
    conn.commit()


@dataclass
class BusStop:
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
