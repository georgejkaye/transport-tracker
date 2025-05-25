from dataclasses import dataclass
from datetime import datetime, timedelta
from psycopg import Connection
from typing import Optional

from api.data.bus.operators import BusOperator, register_bus_operator
from api.utils.database import register_type


@dataclass
class BusStopOverview:
    id: int
    atco: str
    name: str
    locality: str
    street: str
    indicator: str


def register_bus_stop_overview(
    bus_stop_id: int,
    stop_atco: str,
    stop_name: str,
    stop_locality: str,
    stop_street: str,
    stop_indicator: str,
) -> BusStopOverview:
    return BusStopOverview(
        bus_stop_id,
        stop_atco,
        stop_name,
        stop_locality,
        stop_street,
        stop_indicator,
    )


@dataclass
class BusCallOverview:
    id: int
    stop: BusStopOverview
    plan_arr: datetime
    act_arr: datetime
    plan_dep: datetime
    act_dep: datetime


def register_bus_call_overview(
    bus_call_id: int,
    bus_stop: BusStopOverview,
    plan_arr: datetime,
    act_arr: datetime,
    plan_dep: datetime,
    act_dep: datetime,
) -> BusCallOverview:
    return BusCallOverview(
        bus_call_id, bus_stop, plan_arr, act_arr, plan_dep, act_dep
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
    board: BusCallOverview
    alight: BusCallOverview
    duration: timedelta


def register_bus_leg_overview(
    leg_id: int,
    bus_service: BusServiceOverview,
    bus_operator: BusOperator,
    leg_start: BusCallOverview,
    leg_end: BusCallOverview,
    leg_duration: timedelta,
) -> BusLegOverview:
    return BusLegOverview(
        leg_id, bus_service, bus_operator, leg_start, leg_end, leg_duration
    )


def register_bus_leg_overview_types(conn: Connection):
    register_type(conn, "BusStopOverviewOutData", register_bus_stop_overview)
    register_type(conn, "BusCallOverviewOutData", register_bus_call_overview)
    register_type(
        conn, "BusServiceOverviewOutData", register_bus_service_overview
    )
    register_type(conn, "BusOperatorOutData", register_bus_operator)
    register_type(conn, "BusLegOverviewOutData", register_bus_leg_overview)


@dataclass
class BusVehicleOverview:
    id: int
    number: str
    name: Optional[str]
    numberplate: str
    operator: BusOperator
    legs: list[BusLegOverview]
    duration: timedelta


def register_bus_vehicle_overview(
    vehicle_id: int,
    vehicle_number: str,
    vehicle_name: Optional[str],
    vehicle_numberplate: str,
    vehicle_operator: BusOperator,
    vehicle_legs: list[BusLegOverview],
    vehicle_duration: timedelta,
) -> BusVehicleOverview:
    return BusVehicleOverview(
        vehicle_id,
        vehicle_number,
        vehicle_name,
        vehicle_numberplate,
        vehicle_operator,
        vehicle_legs,
        vehicle_duration,
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
        "SELECT GetBusVehicleOverviews(%s)", [user_id]
    ).fetchall()
    return [row[0] for row in rows]
