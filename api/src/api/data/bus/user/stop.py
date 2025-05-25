from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from api.data.bus.operators import BusOperator, register_bus_operator
from api.data.bus.overview import (
    BusCallOverview,
    BusServiceOverview,
    register_bus_call_overview,
    register_bus_service_overview,
)
from api.data.bus.stop import register_bus_stop, register_bus_stop_overview
from api.utils.database import DbConnectionData, connect, register_type
from psycopg import Connection


@dataclass
class BusStopLegUserDetails:
    id: int
    service: BusServiceOverview
    operator: BusOperator
    board: BusCallOverview
    alight: BusCallOverview
    current: BusCallOverview
    before: int
    after: int


def register_bus_stop_leg_user_details(
    leg_id: int,
    bus_service: BusServiceOverview,
    bus_operator: BusOperator,
    board_call: BusCallOverview,
    alight_call: BusCallOverview,
    this_call: BusCallOverview,
    stops_before: int,
    stops_after: int,
) -> BusStopLegUserDetails:
    return BusStopLegUserDetails(
        leg_id,
        bus_service,
        bus_operator,
        board_call,
        alight_call,
        this_call,
        stops_before,
        stops_after,
    )


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
    legs: list[BusStopLegUserDetails]


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
    stop_legs: list[BusStopLegUserDetails],
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


def register_bus_stop_user_details_types(conn):
    register_type(conn, "BusStopOverviewOutData", register_bus_stop_overview)
    register_type(
        conn, "BusServiceOverviewOutData", register_bus_service_overview
    )
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusCallOverviewOutData", register_bus_call_overview)
    register_type(
        conn, "BusStopLegUserDetails", register_bus_stop_leg_user_details
    )
    register_type(conn, "BusStopUserDetails", register_bus_stop_user_details)


def get_bus_stop_user_details(
    conn: Connection, user_id: int, bus_stop_id: int
) -> Optional[BusStopUserDetails]:
    register_bus_stop_user_details_types(conn)
    result = conn.execute(
        "SELECT GetBusStopUserDetails(%s, %s)", [user_id, bus_stop_id]
    ).fetchone()
    if result is None:
        return result
    return result[0]


if __name__ == "__main__":
    with connect(
        DbConnectionData("transport", "transport", "transport", "localhost")
    ) as conn:
        get_bus_stop_user_details(conn, 1, 283041)
