from dataclasses import dataclass
from datetime import datetime, timedelta
from api.data.bus.stop import BusStopOverview, register_bus_stop_overview
from psycopg import Connection
from typing import Optional

from api.data.bus.operators import BusOperator, register_bus_operator
from api.utils.database import register_type


@dataclass
class BusCallOverview:
    id: int
    call_index: int
    stop: BusStopOverview
    plan_arr: Optional[datetime]
    act_arr: Optional[datetime]
    plan_dep: Optional[datetime]
    act_dep: Optional[datetime]


def register_bus_call_overview(
    bus_call_id: int,
    call_index: int,
    bus_stop: BusStopOverview,
    plan_arr: Optional[datetime],
    act_arr: Optional[datetime],
    plan_dep: Optional[datetime],
    act_dep: Optional[datetime],
) -> BusCallOverview:
    return BusCallOverview(
        bus_call_id, call_index, bus_stop, plan_arr, act_arr, plan_dep, act_dep
    )


@dataclass
class BusServiceOverview:
    id: int
    line: str
    bg_colour: str
    fg_colour: str


def register_bus_service_overview(
    service_id: int,
    service_line: str,
    bg_colour: Optional[str],
    fg_colour: Optional[str],
) -> BusServiceOverview:
    return BusServiceOverview(
        service_id, service_line, bg_colour or "#ffffff", fg_colour or "#000000"
    )


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
