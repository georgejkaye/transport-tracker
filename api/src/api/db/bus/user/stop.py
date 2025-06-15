from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from psycopg import Connection
from psycopg.rows import class_row


from api.db.bus.operators import (
    register_bus_operator_details_types,
)
from api.db.bus.overview import (
    BusCallDetails,
    BusLegServiceDetails,
    register_bus_call_details_types,
    register_bus_leg_service_details_types,
)
from api.utils.database import register_type


@dataclass
class BusStopLegDetails:
    id: int
    service: BusLegServiceDetails
    board: BusCallDetails
    alight: BusCallDetails
    current: BusCallDetails
    before: int
    after: int


def register_bus_stop_leg_details(
    leg_id: int,
    bus_service: BusLegServiceDetails,
    board_call: BusCallDetails,
    alight_call: BusCallDetails,
    this_call: BusCallDetails,
    stops_before: int,
    stops_after: int,
) -> BusStopLegDetails:
    return BusStopLegDetails(
        leg_id,
        bus_service,
        board_call,
        alight_call,
        this_call,
        stops_before,
        stops_after,
    )


def register_bus_stop_leg_user_details_types(conn: Connection) -> None:
    register_bus_leg_service_details_types(conn)
    register_bus_operator_details_types(conn)
    register_bus_call_details_types(conn)
    register_type(conn, "BusStopLegDetails", register_bus_stop_leg_details)


@dataclass
class BusStopUserDetails:
    id: int
    atco: str
    naptan: Optional[str]
    name: str
    landmark: Optional[str]
    street: Optional[str]
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
    legs: list[BusStopLegDetails]


def register_bus_stop_user_details(
    bus_stop_id: int,
    atco_code: str,
    naptan_code: str,
    stop_name: str,
    landmark_name: str,
    street_name: str,
    crossing_name: str,
    indicator: str,
    bearing: str,
    locality_name: str,
    parent_locality_name: str,
    grandparent_locality_name: str,
    town_name: str,
    suburb_name: str,
    latitude: Decimal,
    longitude: Decimal,
    stop_legs: list[BusStopLegDetails],
) -> BusStopUserDetails:
    return BusStopUserDetails(
        bus_stop_id,
        atco_code,
        naptan_code,
        stop_name,
        landmark_name,
        street_name,
        crossing_name,
        indicator,
        bearing,
        locality_name,
        parent_locality_name,
        grandparent_locality_name,
        town_name,
        suburb_name,
        latitude,
        longitude,
        stop_legs,
    )


def register_bus_stop_user_details_types(conn: Connection) -> None:
    register_bus_stop_leg_user_details_types(conn)
    register_type(conn, "BusStopUserDetails", register_bus_stop_user_details)


def get_user_details_for_bus_stop(
    conn: Connection, user_id: int, bus_stop_id: int
) -> Optional[BusStopUserDetails]:
    register_bus_stop_user_details_types(conn)
    with conn.cursor(row_factory=class_row(BusStopUserDetails)) as cur:
        result = cur.execute(
            "SELECT GetUserDetailsForBusStop(%s, %s)", [user_id, bus_stop_id]
        ).fetchone()
        if result is None:
            return result
        return result


def get_user_details_for_bus_stop_by_atco(
    conn: Connection, user_id: int, atco: str
) -> Optional[BusStopUserDetails]:
    register_bus_stop_user_details_types(conn)
    with conn.cursor(row_factory=class_row(BusStopUserDetails)) as cur:
        result = cur.execute(
            "SELECT GetUserDetailsForBusStopByAtco(%s, %s)", [user_id, atco]
        ).fetchone()
        if result is None:
            return result
        return result


def get_user_details_for_bus_stops(
    conn: Connection, user_id: int
) -> list[BusStopUserDetails]:
    register_bus_stop_user_details_types(conn)
    with conn.cursor(row_factory=class_row(BusStopUserDetails)) as cur:
        result = cur.execute(
            "SELECT GetUserDetailsForBusStops(%s)", [user_id]
        ).fetchall()
        return result
