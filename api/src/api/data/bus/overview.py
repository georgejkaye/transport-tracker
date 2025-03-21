from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from api.data.bus.operators import BusOperator, register_bus_operator
from api.utils.database import register_type
from psycopg import Connection


@dataclass
class BusStopOverview:
    id: int
    atco: str
    name: str
    locality: str
    street: str


def register_bus_stop_overview(
    bus_stop_id: int,
    stop_atco: str,
    stop_name: str,
    stop_locality: str,
    stop_street: str,
) -> BusStopOverview:
    return BusStopOverview(
        bus_stop_id, stop_atco, stop_name, stop_locality, stop_street
    )


@dataclass
class BusServiceOverview:
    id: int
    line: str


def register_bus_service_overview(
    service_id: int, service_line: str
) -> BusServiceOverview:
    return BusServiceOverview(service_id, service_line)


@dataclass
class BusLegOverview:
    id: int
    service: BusServiceOverview
    operator: BusOperator
    board: BusStopOverview
    alight: BusStopOverview
    duration: timedelta


def register_bus_leg_overview(
    leg_id: int,
    bus_service: BusServiceOverview,
    bus_operator: BusOperator,
    leg_start: BusStopOverview,
    leg_end: BusStopOverview,
    leg_duration: timedelta,
) -> BusLegOverview:
    return BusLegOverview(
        leg_id, bus_service, bus_operator, leg_start, leg_end, leg_duration
    )


def register_bus_leg_overview_types(conn: Connection):
    register_type(conn, "BusStopOverviewOutData", register_bus_stop_overview)
    register_type(
        conn, "BusServiceOverviewOutData", register_bus_service_overview
    )
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusLegOverviewOutData", register_bus_leg_overview)


@dataclass
class BusVehicleOverview:
    id: int
    name: Optional[str]
    numberplate: str
    operator: BusOperator
    legs: list[BusLegOverview]


def register_bus_vehicle_overview(
    vehicle_id: int,
    vehicle_name: Optional[str],
    vehicle_numberplate: str,
    vehicle_operator: BusOperator,
    vehicle_legs: list[BusLegOverview],
) -> BusVehicleOverview:
    return BusVehicleOverview(
        vehicle_id,
        vehicle_name,
        vehicle_numberplate,
        vehicle_operator,
        vehicle_legs,
    )


def register_bus_vehicle_overview_types(conn: Connection):
    register_bus_leg_overview_types(conn)
    register_type(
        conn, "BusVehicleOverviewOutData", register_bus_vehicle_overview
    )


def get_bus_vehicle_overviews_for_user(
    conn: Connection, user_id: int
) -> list[BusVehicleOverview]:
    register_bus_vehicle_overview_types(conn)
    rows = conn.execute(
        "SELECT GetBusVehicleOverviewByUser(%s)", [user_id]
    ).fetchall()
    return [row[0] for row in rows]
