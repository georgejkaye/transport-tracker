from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from psycopg import Connection
from psycopg.rows import class_row

from api.classes.bus.journey import (
    BusCallDetails,
)
from api.classes.bus.leg import (
    BusLegServiceDetails,
)
from api.utils.database import register_type


@dataclass
class BusStopLegDetails:
    leg_id: int
    service: BusLegServiceDetails
    board: BusCallDetails
    alight: BusCallDetails
    current: BusCallDetails
    before: int
    after: int


def register_bus_stop_leg_details(conn: Connection) -> None:
    register_type(conn, "BusStopLegDetails", BusStopLegDetails)


@dataclass
class BusStopUserDetails:
    stop_id: int
    atco_code: str
    naptan_code: Optional[str]
    stop_name: str
    landmark_name: Optional[str]
    street_name: Optional[str]
    crossing_name: Optional[str]
    indicator: Optional[str]
    bearing: str
    locality_name: str
    parent_locality_name: Optional[str]
    grandparent_locality_name: Optional[str]
    town_name: Optional[str]
    suburb_name: Optional[str]
    latitude: Decimal
    longitude: Decimal
    stop_legs: list[BusStopLegDetails]


def register_bus_stop_user_details(conn: Connection) -> None:
    register_type(conn, "BusStopUserDetails", BusStopUserDetails)


def get_user_details_for_bus_stop(
    conn: Connection, user_id: int, bus_stop_id: int
) -> Optional[BusStopUserDetails]:
    with conn.cursor(row_factory=class_row(BusStopUserDetails)) as cur:
        result = cur.execute(
            "SELECT * FROM GetUserDetailsForBusStop(%s, %s)",
            [user_id, bus_stop_id],
        ).fetchone()
        if result is None:
            return result
        return result


def get_user_details_for_bus_stop_by_atco(
    conn: Connection, user_id: int, atco: str
) -> Optional[BusStopUserDetails]:
    with conn.cursor(row_factory=class_row(BusStopUserDetails)) as cur:
        result = cur.execute(
            "SELECT * FROM GetUserDetailsForBusStopByAtco(%s, %s)",
            [user_id, atco],
        ).fetchone()
        if result is None:
            return result
        return result


def get_user_details_for_bus_stops(
    conn: Connection, user_id: int
) -> list[BusStopUserDetails]:
    with conn.cursor(row_factory=class_row(BusStopUserDetails)) as cur:
        result = cur.execute(
            "SELECT * FROM GetUserDetailsForBusStops(%s)", [user_id]
        ).fetchall()
        return result
